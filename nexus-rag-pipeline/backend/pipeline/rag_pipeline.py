from __future__ import annotations

from time import perf_counter

from backend.config import Settings
from backend.evaluation.evaluator import ResponseEvaluator
from backend.metrics import MetricsStore
from backend.retrieval.retriever import ElasticsearchRetriever
from backend.schemas import EvaluationResult, PipelineTraceStep, QueryResponse, SourceDocument
from backend.services.gemini import GeminiService


class RagPipeline:
    def __init__(
        self,
        *,
        settings: Settings,
        retriever: ElasticsearchRetriever,
        gemini: GeminiService,
        evaluator: ResponseEvaluator,
        metrics: MetricsStore,
    ):
        self._settings = settings
        self._retriever = retriever
        self._gemini = gemini
        self._evaluator = evaluator
        self._metrics = metrics

    async def run(self, *, query: str, top_k: int | None = None) -> QueryResponse:
        started = perf_counter()
        active_query = query.strip()
        limit = top_k or self._settings.retrieve_k
        feedback: str | None = None
        answer = ""
        sources: list[SourceDocument] = []
        evaluation = EvaluationResult()
        trace: list[PipelineTraceStep] = []
        retrieval_ms_total = 0
        generation_ms_total = 0
        evaluation_ms_total = 0

        for round_number in range(1, self._settings.max_rag_rounds + 1):
            round_started = perf_counter()

            retrieval_started = perf_counter()
            sources = await self._retriever.retrieve(query=active_query, top_k=limit)
            retrieval_ms_total += _elapsed_ms(retrieval_started)

            if not sources:
                answer = "No indexed source content matched this query. Upload relevant documents or broaden the question."
                evaluation = await self._evaluator.evaluate(query=query, answer=answer, sources=sources)
                trace.append(
                    PipelineTraceStep(
                        round=round_number,
                        query=active_query,
                        retrieved=0,
                        verdict=evaluation.verdict,
                        confidence_score=evaluation.confidence_score,
                        latency_ms=_elapsed_ms(round_started),
                    )
                )
                break

            generation_started = perf_counter()
            answer = await self._gemini.generate_answer(question=query, sources=sources, feedback=feedback)
            generation_ms_total += _elapsed_ms(generation_started)

            evaluation_started = perf_counter()
            evaluation = await self._evaluator.evaluate(query=query, answer=answer, sources=sources)
            evaluation_ms_total += _elapsed_ms(evaluation_started)

            trace.append(
                PipelineTraceStep(
                    round=round_number,
                    query=active_query,
                    retrieved=len(sources),
                    verdict=evaluation.verdict,
                    confidence_score=evaluation.confidence_score,
                    latency_ms=_elapsed_ms(round_started),
                )
            )

            if evaluation.verdict == "pass":
                break
            if not evaluation.refined_query or round_number >= self._settings.max_rag_rounds:
                if evaluation.feedback:
                    answer = await self._gemini.rewrite_grounded(
                        question=query,
                        answer=answer,
                        sources=sources,
                        feedback=evaluation.feedback,
                    )
                break
            active_query = evaluation.refined_query.strip()
            feedback = evaluation.feedback

        latency_ms = _elapsed_ms(started)
        self._metrics.record_query(
            query=query,
            latency_ms=latency_ms,
            retrieval_ms=retrieval_ms_total,
            generation_ms=generation_ms_total,
            evaluation_ms=evaluation_ms_total,
            verdict=evaluation.verdict,
            confidence_score=evaluation.confidence_score,
            source_count=len(sources),
        )
        return QueryResponse(
            answer=answer,
            sources=sources,
            retrieval_results=sources,
            evaluation=evaluation,
            latency_ms=latency_ms,
            trace=trace,
            model=self._settings.gemini_model,
        )


def _elapsed_ms(started: float) -> int:
    return int((perf_counter() - started) * 1000)

