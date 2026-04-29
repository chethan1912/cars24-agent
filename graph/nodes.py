from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic
from graph.state import AgentState
from services.session_service import SessionService
from services.ranking_service import RankingService
import json

# ── WORKFLOW SHELL NODES ─────────────────────────────────────────────────────


def load_context_node(state: AgentState, session_svc: SessionService) -> AgentState:
    """
    Shell node. Runs at the very start of every turn.
    Loads the SessionContext from Redis into state.
    """
    session_id = state["messages"][-1].additional_kwargs.get("session_id")
    context = session_svc.load(session_id)
    return {**state, "context": context, "needs_retrieval": False}


def check_transition_node(state: AgentState) -> AgentState:
    """
    Shell node. Checks if a stage transition should fire.
    This is deterministic — no LLM involved.
    Returns state with potentially updated context.stage.
    """
    context = state["context"]
    current_stage = context.stage

    if current_stage == "intake" and context.profile.intake_complete:
        context.stage = "retrieval"

    elif current_stage == "retrieval" and len(context.shortlist) >= 1:
        context.stage = "explore"

    elif current_stage == "explore":
        if context.token_paid or len(context.pending_test_drives) > 0:
            context.stage = "converting"
        # Note: if needs_retrieval=True, we re-run retrieval internally
        # but do NOT change the stage to "retrieval" — that would reset UX

    return {**state, "context": context}


def save_context_node(state: AgentState, session_svc: SessionService) -> AgentState:
    """
    Shell node. Runs at the end of every turn.
    Saves updated context to Redis.
    """
    session_svc.save(state["context"])
    return state


# ── REACT AGENT NODES ────────────────────────────────────────────────────────

def build_intake_agent(tools: list, llm: ChatAnthropic):
    """ReAct agent for INTAKE stage."""
    def system_prompt(state: AgentState) -> str:
        context = state["context"]
        return """You are a Cars24 buying concierge in the intake phase.
Your ONLY job right now: collect these 5 fields through natural conversation:
1. use_case: why they want a car ("first_car" | "upgrade" | "family" | "commuter")
2. city: which Indian city
3. budget_ceiling: maximum on-road price in rupees (extract number from their words)
4. fuel_pref: list of acceptable fuel types ["petrol"] | ["diesel"] | ["petrol","cng"] etc.
5. risk_tolerance: "low" (peace of mind, willing to pay more), "mid" (balanced), "high" (price first)

Rules:
- Call patch_context every time you collect a new field. Do not batch them all at the end.
- Ask at most ONE question per turn. Do not interrogate.
- If the user volunteers multiple fields in one message, patch all of them.
- Do NOT call sql_filter_inventory, vector_rerank, or any retrieval tools in this stage.
- If the user asks a general question (e.g. "is petrol better than diesel?"), answer it briefly, then continue intake.
- Be warm and conversational. This is a chat, not a form.

Current session_id: {session_id}
Collected so far: {profile_json}
""".format(
            session_id=context.session_id,
            profile_json=json.dumps(context.profile.model_dump())
        )
    return create_react_agent(llm, tools, state_modifier=system_prompt)


def build_retrieval_agent(tools: list, llm: ChatAnthropic, ranking_svc: RankingService):
    """ReAct agent for RETRIEVAL stage."""
    def system_prompt(state: AgentState) -> str:
        context = state["context"]
        return """You are a Cars24 buying concierge performing inventory retrieval.
Run this pipeline in order:
1. Call sql_filter_inventory to get candidate car IDs
2. Call vector_rerank with those IDs to get semantically ranked results
3. Call llm_rank with the ranked_ids to get final shortlist with reasoning
4. Generate a warm, personalised recommendation message showing the top 3 cars

For each car in your recommendation:
- State why it specifically fits THIS buyer (reference their use_case, city, risk_tolerance)
- Include price, year, km driven
- Mention the single most important pro for this buyer
- Do NOT use generic phrases like "popular choice" or "great value"

Current session_id: {session_id}
Buyer profile: {profile_json}
""".format(
            session_id=context.session_id,
            profile_json=json.dumps(context.profile.model_dump())
        )
    return create_react_agent(llm, tools, state_modifier=system_prompt)


def build_explore_agent(tools: list, llm: ChatAnthropic):
    """ReAct agent for EXPLORE stage. Handles all follow-up interactions."""
    def system_prompt(state: AgentState) -> str:
        context = state["context"]
        return """You are a Cars24 buying concierge in explore mode.
The buyer has seen their shortlist. Handle whatever they ask.

CRITICAL RULE — classify every message before acting:
1. CONSTRAINT CHANGE: budget/city/fuel/year changed → call patch_context FIRST, then sql_filter_inventory + vector_rerank + llm_rank
2. CAR-SPECIFIC QUESTION: about a car in the shortlist → call fetch_inspection_report if needed. No re-retrieval.
3. ACTION REQUEST: test drive / EMI / book → call the relevant tool. Collect any missing params first.
4. GENERAL QUESTION: knowledge question → answer directly. No tool call needed.

For constraint changes: patch the context, re-retrieve, then present updated recommendations.
For test drive booking: you MUST have car_id, buyer_address, AND time_slot before calling schedule_test_drive.
For EMI: you need car price. Get it from the shortlist in context.

Current session_id: {session_id}
Buyer profile: {profile_json}
Current shortlist: {shortlist_json}
Recent signals: {signals_json}
""".format(
            session_id=context.session_id,
            profile_json=json.dumps(context.profile.model_dump()),
            shortlist_json=json.dumps([s.model_dump()
                                      for s in context.shortlist]),
            signals_json=json.dumps([s.model_dump()
                                    for s in context.signals[-5:]])
        )
    return create_react_agent(llm, tools, state_modifier=system_prompt)
