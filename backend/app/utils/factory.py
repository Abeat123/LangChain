from abc import ABC, abstractmethod
import os
from typing import List, Optional

from dotenv import load_dotenv
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_ollama import ChatOllama, OllamaEmbeddings

from app.core.logger_handler import logger


load_dotenv()


class DashScopeEmbeddingsWrapper(Embeddings):
    """DashScope embedding wrapper compatible with current and legacy payloads."""

    def __init__(self, model_name: str = "qwen3-embedding", api_key: str | None = None):
        try:
            import dashscope
        except ImportError as exc:
            raise ImportError("dashscope is required. Install it with: pip install dashscope") from exc

        self.dashscope = dashscope
        self.dashscope.api_key = api_key or os.getenv("ALIYUN_ACCESS_KEY_SECRET")
        self.model_name = model_name
        # DashScope synchronous embedding accepts up to 10 texts per request.
        raw_batch_size = int(os.getenv("ALIYUN_EMBED_BATCH_SIZE", "10"))
        self.batch_size = max(1, min(raw_batch_size, 10))

    def _batched(self, texts: List[str]) -> List[List[str]]:
        return [texts[i:i + self.batch_size] for i in range(0, len(texts), self.batch_size)]

    def _extract_embeddings(self, resp) -> List[List[float]]:
        if resp.status_code != 200:
            message = getattr(resp, "message", "unknown error")
            logger.error(f"DashScope embedding request failed: {message}")
            raise ValueError(message)

        output = getattr(resp, "output", None) or {}
        if isinstance(output, dict):
            embeddings = output.get("embeddings") or []
            if embeddings:
                ordered = sorted(embeddings, key=lambda item: item.get("text_index", 0))
                vectors = [item.get("embedding") for item in ordered if item.get("embedding")]
                if vectors:
                    return vectors

            legacy_embedding = output.get("embedding")
            if legacy_embedding:
                return [legacy_embedding]

        logger.error(f"Unexpected DashScope embedding payload: {output}")
        raise ValueError("Invalid DashScope embedding response format")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        results: List[List[float]] = []
        for batch in self._batched(texts):
            resp = self.dashscope.TextEmbedding.call(
                model=self.model_name,
                input=batch,
            )
            results.extend(self._extract_embeddings(resp))
        return results

    def embed_query(self, text: str) -> List[float]:
        resp = self.dashscope.TextEmbedding.call(
            model=self.model_name,
            input=text,
        )
        embeddings = self._extract_embeddings(resp)
        if embeddings:
            return embeddings[0]
        raise ValueError("DashScope did not return an embedding for the query")


class BaseModelFactory(ABC):
    """Base model factory."""

    @abstractmethod
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        pass


class ChatModelFactory(BaseModelFactory):
    """Create the configured chat model."""

    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        llm_type = os.getenv("LLM_TYPE", "ALIYUN").upper()

        if llm_type == "OPENAI":
            from langchain_openai import ChatOpenAI

            model_name = os.getenv("CHAT_MODEL_NAME", "qwen3.5-omni-flash-2026-03-15")
            model_kwargs = {}
            extra_body = {}
            if "omni" in model_name.lower():
                model_kwargs["modalities"] = ["text"]
                extra_body["enable_thinking"] = False
            logger.info(f"ChatModel using OpenAI-compatible model: {model_name}")
            return ChatOpenAI(
                model=model_name,
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_BASE_URL"),
                streaming=True,
                stream_usage=False,
                model_kwargs=model_kwargs,
                extra_body=extra_body,
                timeout=60,
                max_retries=1,
            )

        if llm_type == "OLLAMA":
            model_name = os.getenv("OLLAMA_MODEL_NAME", os.getenv("OLLAMA_CHAT_MODEL_NAME", "qwen3:7b"))
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            logger.info(f"ChatModel using Ollama model: {model_name}, base_url: {base_url}")
            return ChatOllama(
                model=model_name,
                base_url=base_url,
                streaming=True,
                top_p=0.7,
            )

        if llm_type == "ALIYUN":
            model_name = os.getenv("ALIYUN_MODEL_NAME", os.getenv("CHAT_MODEL_NAME", "qwen3-max"))
            api_key = os.getenv("ALIYUN_ACCESS_KEY_SECRET")
            base_url = os.getenv("ALIYUN_BASE_URL")
            logger.info(f"ChatModel using Aliyun model: {model_name}")
            return ChatTongyi(
                model=model_name,
                api_key=api_key,
                base_url=base_url,
                streaming=True,
                top_p=0.7,
            )

        raise ValueError(f"Unsupported LLM_TYPE: {llm_type}. Expected OPENAI, ALIYUN or OLLAMA.")


class EmbedModelFactory(BaseModelFactory):
    """Create the configured embedding model."""

    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        embed_type = os.getenv("EMBED_MODEL_TYPE", "OLLAMA").upper()

        if embed_type == "OLLAMA":
            model_name = os.getenv("TEXT_EMBEDDING_MODEL_NAME", "qwen3-embedding:0.6b")
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            logger.info(f"EmbedModel using Ollama model: {model_name}, base_url: {base_url}")
            return OllamaEmbeddings(
                model=model_name,
                base_url=base_url,
            )

        if embed_type == "ALIYUN":
            model_name = os.getenv("ALIYUN_EMBED_MODEL_NAME", "qwen3-embedding")
            api_key = os.getenv("ALIYUN_ACCESS_KEY_SECRET")
            logger.info(f"EmbedModel using Aliyun model: {model_name}")
            return DashScopeEmbeddingsWrapper(
                model_name=model_name,
                api_key=api_key,
            )

        raise ValueError(f"Unsupported EMBED_MODEL_TYPE: {embed_type}. Expected ALIYUN or OLLAMA.")


class RerankerModelFactory(BaseModelFactory):
    """Reranker is currently disabled."""

    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        return None


chat_model = ChatModelFactory().generator()
embed_model = EmbedModelFactory().generator()
reranker_model = None
