const state = {
  currentResponse: null,
  selectedSourceIndex: 0,
  history: loadHistory(),
  health: null,
};

const els = {
  healthPill: document.getElementById("healthPill"),
  healthText: document.getElementById("healthText"),
  modelText: document.getElementById("modelText"),
  indexText: document.getElementById("indexText"),
  refreshButton: document.getElementById("refreshButton"),
  queryForm: document.getElementById("queryForm"),
  queryInput: document.getElementById("queryInput"),
  topKInput: document.getElementById("topKInput"),
  queryButton: document.getElementById("queryButton"),
  runState: document.getElementById("runState"),
  latencyText: document.getElementById("latencyText"),
  answerText: document.getElementById("answerText"),
  sourcesList: document.getElementById("sourcesList"),
  sourceCount: document.getElementById("sourceCount"),
  sourceDetail: document.getElementById("sourceDetail"),
  traceList: document.getElementById("traceList"),
  confidenceRing: document.getElementById("confidenceRing"),
  verdictText: document.getElementById("verdictText"),
  feedbackText: document.getElementById("feedbackText"),
  scoreStack: document.getElementById("scoreStack"),
  missingTopics: document.getElementById("missingTopics"),
  unsupportedClaims: document.getElementById("unsupportedClaims"),
  evaluateButton: document.getElementById("evaluateButton"),
  metricGrid: document.getElementById("metricGrid"),
  uploadForm: document.getElementById("uploadForm"),
  documentInput: document.getElementById("documentInput"),
  uploadButton: document.getElementById("uploadButton"),
  documentsList: document.getElementById("documentsList"),
  documentsRefreshButton: document.getElementById("documentsRefreshButton"),
  downloadHistoryButton: document.getElementById("downloadHistoryButton"),
  clearHistoryButton: document.getElementById("clearHistoryButton"),
  historyList: document.getElementById("historyList"),
  toast: document.getElementById("toast"),
};

function loadHistory() {
  try {
    return JSON.parse(localStorage.getItem("nexus_response_history") || "[]");
  } catch {
    return [];
  }
}

function saveHistory() {
  localStorage.setItem("nexus_response_history", JSON.stringify(state.history.slice(0, 25)));
}

async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: options.body instanceof FormData ? undefined : { "Content-Type": "application/json" },
    ...options,
  });
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) {
    const message = typeof payload === "string" ? payload : payload.detail || "Request failed.";
    throw new Error(message);
  }
  return payload;
}

function setLoading(target, isLoading) {
  target.classList.toggle("is-loading", isLoading);
}

function showToast(message) {
  els.toast.textContent = message;
  els.toast.classList.add("show");
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => els.toast.classList.remove("show"), 2800);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function formatNumber(value, digits = 0) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "-";
  }
  return Number(value).toFixed(digits);
}

function percent(value) {
  return `${Math.round((Number(value) || 0) * 100)}%`;
}

async function loadHealth() {
  const health = await request("/health");
  state.health = health;
  const dot = els.healthPill.querySelector(".dot");
  dot.className = `dot ${health.status === "ok" ? "dot-ok" : "dot-warn"}`;
  els.healthText.textContent = health.status;
  els.modelText.textContent = health.configuration?.gemini_model || "-";
  els.indexText.textContent = health.configuration?.elasticsearch_index || "-";
}

async function loadMetrics() {
  const metrics = await request("/metrics");
  renderMetrics(metrics);
}

async function loadDocuments() {
  try {
    const payload = await request("/documents");
    renderDocuments(payload.documents || []);
  } catch (error) {
    renderDocuments([]);
    showToast(error.message);
  }
}

function renderMetrics(metrics) {
  const cards = [
    ["Queries", metrics.total_queries],
    ["Avg latency", `${formatNumber(metrics.average_latency_ms)} ms`],
    ["Pass rate", percent(metrics.pass_rate)],
    ["Indexed chunks", metrics.indexed_chunks ?? metrics.total_chunks_indexed],
    ["Errors", metrics.total_errors],
    ["Retrieval avg", `${formatNumber(metrics.average_retrieval_ms)} ms`],
  ];
  els.metricGrid.innerHTML = cards
    .map(
      ([label, value]) => `
        <div class="metric-card">
          <div class="metric-label">${escapeHtml(label)}</div>
          <div class="metric-value">${escapeHtml(value)}</div>
        </div>
      `,
    )
    .join("");
}

function renderResponse(response) {
  state.currentResponse = response;
  state.selectedSourceIndex = 0;
  els.answerText.classList.remove("empty-state");
  els.answerText.textContent = response.answer || "No answer returned.";
  els.latencyText.textContent = `${response.latency_ms || 0} ms`;
  renderSources(response.sources || []);
  renderEvaluation(response.evaluation || {});
  renderTrace(response.trace || []);
}

function renderSources(sources) {
  els.sourceCount.textContent = String(sources.length);
  if (!sources.length) {
    els.sourcesList.className = "source-list empty-state";
    els.sourcesList.textContent = "No retrieved chunks.";
    renderSourceDetail(null);
    return;
  }
  els.sourcesList.className = "source-list";
  els.sourcesList.innerHTML = sources
    .map(
      (source, index) => `
        <button class="source-card ${index === state.selectedSourceIndex ? "active" : ""}" data-source-index="${index}" type="button">
          <div class="card-title">${escapeHtml(source.title)}</div>
          <div class="card-meta">
            <span>${escapeHtml(source.doc_id)}</span>
            <span>${escapeHtml(source.chunk_id)}</span>
            <span>score ${formatNumber(source.score, 3)}</span>
          </div>
          <div class="snippet">${escapeHtml(source.content)}</div>
        </button>
      `,
    )
    .join("");
  els.sourcesList.querySelectorAll("[data-source-index]").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedSourceIndex = Number(button.dataset.sourceIndex);
      renderSources(state.currentResponse.sources || []);
    });
  });
  renderSourceDetail(sources[state.selectedSourceIndex]);
}

function renderSourceDetail(source) {
  if (!source) {
    els.sourceDetail.className = "source-detail empty-state";
    els.sourceDetail.textContent = "Select a retrieved chunk.";
    return;
  }
  els.sourceDetail.className = "source-detail";
  els.sourceDetail.innerHTML = `
    <h3>${escapeHtml(source.title)}</h3>
    <div class="card-meta">
      <span>Doc ${escapeHtml(source.doc_id)}</span>
      <span>Chunk ${escapeHtml(source.chunk_id)}</span>
      <span>Score ${formatNumber(source.score, 4)}</span>
    </div>
    <p>${escapeHtml(source.content)}</p>
  `;
}

function renderEvaluation(evaluation) {
  const confidence = Number(evaluation.confidence_score || 0);
  const degrees = Math.max(0, Math.min(1, confidence)) * 360;
  els.confidenceRing.textContent = percent(confidence);
  els.confidenceRing.style.background = `conic-gradient(var(--cyan) ${degrees}deg, rgba(34, 211, 238, 0.14) ${degrees}deg), rgba(8, 13, 18, 0.92)`;
  els.verdictText.textContent = evaluation.verdict || "No verdict";
  els.feedbackText.textContent = evaluation.feedback || "No evaluation feedback.";

  const scores = [
    ["Grounded", evaluation.groundedness_score],
    ["Complete", evaluation.completeness_score],
    ["Relevant", evaluation.relevance_score],
  ];
  els.scoreStack.innerHTML = scores
    .map(
      ([label, value]) => `
        <div class="score-row">
          <span>${escapeHtml(label)}</span>
          <div class="score-track"><div class="score-fill" style="width:${percent(value)}"></div></div>
          <strong>${percent(value)}</strong>
        </div>
      `,
    )
    .join("");

  renderList(els.missingTopics, evaluation.missing_topics || [], "None");
  renderList(els.unsupportedClaims, evaluation.unsupported_claims || [], "None");
}

function renderList(target, items, emptyText) {
  target.innerHTML = items.length
    ? items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")
    : `<li>${escapeHtml(emptyText)}</li>`;
}

function renderTrace(trace) {
  if (!trace.length) {
    els.traceList.className = "trace-list empty-state";
    els.traceList.textContent = "No pipeline trace.";
    return;
  }
  els.traceList.className = "trace-list";
  els.traceList.innerHTML = trace
    .map(
      (step) => `
        <div class="trace-card">
          <div class="card-title">Round ${step.round}: ${escapeHtml(step.verdict)}</div>
          <div class="card-meta">
            <span>${step.retrieved} chunks</span>
            <span>${percent(step.confidence_score)} confidence</span>
            <span>${step.latency_ms} ms</span>
          </div>
          <div class="snippet">${escapeHtml(step.query)}</div>
        </div>
      `,
    )
    .join("");
}

function renderDocuments(documents) {
  if (!documents.length) {
    els.documentsList.className = "documents-list empty-state";
    els.documentsList.textContent = "No indexed documents loaded.";
    return;
  }
  els.documentsList.className = "documents-list";
  els.documentsList.innerHTML = documents
    .map(
      (document) => `
        <div class="document-card">
          <div class="card-title">${escapeHtml(document.title)}</div>
          <div class="card-meta">
            <span>${escapeHtml(document.doc_id)}</span>
            <span>${document.chunks} chunks</span>
          </div>
          <div class="snippet">${escapeHtml(document.source_name || "Uploaded source")}</div>
        </div>
      `,
    )
    .join("");
}

function renderHistory() {
  if (!state.history.length) {
    els.historyList.className = "history-list empty-state";
    els.historyList.textContent = "No saved responses.";
    return;
  }
  els.historyList.className = "history-list";
  els.historyList.innerHTML = state.history
    .slice(0, 5)
    .map(
      (entry) => `
        <div class="history-card">
          <div class="card-title">${escapeHtml(entry.query)}</div>
          <div class="card-meta">
            <span>${escapeHtml(entry.verdict)}</span>
            <span>${entry.latency_ms} ms</span>
            <span>${new Date(entry.at).toLocaleString()}</span>
          </div>
        </div>
      `,
    )
    .join("");
}

async function runQuery(event) {
  event.preventDefault();
  const query = els.queryInput.value.trim();
  if (!query) {
    return;
  }
  els.queryButton.disabled = true;
  els.runState.textContent = "Running";
  setLoading(document.querySelector(".query-panel"), true);
  try {
    const response = await request("/query", {
      method: "POST",
      body: JSON.stringify({
        query,
        top_k: Number(els.topKInput.value || 5),
      }),
    });
    renderResponse(response);
    state.history.unshift({
      query,
      answer: response.answer,
      verdict: response.evaluation?.verdict || "unknown",
      confidence_score: response.evaluation?.confidence_score || 0,
      latency_ms: response.latency_ms,
      sources: response.sources,
      evaluation: response.evaluation,
      at: new Date().toISOString(),
    });
    saveHistory();
    renderHistory();
    await loadMetrics();
  } catch (error) {
    showToast(error.message);
  } finally {
    els.queryButton.disabled = false;
    els.runState.textContent = "Idle";
    setLoading(document.querySelector(".query-panel"), false);
  }
}

async function evaluateCurrent() {
  if (!state.currentResponse) {
    showToast("Run a query first.");
    return;
  }
  try {
    const evaluation = await request("/evaluate", {
      method: "POST",
      body: JSON.stringify({
        query: els.queryInput.value.trim(),
        answer: state.currentResponse.answer,
        sources: state.currentResponse.sources || [],
      }),
    });
    state.currentResponse.evaluation = evaluation;
    renderEvaluation(evaluation);
  } catch (error) {
    showToast(error.message);
  }
}

async function uploadDocument(event) {
  event.preventDefault();
  const file = els.documentInput.files[0];
  if (!file) {
    showToast("Select a document.");
    return;
  }
  const formData = new FormData();
  formData.append("file", file);
  els.uploadButton.disabled = true;
  setLoading(document.querySelector(".documents-panel"), true);
  try {
    const result = await request("/documents", { method: "POST", body: formData });
    showToast(`Indexed ${result.chunks_indexed} chunks.`);
    els.documentInput.value = "";
    await loadDocuments();
    await loadMetrics();
  } catch (error) {
    showToast(error.message);
  } finally {
    els.uploadButton.disabled = false;
    setLoading(document.querySelector(".documents-panel"), false);
  }
}

function downloadHistory() {
  const blob = new Blob([JSON.stringify(state.history, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `nexus-response-history-${new Date().toISOString().slice(0, 10)}.json`;
  anchor.click();
  URL.revokeObjectURL(url);
}

async function refreshAll() {
  try {
    await Promise.all([loadHealth(), loadMetrics(), loadDocuments()]);
  } catch (error) {
    const dot = els.healthPill.querySelector(".dot");
    dot.className = "dot dot-bad";
    els.healthText.textContent = "offline";
    showToast(error.message);
  }
}

els.queryForm.addEventListener("submit", runQuery);
els.uploadForm.addEventListener("submit", uploadDocument);
els.evaluateButton.addEventListener("click", evaluateCurrent);
els.refreshButton.addEventListener("click", refreshAll);
els.documentsRefreshButton.addEventListener("click", loadDocuments);
els.downloadHistoryButton.addEventListener("click", downloadHistory);
els.clearHistoryButton.addEventListener("click", () => {
  state.history = [];
  saveHistory();
  renderHistory();
});

renderEvaluation({});
renderHistory();
refreshAll();

