from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class SourceDocument(BaseModel):
    doc_id: str
    chunk_id: str
    title: str
    content: str
    score: float = 0.0
    source_name: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvaluationResult(BaseModel):
    verdict: Literal["pass", "partial", "fail"] = "fail"
    passed: bool = False
    groundedness_score: float = Field(default=0.0, ge=0.0, le=1.0)
    completeness_score: float = Field(default=0.0, ge=0.0, le=1.0)
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    unsupported_claims: list[str] = Field(default_factory=list)
    missing_topics: list[str] = Field(default_factory=list)
    feedback: str = ""
    refined_query: str | None = None


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    top_k: int | None = Field(default=None, ge=1, le=20)


class PipelineTraceStep(BaseModel):
    round: int
    query: str
    retrieved: int
    verdict: str
    confidence_score: float
    latency_ms: int


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceDocument]
    evaluation: EvaluationResult
    latency_ms: int
    retrieval_results: list[SourceDocument] = Field(default_factory=list)
    trace: list[PipelineTraceStep] = Field(default_factory=list)
    model: str


class EvaluateRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    answer: str = Field(min_length=1)
    sources: list[SourceDocument] = Field(default_factory=list)


class DocumentUploadResponse(BaseModel):
    doc_id: str
    title: str
    chunks_indexed: int
    index: str


class IndexedDocument(BaseModel):
    doc_id: str
    title: str
    source_name: str | None = None
    chunks: int = 0
    created_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentListResponse(BaseModel):
    documents: list[IndexedDocument]
    count: int

