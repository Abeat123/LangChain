import asyncio

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langsmith import traceable

from app.core.logger_handler import logger
from app.rag.reorder_service import reorder_service
from app.rag.vector_store import VectorStoreService
from app.utils.factory import chat_model
from app.utils.prompt_loader import load_prompt


class RagService:
    def __init__(self, user_id: str = None, knowledge_base_scope_id: str = None, thinking_callback=None):
        self.vector_store = VectorStoreService(knowledge_base_scope_id=knowledge_base_scope_id)
        self.retriever = None
        self.user_id = user_id
        self.prompt_text = load_prompt(prompt_type="rag_summary_prompt")
        self.prompt_template = PromptTemplate.from_template(self.prompt_text)
        self.chat_model = chat_model
        self.chain = self._init_chain()
        self.hyde_prompt_template = PromptTemplate.from_template(
            "基于以下问题，生成一段详细的假设性回答，我会根据这段回答在向量数据库中检索相关文档：\n\n"
            "问题：{query}\n\n假设性回答："
        )
        self.thinking_callback = thinking_callback

    async def initialize_retriever(self, query: str = None):
        if self.retriever is None:
            weights = await self.vector_store.get_dynamic_weights(query)
            if self.thinking_callback:
                await self.thinking_callback(
                    {
                        "type": "thinking",
                        "stage": "retrieval",
                        "content": f"初始化检索器（向量权重: {weights[0]:.1f}，BM25 权重: {weights[1]:.1f}）",
                        "details": {
                            "vector_weight": weights[0],
                            "bm25_weight": weights[1],
                        },
                    }
                )

            self.retriever = await self.vector_store.get_retriever(query, self.user_id)

    def _init_chain(self):
        return self.prompt_template | self.chat_model | StrOutputParser()

    @traceable
    async def generate_hypothetical_document(self, query: str) -> str:
        try:
            hyde_chain = self.hyde_prompt_template | self.chat_model | StrOutputParser()
            hypothetical_doc = await hyde_chain.ainvoke({"query": query})
            logger.info(f"【HyDE】生成的假设文档:\n{hypothetical_doc}")
            return hypothetical_doc
        except Exception as exc:
            logger.error(f"【HyDE】生成假设文档失败: {exc}")
            return query

    @traceable
    async def retrieve_document(self, query: str) -> list:
        if not self.user_id:
            logger.warning("【HyDE】user_id 为空，不执行检索")
            return []

        try:
            if self.retriever is None:
                await self.initialize_retriever(query)

            if self.thinking_callback:
                await self.thinking_callback(
                    {
                        "type": "thinking",
                        "stage": "hyde",
                        "content": f"正在基于查询“{query}”生成假设性文档...",
                    }
                )

            hypothetical_doc = await self.generate_hypothetical_document(query)

            if self.thinking_callback:
                await self.thinking_callback(
                    {
                        "type": "thinking",
                        "stage": "hyde",
                        "content": "假设性文档生成完成",
                        "details": {
                            "hypothetical_doc_preview": (
                                hypothetical_doc[:200] + "..."
                                if len(hypothetical_doc) > 200
                                else hypothetical_doc
                            )
                        },
                    }
                )

            if self.thinking_callback:
                await self.thinking_callback(
                    {
                        "type": "thinking",
                        "stage": "retrieval",
                        "content": "正在向量数据库中检索相关片段...",
                    }
                )

            documents = await self.retriever.ainvoke(hypothetical_doc)

            if self.thinking_callback:
                doc_previews = []
                sources = []
                for index, doc in enumerate(documents, 1):
                    preview = doc.page_content[:150] + "..." if len(doc.page_content) > 150 else doc.page_content
                    source = doc.metadata.get("original_filename", doc.metadata.get("source", "unknown"))
                    sources.append(source)
                    doc_previews.append(
                        {
                            "index": index,
                            "preview": preview,
                            "source": source,
                        }
                    )
                unique_sources = list(dict.fromkeys(sources))
                await self.thinking_callback(
                    {
                        "type": "thinking",
                        "stage": "retrieval",
                        "content": f"检索到 {len(documents)} 个相关片段，来自 {len(unique_sources)} 个文件",
                        "details": {
                            "documents": doc_previews,
                            "chunk_count": len(documents),
                            "file_count": len(unique_sources),
                        },
                    }
                )

            return documents
        except Exception as exc:
            logger.error(f"【HyDE】检索文档失败: {exc}")
            return []

    @traceable
    async def reorder_documents(self, query: str, documents: list) -> list:
        if self.thinking_callback:
            await self.thinking_callback(
                {
                    "type": "thinking",
                    "stage": "reorder",
                    "content": f"正在对 {len(documents)} 个片段进行重排序...",
                }
            )

        result = await reorder_service.reorder_documents(
            query,
            documents,
            thinking_callback=self.thinking_callback,
        )
        if result["success"]:
            reordered_documents = [doc.get("document", "") for doc in result["documents"]]
            if self.thinking_callback:
                score_details = []
                for index, doc in enumerate(result["documents"], 1):
                    preview = doc.get("document", "")
                    score_details.append(
                        {
                            "rank": index,
                            "score": round(doc.get("similarity", 0), 4),
                            "preview": preview[:100] + "..." if len(preview) > 100 else preview,
                        }
                    )
                await self.thinking_callback(
                    {
                        "type": "thinking",
                        "stage": "reorder",
                        "content": f"重排序完成，返回 {len(reordered_documents)} 个相关片段",
                        "details": {"scores": score_details},
                    }
                )
            return reordered_documents

        logger.warning(f"【RAG】重排序失败: {result['error']}")
        return documents

    @traceable
    async def get_documents_and_summary(self, query: str) -> dict:
        if not self.user_id:
            logger.warning("【RAG】user_id 为空，不返回任何文档")
            return {"documents": [], "summary": "抱歉，我没有找到相关信息。"}

        try:
            documents = await self.retrieve_document(query)
            document_contents = [doc.page_content for doc in documents]
            reordered_documents = await self.reorder_documents(query, document_contents)

            if not reordered_documents:
                return {"documents": [], "summary": "抱歉，我没有找到相关信息。"}

            try:
                max_documents = 3
                if self.thinking_callback:
                    await self.thinking_callback(
                        {
                            "type": "thinking",
                            "stage": "summarize",
                            "content": f"正在对前 {min(max_documents, len(reordered_documents))} 个最相关片段进行总结...",
                        }
                    )

                async def summarize_document(index, doc):
                    if self.thinking_callback:
                        await self.thinking_callback(
                            {
                                "type": "thinking",
                                "stage": "summarize",
                                "content": f"正在总结第 {index} 个文档...",
                            }
                        )
                    single_context = f"【参考资料{index}】{doc}\n"
                    return await asyncio.wait_for(
                        self.chain.ainvoke({"input": query, "context": single_context}),
                        timeout=30.0,
                    )

                tasks = [
                    summarize_document(index, doc)
                    for index, doc in enumerate(reordered_documents[:max_documents], 1)
                ]
                individual_summaries = await asyncio.gather(*tasks)

                if len(individual_summaries) == 1:
                    return {
                        "documents": reordered_documents,
                        "summary": individual_summaries[0],
                    }

                combined_context = (
                    "以下是多个文档的摘要，请综合这些信息生成完整回答。"
                    "不要只输出一句概括，应围绕用户问题展开说明，必要时分点回答：\n\n"
                )
                for index, summary in enumerate(individual_summaries, 1):
                    combined_context += f"【文档{index}摘要】{summary}\n\n"

                if self.thinking_callback:
                    await self.thinking_callback(
                        {
                            "type": "thinking",
                            "stage": "summarize",
                            "content": "正在综合多个文档生成最终回答...",
                        }
                    )

                final_summary = await asyncio.wait_for(
                    self.chain.ainvoke({"input": query, "context": combined_context}),
                    timeout=30.0,
                )

                return {
                    "documents": reordered_documents,
                    "summary": final_summary,
                }
            except asyncio.TimeoutError:
                logger.error("【RAG】生成摘要超时")
                return {
                    "documents": reordered_documents,
                    "summary": "抱歉，生成摘要超时，请稍后再试。",
                }
        except Exception as exc:
            logger.error(f"【RAG】生成摘要失败: {exc}", exc_info=True)
            return {
                "documents": [],
                "summary": "抱歉，处理您的请求时出现了错误。",
            }

    @traceable
    async def rag_summary(self, query: str) -> str:
        result = await self.get_documents_and_summary(query)
        return result.get("summary", "抱歉，处理您的请求时出现了错误。")
