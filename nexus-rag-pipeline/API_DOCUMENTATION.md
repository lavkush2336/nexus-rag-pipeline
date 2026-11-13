# Nexus RAG Pipeline - API Documentation

## Overview

Nexus is a closed-loop Retrieval-Augmented Generation (RAG) system that combines:
- **Gemini AI** for text generation and embeddings
- **Elasticsearch** for semantic document retrieval
- **Self-evaluation loop** for iterative quality improvement
- **REST API** for integration with web and desktop applications

This document describes all available API endpoints.

---

## Base URL

```
http://localhost:8000
```

Or deployed on Render:
```
https://your-service.onrender.com
```

---

## Authentication

All endpoints are public. For production deployments, add authentication middleware as needed.

---

## Endpoints

### 1. Service Status

**GET `/`**

Returns the service status and configuration.

**Response:**
```json
{
  "service": "Nexus Closed-Loop RAG Pipeline",
  "status": "ok",
  "ui": "/app",
  "api_docs": "/docs",
  "model": "gemini-3.5-flash",
  "index": "nexus-rag-documents",
  "timestamp": 1718017890.123
}
```

---

### 2. Health Check

**GET `/health`**

Check service health and configuration status.

**Response:**
```json
{
  "status": "ok",
  "checks": {
    "gemini_configured": true,
    "elasticsearch_configured": true,
    "elasticsearch_reachable": true
  },
  "configuration": {
    "gemini_model": "gemini-3.5-flash",
    "gemini_embedding_model": "gemini-embedding-2",
    "elasticsearch_index": "nexus-rag-documents",
    "max_rag_rounds": 3,
    "retrieve_k": 5
  }
}
```

**Status Values:**
- `ok`: All systems operational
- `degraded`: Some services unavailable

---

### 3. Query Pipeline

**POST `/query`**

Execute a complete RAG pipeline: retrieve → generate → evaluate.

**Request:**
```json
{
  "query": "What is the capital of France?",
  "top_k": 5
}
```

**Parameters:**
- `query` (string, required): The question to answer
  - Min length: 1, Max length: 4000
- `top_k` (integer, optional): Number of source chunks to retrieve
  - Min: 1, Max: 20
  - Default: 5 (from settings)

**Response:**
```json
{
  "answer": "The capital of France is Paris [doc_id]. Paris is located in the central part of the country [doc_id].",
  "sources": [
    {
      "doc_id": "abc123",
      "chunk_id": "abc123-1",
      "title": "European Capitals",
      "content": "The capital of France is Paris...",
      "score": 0.9234,
      "source_name": "geography.txt",
      "metadata": {
        "chunk_index": 1,
        "chunk_count": 5
      }
    }
  ],
  "evaluation": {
    "verdict": "pass",
    "passed": true,
    "groundedness_score": 0.95,
    "completeness_score": 0.88,
    "relevance_score": 0.92,
    "confidence_score": 0.92,
    "unsupported_claims": [],
    "missing_topics": [],
    "feedback": "Well-grounded and complete answer.",
    "refined_query": null
  },
  "latency_ms": 2450,
  "retrieval_results": [...],
  "trace": [
    {
      "round": 1,
      "query": "What is the capital of France?",
      "retrieved": 5,
      "verdict": "pass",
      "confidence_score": 0.92,
      "latency_ms": 2450
    }
  ],
  "model": "gemini-3.5-flash"
}
```

**Response Fields:**
- `answer` (string): Generated response grounded in source documents
- `sources` (array): Retrieved source chunks ranked by relevance
- `evaluation` (object): Self-evaluation results
- `latency_ms` (integer): Total pipeline execution time
- `retrieval_results` (array): Raw retrieval results before ranking
- `trace` (array): Log of all pipeline rounds (for debugging and analysis)
- `model` (string): Model used for generation

**Evaluation Verdict:**
- `pass`: Answer is well-grounded and complete
- `partial`: Answer is acceptable but has gaps
- `fail`: Answer lacks grounding or is incomplete

**Error Responses:**
```json
{
  "detail": "Missing GEMINI_API_KEY. Configure it in the environment before using Gemini."
}
```

---

### 4. Standalone Evaluation

**POST `/evaluate`**

Evaluate an answer independently without running the full pipeline.

**Request:**
```json
{
  "query": "What is the capital of France?",
  "answer": "Paris is the capital of France.",
  "sources": [
    {
      "doc_id": "abc123",
      "chunk_id": "abc123-1",
      "title": "European Capitals",
      "content": "The capital of France is Paris...",
      "score": 0.92
    }
  ]
}
```

**Response:**
```json
{
  "verdict": "pass",
  "passed": true,
  "groundedness_score": 0.95,
  "completeness_score": 0.85,
  "relevance_score": 0.90,
  "confidence_score": 0.90,
  "unsupported_claims": [],
  "missing_topics": [],
  "feedback": "Well-grounded answer with appropriate sources.",
  "refined_query": null
}
```

**Fallback Behavior:**

If Gemini is unavailable, the API returns a conservative evaluation based on:
- Presence of citations in the answer
- Number of available sources
- Basic heuristics

```json
{
  "verdict": "partial",
  "passed": false,
  "groundedness_score": 0.6,
  "completeness_score": 0.5,
  "relevance_score": 0.55,
  "confidence_score": 0.55,
  "feedback": "Gemini evaluation was unavailable, so Nexus returned a conservative local evaluation.",
  "unsupported_claims": [],
  "missing_topics": []
}
```

---

### 5. Pipeline Metrics

**GET `/metrics`**

Retrieve aggregated pipeline metrics and performance statistics.

**Response:**
```json
{
  "total_queries": 42,
  "total_documents_indexed": 8,
  "total_chunks_indexed": 243,
  "total_errors": 1,
  "pass_rate": 0.8571,
  "average_latency_ms": 2142.45,
  "average_retrieval_ms": 345.12,
  "average_generation_ms": 1523.89,
  "average_evaluation_ms": 273.44,
  "last_error": "Elasticsearch connection timeout",
  "last_query_at": 1718017850.123,
  "recent_queries": [
    {
      "query": "What is machine learning?",
      "latency_ms": 2100,
      "verdict": "pass",
      "confidence_score": 0.88,
      "source_count": 5,
      "at": 1718017850.123
    }
  ],
  "runtime": {
    "model": "gemini-3.5-flash",
    "embedding_model": "gemini-embedding-2",
    "index": "nexus-rag-documents"
  },
  "indexed_chunks": 243
}
```

**Metrics Definitions:**
- `total_queries`: Cumulative number of queries processed
- `pass_rate`: Ratio of passing evaluations (0.0 to 1.0)
- `average_latency_ms`: Mean execution time for complete pipeline
- `recent_queries`: Last 25 queries (for debugging and analytics)

---

### 6. Document Upload

**POST `/documents`**

Upload a document to the knowledge base. The document is chunked, embedded, and indexed.

**Request:**
- Content-Type: `multipart/form-data`
- File: `file` (binary, required)

**Supported Formats:**
- `.txt` - Plain text
- `.md` - Markdown
- `.pdf` - PDF text extraction
- `.docx` - Word documents

**Response:**
```json
{
  "doc_id": "abc123def456",
  "title": "my-document",
  "chunks_indexed": 42,
  "index": "nexus-rag-documents"
}
```

**Response Fields:**
- `doc_id` (string): Unique document identifier
- `title` (string): Extracted or inferred document title
- `chunks_indexed` (integer): Number of chunks created from the document
- `index` (string): Elasticsearch index where chunks are stored

**Chunking Strategy:**
- Default chunk size: 1600 characters
- Overlap: 200 characters (for context preservation)
- Paragraphs are kept together when possible
- Embedded using `gemini-embedding-2` model

**Error Responses:**
```json
{
  "detail": "Uploaded document did not contain indexable text."
}
```

---

### 7. List Documents

**GET `/documents`**

Retrieve metadata about all indexed documents.

**Response:**
```json
{
  "documents": [
    {
      "doc_id": "abc123",
      "title": "European Geography",
      "source_name": "geography.txt",
      "chunks": 42,
      "created_at": "2024-06-10T12:34:56Z",
      "metadata": {
        "content_type": "text/plain"
      }
    }
  ],
  "count": 1
}
```

**Document Fields:**
- `doc_id` (string): Unique document identifier
- `title` (string): Document title
- `source_name` (string): Original filename
- `chunks` (integer): Number of indexed chunks
- `created_at` (string): ISO 8601 timestamp
- `metadata` (object): Additional metadata

---

### 8. Serve Frontend UI

**GET `/app`**

Serve the web interface.

**Response:**
HTML page containing the Nexus RAG Console UI.

**Access:**
Open browser to `http://localhost:8000/app` or `/app` on deployed service.

---

## Data Types

### SourceDocument

```json
{
  "doc_id": "abc123",
  "chunk_id": "abc123-1",
  "title": "Document Title",
  "content": "Chunk content...",
  "score": 0.9234,
  "source_name": "original-filename.txt",
  "metadata": {
    "chunk_index": 1,
    "chunk_count": 5,
    "content_type": "text/plain"
  }
}
```

### EvaluationResult

```json
{
  "verdict": "pass",
  "passed": true,
  "groundedness_score": 0.95,
  "completeness_score": 0.88,
  "relevance_score": 0.92,
  "confidence_score": 0.92,
  "unsupported_claims": [],
  "missing_topics": [],
  "feedback": "Well-grounded and complete answer.",
  "refined_query": null
}
```

### PipelineTraceStep

```json
{
  "round": 1,
  "query": "Original query",
  "retrieved": 5,
  "verdict": "pass",
  "confidence_score": 0.92,
  "latency_ms": 2450
}
```

---

## Error Handling

All errors return HTTP error status codes with JSON responses.

**Common Error Status Codes:**
- `400 Bad Request`: Invalid request format or parameters
- `500 Internal Server Error`: Server-side error (check `/health` for details)

**Error Response Format:**
```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common Errors:**

1. **Missing Gemini API Key**
```json
{
  "detail": "Missing GEMINI_API_KEY. Configure it in the environment before using Gemini."
}
```

2. **Missing Elasticsearch Configuration**
```json
{
  "detail": "Missing ELASTICSEARCH_URL or ELASTICSEARCH_API_KEY. Configure Elasticsearch before retrieval."
}
```

3. **No Indexed Documents**
```json
{
  "answer": "No indexed source content matched this query. Upload relevant documents or broaden the question.",
  "sources": [],
  "evaluation": { "verdict": "fail", ... }
}
```

---

## Rate Limiting

No rate limiting is enforced by default. For production deployments:
- Add API key authentication
- Implement rate limiting middleware
- Monitor resource usage

---

## Environment Variables

Configure the service using these environment variables:

```bash
# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.5-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-2
GEMINI_TEMPERATURE=0.2
GEMINI_MAX_RETRIES=3
GEMINI_RETRY_BACKOFF_SECONDS=0.8

# Elasticsearch Configuration
ELASTICSEARCH_URL=https://your-cluster.es.region.cloud.es.io:443
ELASTICSEARCH_API_KEY=your_elasticsearch_api_key
ELASTICSEARCH_INDEX=nexus-rag-documents

# RAG Pipeline Configuration
RETRIEVE_K=5
MAX_RAG_ROUNDS=3
REQUEST_TIMEOUT_SECONDS=30
CHUNK_SIZE_CHARS=1600
CHUNK_OVERLAP_CHARS=200

# Application Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO
PORT=8000
CORS_ORIGINS=*
```

---

## Example Usage

### Query Example

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "top_k": 5
  }'
```

### Upload Document Example

```bash
curl -X POST http://localhost:8000/documents \
  -F "file=@my-document.txt"
```

### Get Metrics Example

```bash
curl http://localhost:8000/metrics
```

---

## WebSocket Support

The frontend uses WebSocket connections for real-time updates (optional, not required for REST API usage).

---

## API Documentation UI

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Changelog

### Version 1.0.0
- Initial release with Gemini and Elasticsearch integration
- RAG pipeline with self-evaluation
- Document management endpoints
- Comprehensive metrics tracking
