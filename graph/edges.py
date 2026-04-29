from graph.state import AgentState


def route_by_stage(state: AgentState) -> str:
    """
    Main routing function. Called after check_transition_node.
    Returns the name of the next node to run.
    """
    stage = state["context"].stage
    stage_to_node = {
        "intake": "intake_agent",
        "retrieval": "retrieval_agent",
        "explore": "explore_agent",
        "converting": "converting_agent",
    }
    return stage_to_node.get(stage, "intake_agent")


def should_end(state: AgentState) -> str:
    """After agent runs — save context and end, or loop back."""
    # Always save context after every agent turn
    return "save_context"
