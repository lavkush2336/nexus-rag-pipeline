# Component Map

## App Shell

- `StatusHeader`: service name, health state, model, index, refresh action.
- `ToastRegion`: transient success/error messages.
- `LoadingOverlay`: scoped loading states for query and upload actions.

## Query Workspace

- `QueryComposer`: question input, top-k control, submit button.
- `AnswerPanel`: generated answer, latency, partial/final status.
- `HistoryToolbar`: download response history and clear local history.

## Evidence Explorer

- `RetrievalList`: ranked source chunks with scores and metadata.
- `SourceDetail`: selected source content, title, doc id, chunk id.
- `FeedbackTimeline`: retrieval/generation/evaluation loop trace.

## Evaluation Dashboard

- `ConfidenceGauge`: confidence percentage and verdict color.
- `ScoreBars`: groundedness, completeness, relevance.
- `IssueList`: unsupported claims and missing topics.
- `EvaluationActions`: rerun evaluation for the current response.

## Pipeline Metrics

- `MetricGrid`: query count, document count, latency, pass rate.
- `LatencyBreakdown`: retrieval, generation, evaluation timing.
- `SystemChecks`: Gemini and Elasticsearch configuration state.

## Document Operations

- `DocumentUploader`: file input and upload progress.
- `DocumentInventory`: indexed document cards with chunk counts and timestamps.
- `RefreshDocumentsButton`: reloads indexed document list.

## API Contracts Used By Components

- `GET /health`: `StatusHeader`, `SystemChecks`.
- `POST /query`: `QueryComposer`, `AnswerPanel`, `RetrievalList`, `EvaluationDashboard`.
- `POST /evaluate`: `EvaluationActions`, `EvaluationDashboard`.
- `GET /metrics`: `MetricGrid`, `LatencyBreakdown`.
- `POST /documents`: `DocumentUploader`.
- `GET /documents`: `DocumentInventory`.

