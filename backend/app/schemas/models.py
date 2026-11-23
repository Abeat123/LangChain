from typing import List, Optional, Tuple

from pydantic import BaseModel


class QueryRequest(BaseModel):
    session_id: Optional[str] = None
    query: str
    knowledge_base_id: Optional[str] = None


class RAGRequest(BaseModel):
    query: str
    knowledge_base_id: Optional[str] = None


class SessionResponse(BaseModel):
    session_id: str
    history: List[Tuple[str, str]]


class AgentStep(BaseModel):
    thought: Optional[str] = None
    tool: Optional[str] = None
    tool_input: Optional[dict] = None
    tool_output: Optional[str] = None


class AgentResponse(BaseModel):
    response: str
    session_id: str
    steps: Optional[List[AgentStep]] = None


class RAGResponse(BaseModel):
    response: str


class ReorderRequest(BaseModel):
    query: str
    documents: List[str]


class ReorderResponse(BaseModel):
    documents: List[dict]


class KnowledgeDocument(BaseModel):
    id: str
    filename: str
    original_filename: Optional[str] = None
    user_id: Optional[str] = None
    chunk_count: int
    preview: str
    created_at: Optional[str] = None


class KnowledgeListResponse(BaseModel):
    documents: List[KnowledgeDocument]
    total_count: int


class KnowledgeDocumentDetail(BaseModel):
    id: str
    filename: str
    user_id: Optional[str] = None
    chunk_count: int
    content: str
    created_at: Optional[str] = None


class ChunkInfo(BaseModel):
    chunk_id: str
    index: int
    content: str
    metadata: dict


class DocumentChunksResponse(BaseModel):
    filename: str
    total_chunks: int
    chunks: List[ChunkInfo]


class MD5Record(BaseModel):
    md5: str
    filename: Optional[str] = None
    original_filename: Optional[str] = None
    upload_time: Optional[str] = None


class MD5ListResponse(BaseModel):
    records: List[MD5Record]
    total_count: int


class KnowledgeBaseCreateRequest(BaseModel):
    name: str
    description: Optional[str] = ""


class KnowledgeBaseUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class KnowledgeBaseInfo(BaseModel):
    id: str
    name: str
    description: Optional[str] = ""
    is_default: bool
    document_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class KnowledgeBaseListResponse(BaseModel):
    knowledge_bases: List[KnowledgeBaseInfo]
    total_count: int


class AnswerFeedbackCreateRequest(BaseModel):
    session_id: Optional[str] = None
    knowledge_base_id: Optional[str] = None
    question: str
    answer: str
    feedback_type: str
    comment: Optional[str] = None


class AnswerFeedbackInfo(BaseModel):
    id: int
    session_id: Optional[str] = None
    knowledge_base_id: Optional[str] = None
    knowledge_base_name: Optional[str] = None
    question: str
    answer: str
    feedback_type: str
    comment: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class AnswerFeedbackListResponse(BaseModel):
    items: List[AnswerFeedbackInfo]
    total_count: int
    positive_count: int
    negative_count: int


class AnswerFeedbackStatsResponse(BaseModel):
    total_count: int
    positive_count: int
    negative_count: int
    positive_rate: float
