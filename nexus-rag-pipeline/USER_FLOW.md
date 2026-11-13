# User Flow

## Journey 1: Ask A Grounded Question

1. User opens `/app`.
2. UI loads `/health`, `/metrics`, and `/documents`.
3. User enters a question in the query workspace.
4. UI calls `POST /query`.
5. Backend retrieves chunks from Elasticsearch, ranks context, generates a Gemini answer, evaluates it, and may refine retrieval.
6. UI displays answer, retrieved chunks, source detail, evaluation verdict, confidence, trace, and latency.
7. User downloads response history if needed.

## Journey 2: Inspect Retrieval Quality

1. User runs a query.
2. UI highlights ranked source chunks.
3. User selects a chunk.
4. Source panel displays title, chunk id, score, metadata, and content.
5. User compares retrieved evidence with the generated answer and evaluation output.

## Journey 3: Upload Knowledge

1. User opens the document panel.
2. User selects a text-like file.
3. UI calls `POST /documents`.
4. Backend chunks content, generates Gemini embeddings, ensures the Elasticsearch index exists, and indexes each chunk.
5. UI refreshes `GET /documents` and updates document metrics.

## Journey 4: Evaluate A Response

1. User keeps or edits a generated answer.
2. UI calls `POST /evaluate` with the query, answer, and visible sources.
3. Backend uses Gemini structured output for groundedness, completeness, relevance, and confidence.
4. UI updates the self-evaluation panel.

## Journey 5: Monitor Pipeline Health

1. UI periodically loads `/metrics` and `/health`.
2. User sees query volume, average latency, evaluation pass rate, source usage, document count, and last error.
3. Degraded health is shown as a clear operational state, not a silent UI failure.

## Error States

- Missing Gemini key: query and upload actions surface a configuration error.
- Missing Elasticsearch settings: retrieval and indexing show a connection error.
- Empty index: query response explains that no indexed source content was found.
- Upload failure: document panel shows the backend error and keeps previous document list.
- Evaluation failure: UI shows fallback evaluation fields returned by the API.

