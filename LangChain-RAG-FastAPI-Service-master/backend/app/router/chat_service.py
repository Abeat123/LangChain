import uuid
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException

from app.agent.agent import get_agent_response
from app.core.logger_handler import logger
from app.rag.rag_service import RagService
from app.rag.reorder_service import reorder_service
from app.services import session_manager as sm


class ChatService:
    async def handle_agent_query(
        self,
        query: str,
        session_id: Optional[str],
        user_id: str,
        knowledge_base_scope_id: Optional[str] = None,
    ) -> Tuple[str, dict, str]:
        session_id = session_id or str(uuid.uuid4())
        history = await sm.session_manager.get_history(session_id, user_id)
        result = await get_agent_response(query, history, user_id=user_id, knowledge_base_scope_id=knowledge_base_scope_id)
        response = result.get("response")
        steps = result.get("steps", [])
        await sm.session_manager.add_message(session_id, user_id, query, response)
        return session_id, response, steps

    async def handle_rag_query(
        self,
        query: str,
        user_id: str,
        knowledge_base_scope_id: Optional[str] = None,
    ) -> str:
        rag_service = RagService(user_id, knowledge_base_scope_id=knowledge_base_scope_id)
        return await rag_service.rag_summary(query)

    async def handle_get_session(self, session_id: str, user_id: str) -> List[Tuple[str, str]]:
        return await sm.session_manager.get_history(session_id, user_id)

    async def handle_delete_session(self, session_id: str, user_id: str) -> None:
        await sm.session_manager.clear_session(session_id, user_id)

    async def handle_get_all_sessions(self) -> List[str]:
        return await sm.session_manager.get_all_session_ids()

    async def handle_get_user_sessions(self, user_id: str, current_user_id: str) -> List[Dict]:
        if user_id != current_user_id:
            raise HTTPException(status_code=403, detail="Forbidden")
        return await sm.session_manager.get_user_sessions(user_id)

    async def handle_reorder(self, query: str, documents: List[str]) -> List[Dict[str, Any]]:
        try:
            result = await reorder_service.reorder_documents(query, documents)
            if result["success"]:
                logger.info(f"【重排序结果】查询 {query} 返回 {len(result['documents'])} 条排序记录")
                return result["documents"]
            logger.warning(f"【重排序失败】{result['error']}")
            return [{"document": doc, "similarity": 0.0} for doc in documents]
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"重排序过程中出错: {exc}") from exc


def get_router_service() -> ChatService:
    return ChatService()
