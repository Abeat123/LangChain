import uuid

from fastapi import Depends
from fastapi.responses import StreamingResponse
from fastapi.routing import APIRouter

from app.agent.agent import get_agent_stream_response
from app.core.rate_limit import rate_limit
from app.core.success_response import success_response
from app.router.chat_service import ChatService, get_router_service
from app.schemas.models import (
    AnswerFeedbackCreateRequest,
    AnswerFeedbackListResponse,
    AnswerFeedbackStatsResponse,
    QueryRequest,
    RAGRequest,
    RAGResponse,
    ReorderRequest,
    ReorderResponse,
    SessionResponse,
)
from app.services.feedback_service import FeedbackService
from app.services.knowledge_base_service import KnowledgeBaseService
from app.utils.auth_utils import get_current_user_id


chat_router = APIRouter(prefix="/chat", tags=["chat"])


@chat_router.post("/agent/query/stream")
async def query_stream(
    request: QueryRequest,
    user_id: str = Depends(get_current_user_id),
    _: None = Depends(rate_limit(limit=10, window=60)),
):
    session_id = request.session_id or str(uuid.uuid4())
    scope_id = await KnowledgeBaseService.resolve_scope_id(user_id, request.knowledge_base_id)

    return StreamingResponse(
        get_agent_stream_response(request.query, session_id, user_id, knowledge_base_scope_id=scope_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@chat_router.post("/rag/query", response_model=RAGResponse)
async def query_rag(
    request: RAGRequest,
    user_id: str = Depends(get_current_user_id),
    router_service: ChatService = Depends(get_router_service),
    _: None = Depends(rate_limit(limit=15, window=60)),
):
    scope_id = await KnowledgeBaseService.resolve_scope_id(user_id, request.knowledge_base_id)
    response = await router_service.handle_rag_query(request.query, user_id, knowledge_base_scope_id=scope_id)
    return success_response(data=RAGResponse(response=response))


@chat_router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    router_service: ChatService = Depends(get_router_service),
):
    history = await router_service.handle_get_session(session_id, user_id)
    return success_response(data=SessionResponse(session_id=session_id, history=history))


@chat_router.delete("/session/{session_id}")
async def delete_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    router_service: ChatService = Depends(get_router_service),
):
    await router_service.handle_delete_session(session_id, user_id)
    return success_response(message=f"Session {session_id} deleted successfully")


@chat_router.get("/sessions")
async def get_all_sessions(router_service: ChatService = Depends(get_router_service)):
    session_ids = await router_service.handle_get_all_sessions()
    return success_response(data={"sessions": session_ids})


@chat_router.get("/sessions/{user_id}")
async def get_user_sessions(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    router_service: ChatService = Depends(get_router_service),
):
    session_ids = await router_service.handle_get_user_sessions(user_id, current_user_id)
    return success_response(data={"sessions": session_ids})


@chat_router.post("/reorder", response_model=ReorderResponse)
async def reorder_documents(
    request: ReorderRequest,
    router_service: ChatService = Depends(get_router_service),
    _: None = Depends(rate_limit(limit=20, window=60)),
):
    sorted_docs = await router_service.handle_reorder(request.query, request.documents)
    return success_response(data=ReorderResponse(documents=sorted_docs))


@chat_router.post("/feedback")
async def create_answer_feedback(
    request: AnswerFeedbackCreateRequest,
    user_id: str = Depends(get_current_user_id),
    _: None = Depends(rate_limit(limit=30, window=60)),
):
    item = await FeedbackService.save_feedback(
        user_id=user_id,
        question=request.question,
        answer=request.answer,
        feedback_type=request.feedback_type,
        session_id=request.session_id,
        knowledge_base_id=request.knowledge_base_id,
        comment=request.comment,
    )
    return success_response(data=item, message="反馈已保存")


@chat_router.get("/feedback", response_model=AnswerFeedbackListResponse)
async def get_answer_feedback(
    knowledge_base_id: str = None,
    limit: int = 50,
    user_id: str = Depends(get_current_user_id),
    _: None = Depends(rate_limit(limit=30, window=60)),
):
    result = await FeedbackService.list_feedback(user_id, knowledge_base_id=knowledge_base_id, limit=limit)
    return success_response(data=AnswerFeedbackListResponse(**result))


@chat_router.get("/feedback/stats", response_model=AnswerFeedbackStatsResponse)
async def get_answer_feedback_stats(
    knowledge_base_id: str = None,
    user_id: str = Depends(get_current_user_id),
    _: None = Depends(rate_limit(limit=30, window=60)),
):
    result = await FeedbackService.get_feedback_stats(user_id, knowledge_base_id=knowledge_base_id)
    return success_response(data=AnswerFeedbackStatsResponse(**result))
