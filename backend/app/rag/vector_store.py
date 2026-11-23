import asyncio
import hashlib
import os
from typing import Optional

from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.core.logger_handler import logger
from app.utils.config import chroma_config
from app.utils.factory import embed_model
from app.utils.path_tool import get_abstract_path

from .document_handler import DocumentProcessor
from .md5_manager import MD5Store
from .retrievers.hybrid_retriever import HybridRetriever


class VectorStoreService:
    def __init__(self, knowledge_base_scope_id: Optional[str] = None):
        self.knowledge_base_scope_id = knowledge_base_scope_id
        persist_dir = get_abstract_path(chroma_config["persist_directory"])
        self.collection_name = self._build_collection_name(knowledge_base_scope_id)
        self.vectors_store = Chroma(
            collection_name=self.collection_name,
            embedding_function=embed_model,
            persist_directory=persist_dir,
        )

        self.md5_store = MD5Store()
        self.hybrid_retriever = HybridRetriever(self.vectors_store)
        self.document_processor = DocumentProcessor(
            self.vectors_store,
            self.md5_store,
            knowledge_base_scope_id=knowledge_base_scope_id,
        )

    @staticmethod
    def _build_collection_name(knowledge_base_scope_id: Optional[str]) -> str:
        base_name = chroma_config["collection_name"]
        if not knowledge_base_scope_id:
            return base_name

        digest = hashlib.md5(knowledge_base_scope_id.encode("utf-8")).hexdigest()[:24]
        candidate = f"{base_name[:30]}-{digest}"
        return candidate[:63].strip("-")

    async def get_bm25_retriever(self, user_id: Optional[str] = None):
        return await self.hybrid_retriever.get_bm25_retriever(user_id)

    async def _get_all_documents(self) -> list[Document]:
        return await self.hybrid_retriever._get_all_documents()

    async def get_retriever(self, query: Optional[str] = None, user_id: Optional[str] = None):
        return await self.hybrid_retriever.get_retriever(query, user_id)

    @staticmethod
    async def get_dynamic_weights(query: Optional[str] = None):
        return await HybridRetriever.get_dynamic_weights(query)

    async def check_md5_hex(self, md5_for_check: str, user_id: Optional[str] = None) -> bool:
        return await self.md5_store.check_md5_hex(
            md5_for_check,
            user_id,
            self.knowledge_base_scope_id,
        )

    async def save_md5_hex(
        self,
        md5_hex: str,
        filename: Optional[str] = None,
        original_filename: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        await self.md5_store.save_md5_hex(
            md5_hex,
            filename,
            original_filename,
            user_id,
            self.knowledge_base_scope_id,
        )

    def save_md5_hex_sync(
        self,
        md5_hex: str,
        filename: Optional[str] = None,
        original_filename: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        self.md5_store.save_md5_hex_sync(
            md5_hex,
            filename,
            original_filename,
            user_id,
            self.knowledge_base_scope_id,
        )

    async def delete_user_documents(self, user_id: str):
        await self.delete_user_md5(user_id, delete_documents=True)

    async def delete_user_md5(self, user_id: str, delete_documents: bool = True):
        try:
            if delete_documents:
                await asyncio.to_thread(self.vectors_store.delete, where={"user_id": user_id})
                logger.info(f"【向量数据库】已删除用户 {user_id} 的全部文档")

            await self.md5_store.delete_user_md5(user_id, self.knowledge_base_scope_id)
        except Exception as exc:
            logger.error(f"【向量数据库】删除用户 {user_id} 的 MD5 记录失败: {exc}")
            raise

    async def delete_by_filename(self, user_id: str, filename: str, delete_documents: bool = True):
        try:
            md5_to_delete = await self.md5_store.delete_by_filename(
                user_id,
                filename,
                self.knowledge_base_scope_id,
            )
            if md5_to_delete is None:
                logger.warning(f"【向量数据库】文件 {filename} 不存在")
                return False

            if delete_documents:
                where_clause = {"$and": [{"user_id": user_id}, {"md5": md5_to_delete}]}
                await asyncio.to_thread(self.vectors_store.delete, where=where_clause)

            return True
        except Exception as exc:
            logger.error(f"【向量数据库】删除文件 {filename} 失败: {exc}")
            return False

    async def delete_single_md5(self, user_id: str, md5_to_delete: str, delete_documents: bool = True):
        try:
            success = await self.md5_store.delete_single_md5(
                user_id,
                md5_to_delete,
                self.knowledge_base_scope_id,
            )
            if not success:
                return False

            if delete_documents:
                where_clause = {"$and": [{"user_id": user_id}, {"md5": md5_to_delete}]}
                await asyncio.to_thread(self.vectors_store.delete, where=where_clause)

            return True
        except Exception as exc:
            logger.error(f"【向量数据库】删除 MD5 记录失败: {exc}")
            return False

    async def get_md5_info(self, user_id: str, md5_value: str):
        try:
            return await self.md5_store.get_md5_info(
                user_id,
                md5_value,
                self.knowledge_base_scope_id,
            )
        except Exception as exc:
            logger.error(f"【向量数据库】获取 MD5 记录失败: {exc}")
            return None

    async def get_all_md5_records(self, user_id: str):
        try:
            return await self.md5_store.get_all_md5_records(
                user_id,
                self.knowledge_base_scope_id,
            )
        except Exception as exc:
            logger.error(f"【向量数据库】获取 MD5 列表失败: {exc}")
            return []

    async def get_user_documents(self, user_id: Optional[str] = None):
        try:
            where_clause = {"user_id": user_id} if user_id else None
            all_docs = await asyncio.to_thread(
                self.vectors_store.get,
                include=["documents", "metadatas"],
                where=where_clause,
            )

            docs_info = {}
            for index, doc_id in enumerate(all_docs["ids"]):
                metadata = all_docs["metadatas"][index] if index < len(all_docs["metadatas"]) else {}
                content = all_docs["documents"][index] if index < len(all_docs["documents"]) else ""

                filename = metadata.get("source", metadata.get("filename", "unknown"))
                if isinstance(filename, str) and "\\" in filename:
                    filename = os.path.basename(filename)

                original_filename = metadata.get("original_filename", filename)
                if filename not in docs_info:
                    docs_info[filename] = {
                        "id": doc_id,
                        "filename": filename,
                        "original_filename": original_filename,
                        "user_id": metadata.get("user_id"),
                        "chunk_count": 0,
                        "preview": "",
                        "created_at": metadata.get("created_at"),
                    }

                docs_info[filename]["chunk_count"] += 1
                if not docs_info[filename]["preview"] and content:
                    preview_length = 100
                    docs_info[filename]["preview"] = content[:preview_length] + (
                        "..." if len(content) > preview_length else ""
                    )

            return list(docs_info.values())
        except Exception as exc:
            logger.error(f"【向量数据库】获取用户知识库列表失败: {exc}")
            raise

    async def get_document_detail(self, user_id: str, filename: str):
        try:
            all_docs = await asyncio.to_thread(
                self.vectors_store.get,
                include=["documents", "metadatas"],
                where={"user_id": user_id},
            )

            doc_info = None
            full_content = []
            chunk_count = 0

            for index, doc_id in enumerate(all_docs["ids"]):
                metadata = all_docs["metadatas"][index] if index < len(all_docs["metadatas"]) else {}
                content = all_docs["documents"][index] if index < len(all_docs["documents"]) else ""
                source = metadata.get("source", metadata.get("filename", ""))
                source_name = os.path.basename(source) if isinstance(source, str) else str(source)

                if source_name == filename:
                    if doc_info is None:
                        doc_info = {
                            "id": doc_id,
                            "filename": filename,
                            "user_id": metadata.get("user_id"),
                            "chunk_count": 0,
                            "content": "",
                            "created_at": metadata.get("created_at"),
                        }
                    chunk_count += 1
                    full_content.append(content)

            if doc_info is not None:
                doc_info["chunk_count"] = chunk_count
                doc_info["content"] = "\n".join(full_content)

            return doc_info
        except Exception as exc:
            logger.error(f"【向量数据库】获取文档详情失败: {exc}")
            raise

    async def get_document_chunks(self, user_id: str, filename: str):
        try:
            all_docs = await asyncio.to_thread(
                self.vectors_store.get,
                include=["documents", "metadatas"],
                where={"user_id": user_id},
            )

            chunks = []
            chunk_index = 0
            for index, doc_id in enumerate(all_docs["ids"]):
                metadata = all_docs["metadatas"][index] if index < len(all_docs["metadatas"]) else {}
                content = all_docs["documents"][index] if index < len(all_docs["documents"]) else ""
                source = metadata.get("source", metadata.get("filename", ""))
                source_name = os.path.basename(source) if isinstance(source, str) else str(source)

                if source_name == filename:
                    chunks.append(
                        {
                            "chunk_id": doc_id,
                            "index": chunk_index,
                            "content": content,
                            "metadata": metadata,
                        }
                    )
                    chunk_index += 1

            return {
                "filename": filename,
                "total_chunks": len(chunks),
                "chunks": chunks,
            }
        except Exception as exc:
            logger.error(f"【向量数据库】获取文档切片失败: {exc}")
            raise

    async def get_file_document(self, read_path: str) -> list[Document]:
        return await self.document_processor.get_file_document(read_path)

    def get_file_document_sync(self, read_path: str) -> list[Document]:
        return self.document_processor.get_file_document_sync(read_path)

    def split_documents_sync(self, documents: list[Document]) -> list[Document]:
        return self.document_processor.split_documents_sync(documents)

    async def get_document(self, files: list = None, user_id: str = None, progress_callback=None):
        await self.document_processor.get_document(files, user_id, progress_callback)
