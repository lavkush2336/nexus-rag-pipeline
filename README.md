# Nexus Closed-Loop RAG Pipeline

Nexus is a production-ready **Retrieval-Augmented Generation (RAG)** system powered by Google Gemini and Elasticsearch. It combines semantic document retrieval with iterative self-evaluation to produce grounded, high-confidence answers.

## Features

- ✨ **Google Gemini Integration** - State-of-the-art text generation and embeddings
- 🔍 **Elasticsearch Retrieval** - Hybrid semantic + lexical search over indexed documents
- 🔄 **Closed-Loop Feedback** - Automatic evaluation and query refinement (up to 3 rounds)
- 📊 **Self-Evaluation** - Confidence scoring, groundedness checking, completeness analysis
- 🚀 **REST API** - Complete HTTP endpoints for integration
- 💻 **Enterprise UI** - Dark theme console with real-time metrics and history
- 🐳 **Docker Ready** - Single-command deployment
- 📈 **Metrics Tracking** - Query analytics, latency breakdown, pass rates

## Tech Stack

- **Language:** Python 3.12
- **Framework:** FastAPI (REST API + async)
- **AI Model:** Google Gemini (generation + embeddings)
- **Retrieval:** Elasticsearch 9.x
- **Frontend:** Vanilla JavaScript + CSS (no frameworks)
- **Deployment:** Docker, Render, or standalone

## Quick Start

### Prerequisites

- Python 3.11+
- Elasticsearch cluster (cloud or local)
- Google Gemini API key

### 1. Clone and Setup

```bash
# Clone repository
git clone https://github.com/yourusername/nexus-rag-pipeline.git
cd nexus-rag-pipeline

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
GEMINI_API_KEY=your_gemini_api_key
ELASTICSEARCH_URL=https://your-cluster.es.region.cloud.es.io:443
ELASTICSEARCH_API_KEY=your_elasticsearch_api_key
ELASTICSEARCH_INDEX=nexus-rag-documents
```

### 3. Run Locally

```bash
# Start the API server
uvicorn backend.main:app --reload --port 8000
```

Open browser to `http://localhost:8000/app`

### 4. Upload Documents

Use the UI to upload `.txt`, `.md`, `.pdf`, or `.docx` files. Documents are automatically:
- Chunked into overlapping segments
- Embedded using Gemini embeddings
- Indexed in Elasticsearch

### 5. Ask Questions

Type a question in the query panel. The system will:
1. Search Elasticsearch for relevant chunks
2. Generate an answer grounded in sources
3. Evaluate the answer for quality
4. Refine retrieval if needed (up to 3 rounds)

## API Endpoints

All endpoints return JSON. See `API_DOCUMENTATION.md` for complete details.

### Public Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Service status |
| GET | `/health` | Health check |
| GET | `/app` | Serve frontend UI |
| POST | `/query` | Run RAG pipeline |
| POST | `/evaluate` | Evaluate response |
| GET | `/metrics` | Pipeline metrics |
| POST | `/documents` | Upload document |
| GET | `/documents` | List documents |

### Example: Query

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?", "top_k": 5}'
```

Response:
```json
{
  "answer": "Machine learning is a subset of artificial intelligence...",
  "sources": [
    {
      "doc_id": "abc123",
      "chunk_id": "abc123-1",
      "title": "AI Fundamentals",
      "content": "...",
      "score": 0.95
    }
  ],
  "evaluation": {
    "verdict": "pass",
    "confidence_score": 0.92,
    "groundedness_score": 0.95,
    "completeness_score": 0.88
  },
  "latency_ms": 2145,
  "trace": [...]
}
```

## Environment Variables

### Required

```env
GEMINI_API_KEY              # Google Gemini API key
ELASTICSEARCH_URL           # Elasticsearch cluster URL
ELASTICSEARCH_API_KEY       # Elasticsearch API key
```

### Optional

```env
GEMINI_MODEL=gemini-3.5-flash              # Model for generation
GEMINI_EMBEDDING_MODEL=gemini-embedding-2   # Model for embeddings
GEMINI_TEMPERATURE=0.2                      # Generation temperature (0-2)
ELASTICSEARCH_INDEX=nexus-rag-documents     # Index name
RETRIEVE_K=5                                # Number of chunks to retrieve
MAX_RAG_ROUNDS=3                            # Max refinement rounds
CHUNK_SIZE_CHARS=1600                       # Character size per chunk
CHUNK_OVERLAP_CHARS=200                     # Overlap between chunks
PORT=8000                                   # Server port
LOG_LEVEL=INFO                              # Logging level
CORS_ORIGINS=*                              # CORS origins
```

## Deployment

### Docker

Build and run with Docker:

```bash
docker build -t nexus-rag:latest .
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=your_key \
  -e ELASTICSEARCH_URL=https://your-cluster.es.region.cloud.es.io:443 \
  -e ELASTICSEARCH_API_KEY=your_api_key \
  nexus-rag:latest
```

### Render

Deploy to Render using `render.yaml`:

```bash
# Push to GitHub
git push origin main

# Connect to Render and deploy
# Render will auto-detect render.yaml and deploy
```

Configure environment variables in Render dashboard:
- `GEMINI_API_KEY`
- `ELASTICSEARCH_URL`
- `ELASTICSEARCH_API_KEY`

### Standalone

Run directly with uvicorn:

```bash
export GEMINI_API_KEY=your_key
export ELASTICSEARCH_URL=https://...
export ELASTICSEARCH_API_KEY=your_api_key

uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Nexus RAG Pipeline                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  FastAPI REST API                                        │
│  ├─ /query        → RAG Pipeline                         │
│  ├─ /evaluate     → Self-Evaluation Engine               │
│  ├─ /documents    → Document Management                  │
│  └─ /metrics      → Analytics & Tracking                 │
│                                                          │
├─────────────────────────────────────────────────────────┤
│  Query Workflow:                                         │
│                                                          │
│  1. RETRIEVE    → Elasticsearch (hybrid search)          │
│  2. GENERATE    → Gemini (grounded answer)              │
│  3. EVALUATE    → Gemini (self-evaluation)              │
│  4. [REFINE]    → Loop up to 3 rounds if needed         │
│                                                          │
├─────────────────────────────────────────────────────────┤
│  External Services:                                      │
│                                                          │
│  • Google Gemini  → Generation + Embeddings             │
│  • Elasticsearch  → Vector + Lexical Search             │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Project Structure

```
nexus-rag-pipeline/
├── backend/
│   ├── main.py                      # FastAPI app & routes
│   ├── config.py                    # Settings management
│   ├── schemas.py                   # Request/response models
│   ├── metrics.py                   # Metrics collection
│   ├── services/
│   │   ├── gemini.py               # Gemini client
│   │   └── elasticsearch_client.py  # ES client
│   ├── retrieval/
│   │   ├── retriever.py            # Retrieval orchestration
│   │   └── ranker.py               # Context ranking
│   ├── pipeline/
│   │   └── rag_pipeline.py         # RAG orchestration
│   ├── evaluation/
│   │   └── evaluator.py            # Self-evaluation logic
│   ├── ingestion/
│   │   └── documents.py            # Document processing
│   └── logging_config.py            # Logging setup
├── frontend/
│   ├── index.html                   # UI skeleton
│   ├── app.js                       # JavaScript logic
│   └── styles.css                   # Styling
├── requirements.txt                 # Python dependencies
├── Dockerfile                       # Docker configuration
├── Procfile                         # Render configuration
├── render.yaml                      # Render blueprint
├── .env.example                     # Environment template
├── API_DOCUMENTATION.md             # API reference
├── UI_ARCHITECTURE.md               # UI design
├── USER_FLOW.md                     # User journeys
├── COMPONENT_MAP.md                 # Component structure
└── README.md                        # This file
```

## Performance

Typical latencies on Render free tier:

- **Retrieval:** 150-400ms
- **Generation:** 800-2000ms
- **Evaluation:** 200-600ms
- **Total (pass on round 1):** 1.5-3 seconds

Performance improves with:
- Paid Elasticsearch tier
- Render paid tier
- Optimized document indexing
- Query caching

## Troubleshooting

### "Missing GEMINI_API_KEY"
- Ensure `GEMINI_API_KEY` is set in `.env` or environment
- Verify the key is valid at https://ai.google.dev

### "Elasticsearch connection failed"
- Verify `ELASTICSEARCH_URL` and `ELASTICSEARCH_API_KEY`
- Check Elasticsearch cluster is running
- Confirm IP whitelist allows your IP

### "No retrieved chunks"
- Upload documents first using the UI
- Check Elasticsearch index exists: `GET /health`
- Verify documents were indexed: `GET /documents`

### UI not loading
- Verify frontend files in `frontend/` directory
- Check `STATIC_DIR` environment variable
- Open browser console for errors (F12)

## Development

### Add a new endpoint

1. Create handler in `backend/main.py`
2. Define request/response schemas in `backend/schemas.py`
3. Add business logic in appropriate service module
4. Document in `API_DOCUMENTATION.md`

### Modify RAG pipeline

Edit `backend/pipeline/rag_pipeline.py`:
- Change max rounds in `settings.max_rag_rounds`
- Modify retrieval count in `settings.retrieve_k`
- Adjust temperature in `settings.gemini_temperature`

### Update UI

Frontend files are served from `frontend/`:
- `index.html` - Structure
- `app.js` - JavaScript logic
- `styles.css` - Styling

Changes are hot-reloaded in development.

## Testing

Run manual tests:

```bash
# Test service status
curl http://localhost:8000/

# Test health check
curl http://localhost:8000/health

# Test query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Test query"}'
```

## Production Checklist

- [ ] Set `ENVIRONMENT=production` in deployment
- [ ] Configure strong `CORS_ORIGINS` (not `*`)
- [ ] Add authentication middleware if needed
- [ ] Enable HTTPS/TLS
- [ ] Set up monitoring and logging
- [ ] Configure backup for Elasticsearch
- [ ] Test disaster recovery
- [ ] Document API contracts
- [ ] Set up CI/CD pipeline

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Commit changes with clear messages
4. Submit a pull request

## License

MIT License - see LICENSE file

## Support

- 📖 [Full API Documentation](API_DOCUMENTATION.md)
- 🎨 [UI Architecture Guide](UI_ARCHITECTURE.md)
- 🔄 [User Flows](USER_FLOW.md)
- 📋 [Component Map](COMPONENT_MAP.md)

## Roadmap

- [ ] Multi-language support
- [ ] Vector database alternatives (Pinecone, Weaviate)
- [ ] LLM alternatives (Claude, OpenAI)
- [ ] Advanced caching layer
- [ ] Web crawler for auto-indexing
- [ ] Streaming responses
- [ ] User authentication and multi-tenancy
- [ ] Advanced analytics dashboard

---

**Built with ❤️ for the Gemini AI community**
