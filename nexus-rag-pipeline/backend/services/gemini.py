from __future__ import annotations

import asyncio
import json
import logging
import random
from collections.abc import Callable
from typing import Any, TypeVar

from google import genai

from backend.config import Settings
from backend.schemas import EvaluationResult, SourceDocument

logger = logging.getLogger(__name__)
T = TypeVar("T")


class GeminiService:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._client = genai.Client(api_key=settings.gemini_api_key) if settings.gemini_configured else None

    @property
    def configured(self) -> bool:
        return self._client is not None

    def _require_client(self):
        if self._client is None:
            raise RuntimeError("Missing GEMINI_API_KEY. Configure it in the environment before using Gemini.")
        return self._client

    async def _with_retries(self, label: str, call: Callable[[], T]) -> T:
        last_error: Exception | None = None
        for attempt in range(1, self._settings.gemini_max_retries + 1):
            try:
                return await asyncio.to_thread(call)
            except Exception as exc:
                last_error = exc
                if attempt >= self._settings.gemini_max_retries:
                    break
                delay = self._settings.gemini_retry_backoff_seconds * (2 ** (attempt - 1))
                delay += random.uniform(0, 0.25)
                logger.warning("Gemini %s failed on attempt %s: %s", label, attempt, exc)
                await asyncio.sleep(delay)
        raise RuntimeError(f"Gemini {label} failed after retries: {last_error}") from last_error

    async def generate_answer(
        self,
        *,
        question: str,
        sources: list[SourceDocument],
        feedback: str | None = None,
    ) -> str:
        client = self._require_client()
        prompt = self._answer_prompt(question=question, sources=sources, feedback=feedback)

        def call():
            return client.models.generate_content(
                model=self._settings.gemini_model,
                contents=prompt,
                config={"temperature": self._settings.gemini_temperature},
            )

        response = await self._with_retries("generation", call)
        return (getattr(response, "text", "") or "").strip()

    async def rewrite_grounded(
        self,
        *,
        question: str,
        answer: str,
        sources: list[SourceDocument],
        feedback: str,
    ) -> str:
        client = self._require_client()
        prompt = (
            "Rewrite the answer so every factual claim is supported by the supplied sources. "
            "Keep citations in [doc_id] form. If the sources are insufficient, say what is missing.\n\n"
            f"Question:\n{question}\n\n"
            f"Evaluation feedback:\n{feedback}\n\n"
            f"Sources:\n{self._format_sources(sources)}\n\n"
            f"Draft answer:\n{answer}\n"
        )

        def call():
            return client.models.generate_content(
                model=self._settings.gemini_model,
                contents=prompt,
                config={"temperature": 0},
            )

        response = await self._with_retries("grounded rewrite", call)
        return (getattr(response, "text", "") or "").strip()

    async def evaluate_response(
        self,
        *,
        question: str,
        answer: str,
        sources: list[SourceDocument],
    ) -> EvaluationResult:
        client = self._require_client()
        model = self._settings.gemini_evaluation_model or self._settings.gemini_model
        prompt = self._evaluation_prompt(question=question, answer=answer, sources=sources)
        schema = EvaluationResult.model_json_schema()

        def structured_call():
            return client.models.generate_content(
                model=model,
                contents=prompt,
                config={
                    "temperature": 0,
                    "response_format": {
                        "text": {
                            "mime_type": "application/json",
                            "schema": schema,
                        }
                    },
                },
            )

        try:
            response = await self._with_retries("structured evaluation", structured_call)
        except Exception:
            logger.warning("Structured Gemini evaluation failed; retrying with JSON-only prompt.", exc_info=True)

            def json_call():
                return client.models.generate_content(
                    model=model,
                    contents=prompt + "\nReturn JSON only.",
                    config={"temperature": 0},
                )

            response = await self._with_retries("evaluation", json_call)

        data = _safe_json_loads((getattr(response, "text", "") or "").strip())
        result = EvaluationResult.model_validate(data)
        return result.model_copy(update={"passed": result.verdict == "pass"})

    async def embed_query(self, query: str) -> list[float]:
        return await self._embed(f"task: question answering | query: {query}")

    async def embed_document(self, *, title: str, content: str) -> list[float]:
        safe_title = title.strip() or "none"
        return await self._embed(f"title: {safe_title} | text: {content}")

    async def _embed(self, content: str) -> list[float]:
        client = self._require_client()

        def call():
            return client.models.embed_content(
                model=self._settings.gemini_embedding_model,
                contents=content,
            )

        response = await self._with_retries("embedding", call)
        embeddings = getattr(response, "embeddings", None) or []
        if not embeddings and getattr(response, "embedding", None) is not None:
            embeddings = [getattr(response, "embedding")]
        if not embeddings:
            raise RuntimeError("Gemini returned no embeddings.")

        first = embeddings[0]
        values = getattr(first, "values", None)
        if values is None and isinstance(first, dict):
            values = first.get("values")
        if not values:
            raise RuntimeError("Gemini returned an embedding without values.")
        return [float(value) for value in values]

    def _answer_prompt(
        self,
        *,
        question: str,
        sources: list[SourceDocument],
        feedback: str | None,
    ) -> str:
        feedback_block = f"\nPrior evaluation feedback to address:\n{feedback}\n" if feedback else ""
        return (
            "You are Nexus, an enterprise retrieval-augmented generation system.\n"
            "Use only the retrieved source chunks for factual claims.\n"
            "Cite factual sentences with [doc_id].\n"
            "If the sources are insufficient, clearly say what is missing.\n"
            "Do not invent sources, numbers, URLs, or policies.\n"
            f"{feedback_block}\n"
            f"Question:\n{question}\n\n"
            f"Retrieved source chunks:\n{self._format_sources(sources)}\n\n"
            "Grounded answer:\n"
        )

    def _evaluation_prompt(self, *, question: str, answer: str, sources: list[SourceDocument]) -> str:
        return (
            "Evaluate this RAG answer against the retrieved source chunks only.\n"
            "Return JSON with verdict pass, partial, or fail; numeric scores from 0 to 1; "
            "unsupported_claims; missing_topics; feedback; and refined_query when another retrieval pass would help.\n\n"
            f"Question:\n{question}\n\n"
            f"Sources:\n{self._format_sources(sources)}\n\n"
            f"Answer:\n{answer}\n"
        )

    @staticmethod
    def _format_sources(sources: list[SourceDocument]) -> str:
        if not sources:
            return "No sources retrieved."
        chunks: list[str] = []
        for source in sources:
            chunks.append(
                f"[{source.doc_id}] chunk={source.chunk_id} title={source.title} "
                f"score={source.score:.4f}\n{source.content}"
            )
        return "\n\n---\n\n".join(chunks)


def _safe_json_loads(text: str) -> Any:
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise

