from fastapi import APIRouter, Depends
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from graph.graph import build_graph
from api.dependencies import get_db, get_session_svc

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    session_id: str
    response: str
    stage: str
    shortlist_count: int


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db=Depends(get_db), session_svc=Depends(get_session_svc)):
    graph = build_graph(db, session_svc)

    result = await graph.ainvoke({
        "messages": [
            HumanMessage(
                content=request.message,
                additional_kwargs={"session_id": request.session_id}
            )
        ],
        "context": session_svc.load(request.session_id),
        "tool_calls": [],
        "tool_results": [],
        "context_patch": {},
        "needs_retrieval": False,
        "response": "",
    })

    final_context = result["context"]
    last_ai_message = [m for m in result["messages"]
                       if hasattr(m, "content") and m.type == "ai"][-1]

    return ChatResponse(
        session_id=request.session_id,
        response=last_ai_message.content,
        stage=final_context.stage,
        shortlist_count=len(final_context.shortlist),
    )
