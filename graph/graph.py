from langgraph.graph import StateGraph, END
from graph.state import AgentState
from graph.nodes import (
    load_context_node, check_transition_node, save_context_node,
    build_intake_agent, build_retrieval_agent, build_explore_agent
)
from graph.edges import route_by_stage, should_end
from graph.tools import make_tools
from langchain_anthropic import ChatAnthropic
from services.session_service import SessionService
from services.inventory_service import InventoryService
from services.embedding_service import EmbeddingService
from services.ranking_service import RankingService
from services.emi_service import EMIService
from services.inspection_service import InspectionService
from services.booking_service import BookingService
from core.config import settings
import functools


def build_graph(db_session, session_svc: SessionService):
    # Initialise all services
    inventory_svc = InventoryService(db_session)
    embedding_svc = EmbeddingService()
    llm_svc_sonnet = ChatAnthropic(
        model="claude-sonnet-4-5", api_key=settings.ANTHROPIC_API_KEY)
    llm_svc_haiku = ChatAnthropic(
        model="claude-haiku-4-5", api_key=settings.ANTHROPIC_API_KEY)
    ranking_svc = RankingService(inventory_svc)
    emi_svc = EMIService()
    inspection_svc = InspectionService(db_session)
    booking_svc = BookingService(db_session)

    tools = make_tools(inventory_svc, embedding_svc, emi_svc,
                       inspection_svc, booking_svc, session_svc, ranking_svc)

    # Build stage agents
    intake_agent = build_intake_agent(tools, llm_svc_haiku)
    retrieval_agent = build_retrieval_agent(tools, llm_svc_sonnet, ranking_svc)
    explore_agent = build_explore_agent(tools, llm_svc_sonnet)

    # Build graph
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("load_context", functools.partial(
        load_context_node, session_svc=session_svc))
    graph.add_node("check_transition", check_transition_node)
    graph.add_node("intake_agent", intake_agent)
    graph.add_node("retrieval_agent", retrieval_agent)
    graph.add_node("explore_agent", explore_agent)
    graph.add_node("save_context", functools.partial(
        save_context_node, session_svc=session_svc))

    # Entry point
    graph.set_entry_point("load_context")

    # Edges
    graph.add_edge("load_context", "check_transition")
    graph.add_conditional_edges("check_transition", route_by_stage)
    graph.add_edge("intake_agent", "save_context")
    graph.add_edge("retrieval_agent", "save_context")
    graph.add_edge("explore_agent", "save_context")
    graph.add_edge("save_context", END)

    return graph.compile()
