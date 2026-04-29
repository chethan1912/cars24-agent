from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from core.models import SessionContext


class AgentState(TypedDict):
    # LangGraph manages message history with the add_messages reducer
    messages: Annotated[list, add_messages]

    # Our custom context object — passed through every node
    context: SessionContext

    # What the ReAct agent decided to do this turn
    tool_calls: list[dict]
    tool_results: list[dict]

    # Context patch emitted by ReAct — applied by shell before saving
    context_patch: dict

    # Flag set by ReAct if constraint changed → triggers re-retrieval in Explore
    needs_retrieval: bool

    # Final response string to send to user
    response: str
