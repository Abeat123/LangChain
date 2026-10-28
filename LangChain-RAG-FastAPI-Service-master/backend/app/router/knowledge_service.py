import asyncio
import mimetypes
import os
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, List, Optional

try:
    import magic
except ImportError:  # pragma: no cover
    magic = None

from fastapi import HTTPException, UploadFile

from app.core.logger_handler import logger
from app.rag.sse_models import SSEEvent, SliceResult
from app.rag.task_queue import TaskQueue
from app.rag.text_spliter import AsyncTextSplitter
from app.rag.vector_store import VectorStoreService
from app.utils.config import chroma_config
from app.utils.file_handler import (
    get_file_md5_hex_sync,
    markdown_loader_sync,
    pdf_loader_sync,
    ppt_loader_sync,
    txt_loader_sync,
    word_loader_sync,
)


ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".pptx", ".docx"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "text/plain",
    "text/markdown",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
MAX_FILE_SIZE = 20 * 1024 * 1024
MAX_FOLDER_SIZE = 200 * 1024 * 1024


@dataclass
class ProcessingState:
    total_files: int = 0
    total_valid: int = 0
    sliced_count: int = 0
    written_count: int = 0
    success_count: int = 0
    failed_count: int = 0
    slice_success_count: int = 0

    def current_progress(self) -> int:
        if self.total_valid == 0:
            return 0
        slice_progress = (self.sliced_count / self.total_valid) * 60
        write_progress = (self.written_count / self.total_valid) * 40
        return int(min(99, slice_progress + write_progress))


def _load_file_document_sync(read_path: str):
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


def _split_documents_sync(documents):
    splitter = AsyncTextSplitter(
        chunk_size=chroma_config["chunk_size"],
        chunk_overlap=chroma_config["chunk_overlap"],
        separators=chroma_config["separators"],
    )
    return splitter.split_documents_sync(documents)


def _sync_slice_file(
    file_content: bytes,
    filename: str,
    file_index: int,
    user_id: str,
    queue: TaskQueue,
    knowledge_base_scope_id: Optional[str] = None,
):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name

        try:
            documents = _load_file_document_sync(temp_file_path)
            if not documents:
                queue.put(SliceResult.error_result(file_index=file_index, filename=filename, error="文件内容为空"))
                return

            split_docs = _split_documents_sync(documents)
            if not split_docs:
                queue.put(SliceResult.error_result(file_index=file_index, filename=filename, error="切片结果为空"))
                return

            md5_hex = get_file_md5_hex_sync(temp_file_path)
            for doc in split_docs:
                doc.metadata["user_id"] = user_id
                doc.metadata["source"] = filename
                doc.metadata["filename"] = filename
                doc.metadata["original_filename"] = filename
                doc.metadata["md5"] = md5_hex
                if knowledge_base_scope_id:
                    doc.metadata["knowledge_base_id"] = knowledge_base_scope_id

            queue.put(
                SliceResult.success_result(
                    file_index=file_index,
                    filename=filename,
                    documents=split_docs,
                    md5=md5_hex,
                )
            )
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    except Exception as exc:
        logger.error(f"【知识库上传】切片文件 {filename} 失败: {exc}")
        queue.put(SliceResult.error_result(file_index=file_index, filename=filename, error=str(exc)))


class KnowledgeService:
    @staticmethod
    def _detect_file_type(filename: str, content: bytes) -> str:
        if magic is not None:
            try:
                return magic.Magic(mime=True).from_buffer(content)
            except Exception as exc:
                logger.warning(f"libmagic 检测失败，改用扩展名兜底: {exc}")

        guessed_type, _ = mimetypes.guess_type(filename)
        return guessed_type or "application/octet-stream"

    async def handle_add_vector_single(
        self,
        file: UploadFile,
        user_id: str,
        knowledge_base_scope_id: Optional[str] = None,
    ) -> str:
        store = VectorStoreService(knowledge_base_scope_id=knowledge_base_scope_id)

        if file.size and file.size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="文件大小不能超过 20MB")

        content = await file.read()
        await file.seek(0)

        file_type = self._detect_file_type(file.filename, content)
        file_extension = os.path.splitext(file.filename)[1].lower()

        if file_type not in ALLOWED_MIME_TYPES and file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=(
                    "文件类型不受支持，目前仅支持 PDF、TXT、Markdown、PPTX、DOCX。"
                    f"检测到类型: {file_type}，扩展名: {file_extension}"
                ),
            )

        await store.get_document(files=[file], user_id=user_id)
        return file.filename

    async def handle_add_vector_multiple(
        self,
        files: List[UploadFile],
        user_id: str,
        knowledge_base_scope_id: Optional[str] = None,
    ) -> List[str]:
        total_size = sum(file.size or 0 for file in files)
        if total_size > MAX_FOLDER_SIZE:
            raise HTTPException(status_code=400, detail="文件总大小不能超过 200MB")

        results = []
        for file in files:
            await self.handle_add_vector_single(file, user_id, knowledge_base_scope_id)
            results.append(file.filename)
        return results

    def _yield_start_event(self, total_files: int) -> str:
        return SSEEvent(event_type="start", total_files=total_files, message="开始处理文件...", progress=0).to_sse()

    def _yield_size_error_event(self) -> str:
        return SSEEvent(
            event_type="error",
            message="文件总大小不能超过 200MB",
            error_message="文件总大小不能超过 200MB",
        ).to_sse()

    def _yield_validation_error_event(
        self,
        current_index: int,
        total_files: int,
        filename: str,
        file_type: str,
        file_extension: str,
        failed_count: int,
    ) -> str:
        return SSEEvent(
            event_type="error",
            file_index=current_index,
            total_files=total_files,
            filename=filename,
            step="validation",
            message=f"文件 {filename} 类型不支持",
            error_message=f"文件类型: {file_type}，扩展名: {file_extension}",
            progress=int(current_index / total_files * 100),
            failed_count=failed_count,
        ).to_sse()

    def _yield_slicing_completed_event(self, result: SliceResult, state: ProcessingState) -> str:
        return SSEEvent(
            event_type="slicing_completed",
            file_index=result.file_index,
            total_files=state.total_files,
            filename=result.filename,
            chunk_count=result.chunk_count,
            step="slicing",
            message=f"文件 {result.filename} 切片完成，共 {result.chunk_count} 个切片",
            progress=state.current_progress(),
            success_count=state.success_count,
            failed_count=state.failed_count,
            slice_success_count=state.slice_success_count,
        ).to_sse()

    def _yield_writing_event(self, result: SliceResult, state: ProcessingState) -> str:
        return SSEEvent(
            event_type="writing",
            file_index=result.file_index,
            total_files=state.total_files,
            filename=result.filename,
            step="writing",
            message=f"正在写入向量 {result.filename}...",
            progress=state.current_progress(),
            success_count=state.success_count,
            failed_count=state.failed_count,
            slice_success_count=state.slice_success_count,
        ).to_sse()

    def _yield_completed_event(self, result: SliceResult, state: ProcessingState) -> str:
        return SSEEvent(
            event_type="completed",
            file_index=result.file_index,
            total_files=state.total_files,
            filename=result.filename,
            step="completed",
            message=f"文件 {result.filename} 处理完成",
            progress=state.current_progress(),
            success_count=state.success_count,
            failed_count=state.failed_count,
            slice_success_count=state.slice_success_count,
        ).to_sse()

    def _yield_write_error_event(self, result: SliceResult, state: ProcessingState, error: str) -> str:
        return SSEEvent(
            event_type="error",
            file_index=result.file_index,
            total_files=state.total_files,
            filename=result.filename,
            step="writing",
            message=f"文件 {result.filename} 写入失败",
            error_message=error,
            progress=state.current_progress(),
            success_count=state.success_count,
            failed_count=state.failed_count,
            slice_success_count=state.slice_success_count,
        ).to_sse()

    def _yield_slice_error_event(self, result: SliceResult, state: ProcessingState) -> str:
        return SSEEvent(
            event_type="error",
            file_index=result.file_index,
            total_files=state.total_files,
            filename=result.filename,
            step="slicing",
            message=f"文件 {result.filename} 切片失败",
            error_message=result.error,
            progress=state.current_progress(),
            success_count=state.success_count,
            failed_count=state.failed_count,
            slice_success_count=state.slice_success_count,
        ).to_sse()

    def _yield_finish_event(self, start_time: float, total_files: int, success_count: int, failed_count: int) -> str:
        total_time = round(time.time() - start_time, 2)
        return SSEEvent(
            event_type="finish",
            total_files=total_files,
            success_count=success_count,
            failed_count=failed_count,
            message=f"处理完成，耗时 {total_time} 秒",
            progress=100,
        ).to_sse()

    async def _validate_and_read_files(self, files: List[UploadFile]) -> tuple[List[dict], List[str], int]:
        total_files = len(files)
        total_size = 0
        files_content = []
        error_events: List[str] = []

        for file in files:
            content = await file.read()
            files_content.append({"file": file, "content": content})
            total_size += len(content)
            await file.seek(0)

        if total_size > MAX_FOLDER_SIZE:
            return [], [self._yield_size_error_event()], total_files

        valid_files = []
        failed_count = 0
        for current_index, file_info in enumerate(files_content, 1):
            file = file_info["file"]
            content = file_info["content"]
            file_type = self._detect_file_type(file.filename, content)
            file_extension = os.path.splitext(file.filename)[1].lower()

            if file_type not in ALLOWED_MIME_TYPES and file_extension not in ALLOWED_EXTENSIONS:
                failed_count += 1
                error_events.append(
                    self._yield_validation_error_event(
                        current_index,
                        total_files,
                        file.filename,
                        file_type,
                        file_extension,
                        failed_count,
                    )
                )
            else:
                valid_files.append(
                    {
                        "content": content,
                        "filename": file.filename,
                        "file_index": current_index,
                    }
                )

        return valid_files, error_events, total_files

    def _start_slicing(
        self,
        valid_files: List[dict],
        user_id: str,
        knowledge_base_scope_id: Optional[str] = None,
    ) -> tuple[TaskQueue, ThreadPoolExecutor, list]:
        queue = TaskQueue(maxsize=10)
        queue.set_total_count(len(valid_files))

        slice_tasks = [
            (info["content"], info["filename"], info["file_index"], user_id, queue, knowledge_base_scope_id)
            for info in valid_files
        ]
        max_workers = min(len(slice_tasks), max(1, os.cpu_count() or 1))
        executor = ThreadPoolExecutor(max_workers=max_workers)
        futures = [executor.submit(_sync_slice_file, *args) for args in slice_tasks]
        return queue, executor, futures

    async def _process_slice_results(
        self,
        queue: TaskQueue,
        valid_count: int,
        store: VectorStoreService,
        state: ProcessingState,
        user_id: str,
    ) -> AsyncGenerator[str, None]:
        while state.written_count < valid_count:
            try:
                result = queue.get(block=True, timeout=0.1)
                state.sliced_count += 1

                if result.success:
                    state.slice_success_count += 1
                    yield self._yield_slicing_completed_event(result, state)

                    try:
                        yield self._yield_writing_event(result, state)
                        await asyncio.to_thread(store.vectors_store.add_documents, result.documents)
                        await store.save_md5_hex(result.md5, result.filename, result.filename, user_id)
                        state.success_count += 1
                        state.written_count += 1
                        yield self._yield_completed_event(result, state)
                    except Exception as exc:
                        state.written_count += 1
                        state.failed_count += 1
                        logger.error(f"【知识库上传】写入文件 {result.filename} 失败: {exc}")
                        yield self._yield_write_error_event(result, state, str(exc))
                else:
                    state.written_count += 1
                    state.failed_count += 1
                    yield self._yield_slice_error_event(result, state)

                queue.task_done()
            except Exception:
                continue

    async def handle_add_vector_multiple_stream(
        self,
        files: List[UploadFile],
        user_id: str,
        knowledge_base_scope_id: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        total_files = len(files)
        logger.info(f"【知识库上传】开始处理上传，文件数: {total_files}，用户: {user_id}")
        yield self._yield_start_event(total_files)

        valid_files, error_events, _ = await self._validate_and_read_files(files)
        for event in error_events:
            yield event

        if not valid_files:
            return

        start_time = time.time()
        state = ProcessingState(total_files=total_files, total_valid=len(valid_files))
        queue, executor, _ = self._start_slicing(valid_files, user_id, knowledge_base_scope_id)
        store = VectorStoreService(knowledge_base_scope_id=knowledge_base_scope_id)

        async for sse in self._process_slice_results(queue, len(valid_files), store, state, user_id):
            yield sse

        executor.shutdown(wait=True)
        yield self._yield_finish_event(start_time, total_files, state.success_count, state.failed_count)

    async def clean_user_upload(self, user_id: str, knowledge_base_scope_id: Optional[str] = None) -> None:
        store = VectorStoreService(knowledge_base_scope_id=knowledge_base_scope_id)
        await store.delete_user_documents(user_id)

    async def handle_clear_user_md5(
        self,
        user_id: str,
        delete_documents: bool = True,
        knowledge_base_scope_id: Optional[str] = None,
    ) -> None:
        store = VectorStoreService(knowledge_base_scope_id=knowledge_base_scope_id)
        await store.delete_user_md5(user_id, delete_documents)

    async def handle_delete_single_md5(
        self,
        user_id: str,
        md5_value: str,
        delete_documents: bool = True,
        knowledge_base_scope_id: Optional[str] = None,
    ) -> bool:
        store = VectorStoreService(knowledge_base_scope_id=knowledge_base_scope_id)
        return await store.delete_single_md5(user_id, md5_value, delete_documents)

    async def handle_delete_by_filename(
        self,
        user_id: str,
        filename: str,
        delete_documents: bool = True,
        knowledge_base_scope_id: Optional[str] = None,
    ) -> bool:
        store = VectorStoreService(knowledge_base_scope_id=knowledge_base_scope_id)
        return await store.delete_by_filename(user_id, filename, delete_documents)

    async def handle_get_md5_info(self, user_id: str, md5_value: str, knowledge_base_scope_id: Optional[str] = None):
        store = VectorStoreService(knowledge_base_scope_id=knowledge_base_scope_id)
        return await store.get_md5_info(user_id, md5_value)

    async def handle_get_all_md5_records(self, user_id: str, knowledge_base_scope_id: Optional[str] = None):
        store = VectorStoreService(knowledge_base_scope_id=knowledge_base_scope_id)
        return await store.get_all_md5_records(user_id)

    async def handle_get_user_knowledge(self, user_id: str, knowledge_base_scope_id: Optional[str] = None) -> list:
        store = VectorStoreService(knowledge_base_scope_id=knowledge_base_scope_id)
        return await store.get_user_documents(user_id)

    async def handle_get_document_detail(
        self,
        user_id: str,
        filename: str,
        knowledge_base_scope_id: Optional[str] = None,
    ) -> dict:
        store = VectorStoreService(knowledge_base_scope_id=knowledge_base_scope_id)
        document = await store.get_document_detail(user_id, filename)
        if not document:
            raise HTTPException(status_code=404, detail=f"文档 {filename} 不存在")
        return document

    async def handle_get_document_chunks(
        self,
        user_id: str,
        filename: str,
        knowledge_base_scope_id: Optional[str] = None,
    ) -> dict:
        store = VectorStoreService(knowledge_base_scope_id=knowledge_base_scope_id)
        chunks = await store.get_document_chunks(user_id, filename)
        if chunks["total_chunks"] == 0:
            raise HTTPException(status_code=404, detail=f"文档 {filename} 不存在或没有切片")
        return chunks


def get_knowledge_service() -> KnowledgeService:
    return KnowledgeService()
