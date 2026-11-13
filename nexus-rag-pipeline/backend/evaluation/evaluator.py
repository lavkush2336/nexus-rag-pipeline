from __future__ import annotations

import re

from backend.schemas import EvaluationResult, SourceDocument
from backend.services.gemini import GeminiService

_CITATION_RE = re.compile(r"\[[^\]]+\]")


class ResponseEvaluator:
    def __init__(self, gemini: GeminiService):
        self._gemini = gemini

    async def evaluate(self, *, query: str, answer: str, sources: list[SourceDocument]) -> EvaluationResult:
        if not sources:
            return EvaluationResult(
                verdict="fail",
                groundedness_score=0,
                completeness_score=0,
                relevance_score=0,
                confidence_score=0,
                missing_topics=["No retrieved source chunks were available."],
                feedback="Index or upload source documents before asking this question.",
            )
        try:
            return await self._gemini.evaluate_response(question=query, answer=answer, sources=sources)
        except Exception:
            return self._fallback_evaluation(answer=answer, sources=sources)

    @staticmethod
    def _fallback_evaluation(*, answer: str, sources: list[SourceDocument]) -> EvaluationResult:
        has_citations = bool(_CITATION_RE.search(answer))
        has_sources = bool(sources)
        confidence = 0.55 if has_citations and has_sources else 0.35
        verdict = "partial" if has_sources else "fail"
        return EvaluationResult(
            verdict=verdict,
            passed=False,
            groundedness_score=0.6 if has_citations else 0.35,
            completeness_score=0.5,
            relevance_score=0.55 if has_sources else 0.2,
            confidence_score=confidence,
            feedback="Gemini evaluation was unavailable, so Nexus returned a conservative local evaluation.",
        )

