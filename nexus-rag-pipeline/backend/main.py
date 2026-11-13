from __future__ import annotations
import os
import logging
from contextlib import asynccontextmanager
from time import time

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.config import get_settings
from backend.evaluation.evaluator import ResponseEvaluator
from backend.ingestion.documents import index_upload
from backend.logging_config import configure_logging
from backend.metrics import MetricsStore
from backend.monitoring import create_structured_logger
from backend.pipeline.rag_pipeline import RagPipeline
from backend.rate_limit import RateLimitMiddleware
from backend.retrieval.retriever import ElasticsearchRetriever
from backend.schemas import (
    DocumentListResponse,
    DocumentUploadResponse,
    EvaluateRequest,
    EvaluationResult,
    QueryRequest,
    QueryResponse,
)
from backend.security import SecurityHeadersMiddleware
from backend.services.elasticsearch_client import ElasticsearchService
from backend.services.gemini import GeminiService

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)
structured_logger = create_structured_logger(__name__)

metrics = MetricsStore()
gemini_service = GeminiService(settings)
elasticsearch_service = ElasticsearchService(settings)
retriever = ElasticsearchRetriever(elasticsearch=elasticsearch_service, gemini=gemini_service)
evaluator = ResponseEvaluator(gemini=gemini_service)
pipeline = RagPipeline(
    settings=settings,
    retriever=retriever,
    gemini=gemini_service,
    evaluator=evaluator,
    metrics=metrics,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await elasticsearch_service.close()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Gemini-powered closed-loop RAG API with Elasticsearch retrieval.",
    lifespan=lifespan,
)

# Add security headers middleware (must be before other middleware)
if settings.environment == "production":
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=60, requests_per_hour=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")


@app.get("/")
async def service_status() -> dict:
    return {
        "service": settings.app_name,
        "status": "ok",
        "ui": "/app",
        "api_docs": "/docs",
        "model": settings.gemini_model,
        "index": settings.elasticsearch_index,
        "timestamp": time(),
    }


@app.get("/app")
async def app_shell() -> FileResponse:
    return FileResponse(settings.static_dir / "index.html")


@app.get("/health")
async def health() -> dict:
    """Enhanced health check for production deployments.
    
    Returns:
        - status: "ok" (all checks pass), "degraded" (partial failure), or "unhealthy"
        - checks: Individual component health status
        - timestamp: Server time for clock skew detection
        - configuration: Current runtime configuration (for debugging)
        
    Status codes:
        - 200 OK: Service is healthy (status: "ok")
        - 503 Service Unavailable: Service is degraded or unhealthy
    """
    start_time = time()
    elasticsearch_ok = False
    elasticsearch_latency = 0

    try:
        elasticsearch_ok = await elasticsearch_service.ping()
        elasticsearch_latency = (time() - start_time) * 1000
    except Exception as exc:
        logger.warning(f"Elasticsearch health check failed: {exc}")
        structured_logger.log_error(
            "elasticsearch_health_check_failed",
            str(exc),
            exception=exc,
        )

    gemini_ok = gemini_service.configured

    # Determine overall status
    if elasticsearch_ok and gemini_ok:
        status = "ok"
        status_code = 200
    elif elasticsearch_ok or gemini_ok:
        status = "degraded"
        status_code = 503
    else:
        status = "unhealthy"
        status_code = 503

    response = {
        "status": status,
        "timestamp": time(),
        "checks": {
            "gemini_configured": gemini_ok,
            "gemini_api_available": gemini_ok,
            "elasticsearch_configured": elasticsearch_service.configured,
            "elasticsearch_reachable": elasticsearch_ok,
            "elasticsearch_latency_ms": round(elasticsearch_latency, 2),
        },
        "configuration": {
            "environment": settings.environment,
            "gemini_model": settings.gemini_model,
            "gemini_embedding_model": settings.gemini_embedding_model,
            "elasticsearch_index": settings.elasticsearch_index,
            "max_rag_rounds": settings.max_rag_rounds,
            "retrieve_k": settings.retrieve_k,
            "log_level": settings.log_level,
        },
        "dependencies": {
            "elasticsearch": "required",
            "gemini": "required",
        },
    }

    if status != "ok":
        from fastapi import Response
        return Response(
            content=__import__("json").dumps(response),
            status_code=status_code,
            media_type="application/json",
        )

    return response


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest) -> QueryResponse:
    try:
        return await pipeline.run(query=request.query, top_k=request.top_k)
    except Exception as exc:
        logger.exception("Query failed.")
        metrics.record_error(exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/evaluate", response_model=EvaluationResult)
async def evaluate(request: EvaluateRequest) -> EvaluationResult:
    try:
        return await evaluator.evaluate(query=request.query, answer=request.answer, sources=request.sources)
    except Exception as exc:
        logger.exception("Evaluation failed.")
        metrics.record_error(exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/metrics")
async def get_metrics() -> dict:
    snapshot = metrics.snapshot()
    snapshot["runtime"] = {
        "model": settings.gemini_model,
        "embedding_model": settings.gemini_embedding_model,
        "index": settings.elasticsearch_index,
    }
    if elasticsearch_service.configured:
        try:
            snapshot["indexed_chunks"] = await elasticsearch_service.count_chunks()
        except Exception as exc:
            metrics.record_error(exc)
            snapshot["indexed_chunks"] = None
    return snapshot


@app.post("/documents", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)) -> DocumentUploadResponse:
    try:
        doc_id, title, chunks = await index_upload(
            file=file,
            settings=settings,
            gemini=gemini_service,
            elasticsearch=elasticsearch_service,
        )
        metrics.record_documents(documents=1, chunks=chunks)
        return DocumentUploadResponse(
            doc_id=doc_id,
            title=title,
            chunks_indexed=chunks,
            index=settings.elasticsearch_index,
        )
    except Exception as exc:
        logger.exception("Document upload failed.")
        metrics.record_error(exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/documents", response_model=DocumentListResponse)
async def list_documents() -> DocumentListResponse:
    try:
        documents = await elasticsearch_service.list_documents()
        return DocumentListResponse(documents=documents, count=len(documents))
    except Exception as exc:
        logger.exception("Document listing failed.")
        metrics.record_error(exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@app.get("/env-check")
def env_check():
    return {
        "has_url": bool(os.getenv("ELASTICSEARCH_URL")),
        "has_api_key": bool(os.getenv("ELASTICSEARCH_API_KEY")),
        "has_index": bool(os.getenv("ELASTICSEARCH_INDEX")),
        "has_gemini": bool(os.getenv("GEMINI_API_KEY"))
    }