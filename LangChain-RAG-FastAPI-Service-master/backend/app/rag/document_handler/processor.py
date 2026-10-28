import asyncio
import os
import tempfile
from typing import Optional

from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.core.logger_handler import logger
from app.rag.text_spliter import AsyncTextSplitter
from app.utils.config import chroma_config
from app.utils.factory import embed_model
from app.utils.file_handler import (
    get_file_md5_hex,
    listdir_allowed_type,
    markdown_loader,
    markdown_loader_sync,
    pdf_loader,
    pdf_loader_sync,
    ppt_loader,
    ppt_loader_sync,
    txt_loader,
    txt_loader_sync,
    word_loader,
    word_loader_sync,
)


class DocumentProcessor:
    def __init__(
        self,
        vectors_store: Chroma,
        md5_store,
        knowledge_base_scope_id: Optional[str] = None,
    ):
        self.vectors_store = vectors_store
        self.md5_store = md5_store
        self.knowledge_base_scope_id = knowledge_base_scope_id
        self.spliter = AsyncTextSplitter(
            chunk_size=chroma_config["chunk_size"],
            chunk_overlap=chroma_config["chunk_overlap"],
            separators=chroma_config["separators"],
            embedding_model=embed_model,
        )

    async def get_file_document(self, read_path: str) -> list[Document]:
        if read_path.endswith(".txt"):
            return await txt_loader(read_path)
        if read_path.endswith(".pdf"):
            return await pdf_loader(read_path)
        if read_path.endswith(".md"):
            return await markdown_loader(read_path)
        if read_path.endswith(".pptx"):
            return await ppt_loader(read_path)
        if read_path.endswith(".docx"):
            return await word_loader(read_path)
        return []

    def get_file_document_sync(self, read_path: str) -> list[Document]:
        if read_path.endswith(".txt"):
            return txt_loader_sync(read_path)
        if read_path.endswith(".pdf"):
            return pdf_loader_sync(read_path)
        if read_path.endswith(".md"):
            return markdown_loader_sync(read_path)
        if read_path.endswith(".pptx"):
            return ppt_loader_sync(read_path)
        if read_path.endswith(".docx"):
            return word_loader_sync(read_path)
        return []

    def split_documents_sync(self, documents: list[Document]) -> list[Document]:
        return self.spliter.split_documents_sync(documents)

    async def get_document(self, files: list = None, user_id: str = None, progress_callback=None):
        file_paths = []
        file_names = {}

        if files:
            for file in files:
                temp_file = await asyncio.to_thread(
                    tempfile.NamedTemporaryFile,
                    delete=False,
                    suffix=os.path.splitext(file.filename)[1],
                )
                content = await file.read()
                try:
                    await asyncio.to_thread(temp_file.write, content)
                finally:
                    # Flush the buffer and release Windows' file handle before parsing.
                    await asyncio.to_thread(temp_file.close)
                file_paths.append(temp_file.name)
                file_names[temp_file.name] = file.filename
        else:
            allowed_file_path = await listdir_allowed_type(
                chroma_config["data_path"],
                tuple(chroma_config["allow_knowledge_file_types"]),
            )
            file_paths = list(allowed_file_path)

        for file_path in file_paths:
            filename = file_names.get(file_path, os.path.basename(file_path))
            md5_hex = await get_file_md5_hex(file_path)

            if await self.md5_store.check_md5_hex(md5_hex, user_id, self.knowledge_base_scope_id):
                if progress_callback:
                    await progress_callback(
                        {
                            "step": "skipping",
                            "filename": filename,
                            "message": f"文件 {filename} 已存在，已跳过",
                        }
                    )
                logger.info(f"【向量数据库】文件 {filename} 已存在，跳过写入")
                self._cleanup_temp_file(files, file_path)
                continue

            try:
                if progress_callback:
                    await progress_callback(
                        {
                            "step": "loading",
                            "filename": filename,
                            "message": f"正在加载文档 {filename}...",
                        }
                    )

                document = await self.get_file_document(file_path)
                if not document:
                    if progress_callback:
                        await progress_callback(
                            {
                                "step": "error",
                                "filename": filename,
                                "message": f"文件 {filename} 内容为空，已跳过",
                                "error_message": "文档内容为空",
                            }
                        )
                    self._cleanup_temp_file(files, file_path)
                    continue

                if progress_callback:
                    await progress_callback(
                        {
                            "step": "splitting",
                            "filename": filename,
                            "message": f"正在切分文档 {filename}...",
                        }
                    )

                document = await self.spliter.split_documents(document)
                if not document:
                    if progress_callback:
                        await progress_callback(
                            {
                                "step": "error",
                                "filename": filename,
                                "message": f"文件 {filename} 切分结果为空，已跳过",
                                "error_message": "文档切分后为空",
                            }
                        )
                    self._cleanup_temp_file(files, file_path)
                    continue

                if progress_callback:
                    await progress_callback(
                        {
                            "step": "storing",
                            "filename": filename,
                            "message": f"正在写入向量 {filename}...",
                        }
                    )

                for doc in document:
                    if user_id:
                        doc.metadata["user_id"] = user_id
                    doc.metadata["original_filename"] = filename
                    doc.metadata["md5"] = md5_hex
                    if self.knowledge_base_scope_id:
                        doc.metadata["knowledge_base_id"] = self.knowledge_base_scope_id

                await asyncio.to_thread(self.vectors_store.add_documents, document)

                original_filename = file_names.get(file_path, filename) if files else filename
                await self.md5_store.save_md5_hex(
                    md5_hex,
                    filename,
                    original_filename,
                    user_id,
                    self.knowledge_base_scope_id,
                )

                if progress_callback:
                    await progress_callback(
                        {
                            "step": "completed",
                            "filename": filename,
                            "message": f"文件 {filename} 处理完成",
                        }
                    )
            except Exception as exc:
                if progress_callback:
                    await progress_callback(
                        {
                            "step": "error",
                            "filename": filename,
                            "message": f"文件 {filename} 处理失败",
                            "error_message": str(exc),
                        }
                    )
                logger.error(f"【向量数据库】处理文件 {filename} 失败: {exc}")
            finally:
                self._cleanup_temp_file(files, file_path)

    @staticmethod
    def _cleanup_temp_file(files, file_path: str):
        if not files:
            return
        try:
            os.unlink(file_path)
        except OSError:
            pass
