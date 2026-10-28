import datetime
from contextvars import ContextVar
from typing import List, Optional

from langchain_core.tools import tool

from app.core.logger_handler import logger
from app.rag.rag_service import RagService
from app.rag.reorder_service import reorder_service
from app.utils.auth_utils import decode_django_jwt


current_user_id_var: ContextVar[Optional[str]] = ContextVar("current_user_id", default=None)
current_knowledge_base_scope_var: ContextVar[Optional[str]] = ContextVar("current_knowledge_base_scope", default=None)
thinking_callback_var: ContextVar[Optional[callable]] = ContextVar("thinking_callback", default=None)


def set_current_user_id(user_id: str):
    current_user_id_var.set(user_id)


def get_current_user_id_from_context() -> Optional[str]:
    return current_user_id_var.get()


def set_current_knowledge_base_scope(knowledge_base_scope_id: Optional[str]):
    current_knowledge_base_scope_var.set(knowledge_base_scope_id)


def get_current_knowledge_base_scope() -> Optional[str]:
    return current_knowledge_base_scope_var.get()


def set_thinking_callback(callback):
    thinking_callback_var.set(callback)


def get_thinking_callback_from_context():
    return thinking_callback_var.get()


@tool(
    description=(
        "从向量数据库检索文档并生成摘要，返回格式为："
        "摘要: [摘要内容]\\n\\n检索到的文档列表:\\n1. [文档1内容]\\n2. [文档2内容]..."
    )
)
async def rag_summary_tools(query: str, user_id: str = None) -> str:
    effective_user_id = user_id or get_current_user_id_from_context()
    if not effective_user_id:
        return "错误: 无法确定用户身份，请提供有效的 user_id"

    thinking_callback = get_thinking_callback_from_context()
    knowledge_base_scope_id = get_current_knowledge_base_scope()
    result = await RagService(
        effective_user_id,
        knowledge_base_scope_id=knowledge_base_scope_id,
        thinking_callback=thinking_callback,
    ).get_documents_and_summary(query)
    documents = result.get("documents", [])
    summary = result.get("summary", "")

    formatted_result = f"摘要: {summary}\n\n"
    formatted_result += "检索到的文档列表（已重排序）:\n"
    for index, doc in enumerate(documents, 1):
        formatted_result += f"{index}. {doc}\n"

    return formatted_result


@tool(description="对文档列表进行重排序，输入 query 和 documents，输出重排序后的文档内容及相似度。")
async def reorder_documents_tools(query: str, documents: List[str]) -> str:
    thinking_callback = get_thinking_callback_from_context()
    result = await reorder_service.reorder_documents(query, documents, thinking_callback=thinking_callback)
    if result["success"]:
        formatted_result = await reorder_service.format_reorder_result(result["documents"])
        logger.info(formatted_result)
        return formatted_result
    return f"重排序失败: {result['error']}"


@tool(description="当用户明确询问自己的 ID 或用户名时，传入完整 JWT token，解析出当前用户信息。")
async def get_user_info_tools(token: str) -> str:
    payload = decode_django_jwt(token)
    if payload:
        user_id = payload.get("user_id", "未知")
        user_name = payload.get("user_name", "未知")
        return f"用户信息：\n- 用户ID: {user_id}\n- 用户名: {user_name}"
    return "无法解析 JWT token，无法获取用户信息"


@tool(description="根据城市名称获取天气信息。")
async def get_weather_tools(city: str = None) -> str:
    if not city:
        return "请提供城市名称"
    return f"【{city}】的天气是晴朗的"


@tool(description="获取当前时间。")
async def what_time_is_now() -> str:
    return f"当前时间是：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
