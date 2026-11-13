# Project Cleanup Report

Generated: 2026-06-10

## Pre-Deletion Audit

| Path | Why It Exists | Currently Used | Depends On It | Decision |
| --- | --- | --- | --- | --- |
| `.env.example` | Environment template for local and hosted deployment. | Yes, but contains OpenAI and legacy Elasticsearch names. | README, deployment setup. | REFRACTOR |
| `.gitignore` | Keeps local env, caches, and secrets out of git. | Yes. | Git workflow. | KEEP |
| `DEPLOYMENT.md` | Render and Docker deployment notes. | Yes, but OpenAI/MCP content is obsolete. | Developer workflow. | REFRACTOR |
| `DEPLOYMENT_REPORT.md` | Historical deployment attempt report. | No. | Nothing imports or runs it. | DELETE |
| `DEPLOYMENT_REPORT_UPDATED.md` | Historical Render API attempt report. | No. | Nothing imports or runs it. | DELETE |
| `Dockerfile` | Container deployment definition. | Yes, but starts old MCP server. | Docker, Render alternatives. | REFRACTOR |
| `LICENSE` | Project license. | Yes. | Repository metadata. | KEEP |
| `Procfile` | Platform start command. | Yes, but starts old MCP server. | Render-like process managers. | REFRACTOR |
| `README.md` | Primary project documentation. | Yes, but describes OpenAI/MCP CLI app. | Users and deployment setup. | REFRACTOR |
| `index.html` | Static OpenAI/MCP configuration mock. | No runtime API integration. | Nothing depends on it after new UI. | DELETE |
| `render.yaml` | Render blueprint. | Yes, but points to old MCP server and OpenAI env. | Render deployment. | REFRACTOR |
| `render_payload*.json` | Temporary Render API request payloads. | No. | Nothing imports or deploys them. | DELETE |
| `render_response*.json` | Temporary Render API response captures. | No. | Nothing imports or deploys them. | DELETE |
| `requirements.txt` | Python dependency manifest. | Yes, but includes OpenAI, MCP, Typer, AnyIO for old CLI. | Docker, local setup, Render. | REFRACTOR |
| `rag_agent/` | Old CLI closed-loop RAG agent. | No for required REST/UI app. | Old CLI only; imports OpenAI and MCP. | DELETE |
| `rag_agent/__pycache__/` | Generated Python bytecode. | No. | Python runtime can regenerate. | DELETE |
| `my-elastic-mcp/` | Old standalone MCP Elasticsearch server. | No for direct REST API architecture. | Old Docker/Procfile/render config only. | DELETE |
| `my-elastic-mcp/ngrok.exe` | Local tunnel binary for exposing MCP SSE. | No, ignored by git and not part of production app. | Nothing in runtime. | DELETE |
| `my-elastic-mcp/__pycache__/` | Generated Python bytecode. | No. | Python runtime can regenerate. | DELETE |
| `.venv/` | Local virtual environment. | Local developer convenience only. | Not source-managed and ignored. | KEEP |

## Dependency Trace Summary

- OpenAI appears in `.env.example`, `README.md`, `DEPLOYMENT.md`, `render.yaml`, `index.html`, `rag_agent/openai_llm.py`, `rag_agent/agent.py`, `rag_agent/cli.py`, and `requirements.txt`.
- MCP appears in the old CLI retriever, old Elasticsearch MCP server, docs, deployment commands, and old UI copy.
- No production file outside those legacy paths requires `rag_agent/` or `my-elastic-mcp/`.
- The new runtime will use `backend.main:app` as the single process entrypoint.

## Planned Files Created

- `backend/`: FastAPI app, Gemini service, Elasticsearch service, retrieval, ingestion, evaluation, metrics, schemas, and config.
- `frontend/`: Enterprise RAG operations UI.
- `API_DOCUMENTATION.md`: REST API reference.
- `UI_ARCHITECTURE.md`, `USER_FLOW.md`, `COMPONENT_MAP.md`: UX planning artifacts.

## Planned Files Deleted

- `DEPLOYMENT_REPORT.md`
- `DEPLOYMENT_REPORT_UPDATED.md`
- `index.html`
- `render_payload.json`
- `render_payload2.json`
- `render_response.json`
- `render_response2.json`
- `rag_agent/`
- `my-elastic-mcp/`

## Planned Dependencies Removed

- `openai`
- `mcp`
- `typer`
- `anyio`

## Planned Dependencies Added

- `fastapi`
- `uvicorn[standard]`
- `google-genai`
- `python-multipart`

## Final Results

This section is updated after implementation and deletion.

