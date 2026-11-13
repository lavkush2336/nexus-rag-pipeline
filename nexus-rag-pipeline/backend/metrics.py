from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from time import time
from typing import Any


@dataclass
class MetricsStore:
    total_queries: int = 0
    total_documents_indexed: int = 0
    total_chunks_indexed: int = 0
    total_errors: int = 0
    passed_evaluations: int = 0
    total_evaluations: int = 0
    latency_ms_total: int = 0
    retrieval_ms_total: int = 0
    generation_ms_total: int = 0
    evaluation_ms_total: int = 0
    last_error: str | None = None
    last_query_at: float | None = None
    recent_queries: deque[dict[str, Any]] = field(default_factory=lambda: deque(maxlen=25))

    def record_query(
        self,
        *,
        query: str,
        latency_ms: int,
        retrieval_ms: int,
        generation_ms: int,
        evaluation_ms: int,
        verdict: str,
        confidence_score: float,
        source_count: int,
    ) -> None:
        self.total_queries += 1
        self.total_evaluations += 1
        self.latency_ms_total += latency_ms
        self.retrieval_ms_total += retrieval_ms
        self.generation_ms_total += generation_ms
        self.evaluation_ms_total += evaluation_ms
        self.last_query_at = time()
        if verdict == "pass":
            self.passed_evaluations += 1
        self.recent_queries.appendleft(
            {
                "query": query,
                "latency_ms": latency_ms,
                "verdict": verdict,
                "confidence_score": confidence_score,
                "source_count": source_count,
                "at": self.last_query_at,
            }
        )

    def record_documents(self, *, documents: int, chunks: int) -> None:
        self.total_documents_indexed += documents
        self.total_chunks_indexed += chunks

    def record_error(self, error: Exception | str) -> None:
        self.total_errors += 1
        self.last_error = str(error)

    def snapshot(self) -> dict[str, Any]:
        avg_latency = self.latency_ms_total / self.total_queries if self.total_queries else 0
        avg_retrieval = self.retrieval_ms_total / self.total_queries if self.total_queries else 0
        avg_generation = self.generation_ms_total / self.total_queries if self.total_queries else 0
        avg_evaluation = self.evaluation_ms_total / self.total_queries if self.total_queries else 0
        pass_rate = self.passed_evaluations / self.total_evaluations if self.total_evaluations else 0
        return {
            "total_queries": self.total_queries,
            "total_documents_indexed": self.total_documents_indexed,
            "total_chunks_indexed": self.total_chunks_indexed,
            "total_errors": self.total_errors,
            "pass_rate": round(pass_rate, 4),
            "average_latency_ms": round(avg_latency, 2),
            "average_retrieval_ms": round(avg_retrieval, 2),
            "average_generation_ms": round(avg_generation, 2),
            "average_evaluation_ms": round(avg_evaluation, 2),
            "last_error": self.last_error,
            "last_query_at": self.last_query_at,
            "recent_queries": list(self.recent_queries),
        }

