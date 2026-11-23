from typing import List, Optional

from fastapi import Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.routing import APIRouter

from app.core.rate_limit import rate_limit
from app.core.success_response import success_response
from app.router.knowledge_service import KnowledgeService, get_knowledge_service
from app.schemas.models import (
    DocumentChunksResponse,
    KnowledgeBaseCreateRequest,
    KnowledgeBaseListResponse,
    KnowledgeBaseUpdateRequest,
    KnowledgeDocumentDetail,
    KnowledgeListResponse,
    MD5ListResponse,
    MD5Record,
)
from app.services.knowledge_base_service import KnowledgeBaseService
from app.utils.auth_utils import get_current_user_id


knowledge_router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@knowledge_router.post("/add/single")
async def add_vector_single(
    file: UploadFile = File(...),
    knowledge_base_id: Optional[str] = Form(None),
    user_id: str = Depends(get_current_user_id),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
    _: None = Depends(rate_limit(limit=10, window=60)),
):
    scope_id = await KnowledgeBaseService.resolve_scope_id(user_id, knowledge_base_id)
    filename = await knowledge_service.handle_add_vector_single(file, user_id, scope_id)
    return success_response(message=f"文件 {filename} 已成功上传并存储到向量数据库")


@knowledge_router.post("/add/multiple")
async def add_vector_multiple(
    files: List[UploadFile] = File(..., description="要上传的文件列表，仅支持 PDF、TXT、MD、PPTX、DOCX"),
    knowledge_base_id: Optional[str] = Form(None),
    user_id: str = Depends(get_current_user_id),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
    _: None = Depends(rate_limit(limit=10, window=60)),
):
    scope_id = await KnowledgeBaseService.resolve_scope_id(user_id, knowledge_base_id)
    filenames = await knowledge_service.handle_add_vector_multiple(files, user_id, scope_id)
    return success_response(message=f"文件 {filenames} 已成功上传并存储到向量数据库")


@knowledge_router.post("/add/multiple/stream")
async def add_vector_multiple_stream(
    files: List[UploadFile] = File(..., description="要上传的文件列表，仅支持 PDF、TXT、MD、PPTX、DOCX"),
    knowledge_base_id: Optional[str] = Form(None),
    user_id: str = Depends(get_current_user_id),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
    _: None = Depends(rate_limit(limit=10, window=60)),
):
    scope_id = await KnowledgeBaseService.resolve_scope_id(user_id, knowledge_base_id)
    return StreamingResponse(
        knowledge_service.handle_add_vector_multiple_stream(files, user_id, scope_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        },
    )


@knowledge_router.delete("/clean")
async def clean_user_vectors(
    knowledge_base_id: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
):
    scope_id = await KnowledgeBaseService.resolve_scope_id(user_id, knowledge_base_id)
    await knowledge_service.clean_user_upload(user_id, scope_id)
    return success_response(message="已成功删除知识库中的全部文档")


@knowledge_router.delete("/md5/clear")
async def clear_user_md5(
    delete_documents: bool = True,
    knowledge_base_id: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
):
    scope_id = await KnowledgeBaseService.resolve_scope_id(user_id, knowledge_base_id)
    await knowledge_service.handle_clear_user_md5(user_id, delete_documents, scope_id)
    message = "已成功清空 MD5 记录"
    if delete_documents:
        message += "并删除对应知识库文档"
    return success_response(message=message)


@knowledge_router.delete("/md5/delete/{md5_value}")
async def delete_single_md5(
    md5_value: str,
    delete_documents: bool = True,
    knowledge_base_id: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
):
    scope_id = await KnowledgeBaseService.resolve_scope_id(user_id, knowledge_base_id)
    success = await knowledge_service.handle_delete_single_md5(user_id, md5_value, delete_documents, scope_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"MD5 记录 {md5_value} 不存在")
    return success_response(message=f"已成功删除 MD5 记录 {md5_value}")


@knowledge_router.delete("/delete/filename")
async def delete_by_filename(
    filename: str,
    delete_documents: bool = True,
    knowledge_base_id: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
):
    scope_id = await KnowledgeBaseService.resolve_scope_id(user_id, knowledge_base_id)
    success = await knowledge_service.handle_delete_by_filename(user_id, filename, delete_documents, scope_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"文件 {filename} 不存在")
    return success_response(message=f"已成功删除文件 {filename}")


@knowledge_router.get("/md5/list", response_model=MD5ListResponse)
async def get_all_md5_records(
    knowledge_base_id: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
    _: None = Depends(rate_limit(limit=10, window=60)),
):
    scope_id = await KnowledgeBaseService.resolve_scope_id(user_id, knowledge_base_id)
    records = await knowledge_service.handle_get_all_md5_records(user_id, scope_id)
    return success_response(data=MD5ListResponse(records=records, total_count=len(records)))


@knowledge_router.get("/md5/{md5_value}", response_model=MD5Record)
async def get_md5_info(
    md5_value: str,
    knowledge_base_id: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
    _: None = Depends(rate_limit(limit=10, window=60)),
):
    scope_id = await KnowledgeBaseService.resolve_scope_id(user_id, knowledge_base_id)
    md5_info = await knowledge_service.handle_get_md5_info(user_id, md5_value, scope_id)
    if not md5_info:
        raise HTTPException(status_code=404, detail=f"MD5 记录 {md5_value} 不存在")
    return success_response(data=md5_info)


@knowledge_router.get("/list", response_model=KnowledgeListResponse)
async def get_user_knowledge_list(
    knowledge_base_id: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
    _: None = Depends(rate_limit(limit=10, window=60)),
):
    scope_id = await KnowledgeBaseService.resolve_scope_id(user_id, knowledge_base_id)
    documents = await knowledge_service.handle_get_user_knowledge(user_id, scope_id)
    return success_response(data=KnowledgeListResponse(documents=documents, total_count=len(documents)))


@knowledge_router.get("/detail", response_model=KnowledgeDocumentDetail)
async def get_document_detail(
    filename: str,
    knowledge_base_id: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
    _: None = Depends(rate_limit(limit=10, window=60)),
):
    scope_id = await KnowledgeBaseService.resolve_scope_id(user_id, knowledge_base_id)
    document = await knowledge_service.handle_get_document_detail(user_id, filename, scope_id)
    return success_response(data=document)


@knowledge_router.get("/chunks", response_model=DocumentChunksResponse)
async def get_document_chunks(
    filename: str,
    knowledge_base_id: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
    _: None = Depends(rate_limit(limit=10, window=60)),
):
    scope_id = await KnowledgeBaseService.resolve_scope_id(user_id, knowledge_base_id)
    chunks = await knowledge_service.handle_get_document_chunks(user_id, filename, scope_id)
    return success_response(data=chunks)


@knowledge_router.get("/bases", response_model=KnowledgeBaseListResponse)
async def get_knowledge_bases(
    user_id: str = Depends(get_current_user_id),
    _: None = Depends(rate_limit(limit=20, window=60)),
):
    items = await KnowledgeBaseService.list_user_bases(user_id)
    return success_response(data=KnowledgeBaseListResponse(knowledge_bases=items, total_count=len(items)))


@knowledge_router.post("/bases")
async def create_knowledge_base(
    request: KnowledgeBaseCreateRequest,
    user_id: str = Depends(get_current_user_id),
    _: None = Depends(rate_limit(limit=10, window=60)),
):
    item = await KnowledgeBaseService.create_base(user_id, request.name, request.description)
    return success_response(data=item, message="知识库创建成功")


@knowledge_router.patch("/bases/{knowledge_base_id}")
async def update_knowledge_base(
    knowledge_base_id: str,
    request: KnowledgeBaseUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    _: None = Depends(rate_limit(limit=10, window=60)),
):
    item = await KnowledgeBaseService.update_base(
        user_id,
        knowledge_base_id,
        name=request.name,
        description=request.description,
    )
    return success_response(data=item, message="知识库更新成功")


@knowledge_router.delete("/bases/{knowledge_base_id}")
async def delete_knowledge_base(
    knowledge_base_id: str,
    user_id: str = Depends(get_current_user_id),
    _: None = Depends(rate_limit(limit=10, window=60)),
):
    await KnowledgeBaseService.delete_base(user_id, knowledge_base_id)
    return success_response(message="知识库删除成功")
