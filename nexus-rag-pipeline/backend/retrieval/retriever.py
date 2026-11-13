from __future__ import annotations

from backend.retrieval.ranker import rank_context
from backend.schemas import SourceDocument
from backend.services.elasticsearch_client import ElasticsearchService
from backend.services.gemini import GeminiService


class ElasticsearchRetriever:
    def __init__(self, *, elasticsearch: ElasticsearchService, gemini: GeminiService):
        self._elasticsearch = elasticsearch
        self._gemini = gemini

    async def retrieve(self, *, query: str, top_k: int) -> list[SourceDocument]:
        query_vector = await self._gemini.embed_query(query)
        vector_results = await self._elasticsearch.vector_search(query_vector=query_vector, top_k=top_k)
        lexical_results = await self._elasticsearch.lexical_search(query=query, top_k=top_k)

        merged: dict[str, SourceDocument] = {}
        for result in [*vector_results, *lexical_results]:
            existing = merged.get(result.chunk_id)
            if existing is None or result.score > existing.score:
                merged[result.chunk_id] = result

        return rank_context(query, list(merged.values()), top_k)

