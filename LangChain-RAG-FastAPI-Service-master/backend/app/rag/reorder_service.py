import asyncio
import os
from http import HTTPStatus
from typing import Any, Dict, List

from dotenv import load_dotenv

from app.core.logger_handler import logger

load_dotenv()


def check_and_download_reranker_model() -> None:
    """Validate Aliyun reranker configuration on startup."""
    model_name = os.getenv("ALIYUN_RERANK_MODEL_NAME", os.getenv("RERANKER_MODEL_NAME", "qwen3-rerank"))
    api_key = os.getenv("ALIYUN_ACCESS_KEY_SECRET") or os.getenv("DASHSCOPE_API_KEY")

    if api_key:
        logger.info(f"Aliyun reranker configured with model: {model_name}")
        return

    logger.warning("Aliyun reranker API key is missing. Reorder requests will fail until it is configured.")


class ReorderService:
    def __init__(self):
        try:
            import dashscope
        except ImportError as exc:
            raise ImportError("dashscope is required for Aliyun reranking. Install it with: pip install dashscope") from exc

        self.dashscope = dashscope

    @staticmethod
    def _value_of(payload: Any, key: str, default: Any = None) -> Any:
        if payload is None:
            return default
        if isinstance(payload, dict):
            return payload.get(key, default)
        return getattr(payload, key, default)

    @staticmethod
    def _extract_document_text(document_payload: Any) -> str | None:
        if document_payload is None:
            return None
        if isinstance(document_payload, str):
            return document_payload
        if isinstance(document_payload, dict):
            return document_payload.get("text") or document_payload.get("content")

        text = getattr(document_payload, "text", None)
        if text:
            return text

        content = getattr(document_payload, "content", None)
        if content:
            return content

        return None

    @staticmethod
    def _get_model_name() -> str:
        return os.getenv("ALIYUN_RERANK_MODEL_NAME", os.getenv("RERANKER_MODEL_NAME", "qwen3-rerank"))

    @staticmethod
    def _get_api_key() -> str:
        api_key = os.getenv("ALIYUN_ACCESS_KEY_SECRET") or os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("ALIYUN_ACCESS_KEY_SECRET is not configured")
        return api_key

    def _call_rerank(self, query: str, documents: List[str]):
        return self.dashscope.TextReRank.call(
            model=self._get_model_name(),
            query=query,
            documents=documents,
            return_documents=True,
            api_key=self._get_api_key(),
        )

    def _parse_response(self, response: Any, original_documents: List[str]) -> List[Dict[str, Any]]:
        if response.status_code != HTTPStatus.OK:
            message = getattr(response, "message", "unknown error")
            code = getattr(response, "code", "unknown")
            request_id = getattr(response, "request_id", "unknown")
            logger.error(
                f"Aliyun rerank request failed: code={code}, request_id={request_id}, message={message}"
            )
            raise ValueError(message)

        output = getattr(response, "output", None)
        results = getattr(output, "results", None)

        if not results:
            logger.error(f"Unexpected DashScope rerank payload: {output}")
            raise ValueError("Invalid DashScope rerank response format")

        scored_documents: List[Dict[str, Any]] = []
        for item in results:
            index = self._value_of(item, "index", -1)
            similarity = float(self._value_of(item, "relevance_score", 0.0))
            document_text = self._extract_document_text(self._value_of(item, "document"))

            if document_text is None and isinstance(index, int) and 0 <= index < len(original_documents):
                document_text = original_documents[index]

            scored_documents.append(
                {
                    "document": document_text or "",
                    "similarity": similarity,
                }
            )
            logger.info(f"Aliyun rerank similarity score: {similarity:.4f}")

        scored_documents.sort(key=lambda item: item["similarity"], reverse=True)
        return scored_documents

    async def reorder_documents(
        self,
        query: str,
        documents: List[str],
        thinking_callback=None,
    ) -> Dict[str, Any]:
        try:
            if not documents:
                return {"success": True, "documents": [], "error": ""}

            if thinking_callback:
                await thinking_callback(
                    {
                        "type": "thinking",
                        "stage": "reorder",
                        "content": f"正在使用阿里云百炼对 {len(documents)} 个文档进行重排序...",
                    }
                )

            response = await asyncio.to_thread(self._call_rerank, query, documents)
            sorted_docs = self._parse_response(response, documents)

            if thinking_callback:
                await thinking_callback(
                    {
                        "type": "thinking",
                        "stage": "reorder",
                        "content": f"重排序完成，返回 {len(sorted_docs)} 个文档。",
                        "details": {
                            "scores": [
                                {
                                    "index": index,
                                    "score": round(float(doc["similarity"]), 4),
                                    "preview": doc["document"][:100] + "..." if len(doc["document"]) > 100 else doc["document"],
                                }
                                for index, doc in enumerate(sorted_docs, 1)
                            ]
                        },
                    }
                )

            logger.info(f"Aliyun rerank completed, documents returned: {len(sorted_docs)}")
            return {"success": True, "documents": sorted_docs, "error": ""}
        except Exception as exc:
            error_msg = str(exc)
            logger.error(f"Aliyun rerank failed: {error_msg}")
            return {"success": False, "documents": [], "error": error_msg}

    @staticmethod
    async def format_reorder_result(sorted_docs: List[Dict[str, Any]]) -> str:
        lines = ["重排序后的文档列表："]
        for index, doc in enumerate(sorted_docs, 1):
            lines.append(f"{index}. 相似度: {doc.get('similarity', 0):.4f}")
            lines.append(f"   内容: {doc.get('document', '')}")
            lines.append("")
        return "\n".join(lines)


reorder_service = ReorderService()
