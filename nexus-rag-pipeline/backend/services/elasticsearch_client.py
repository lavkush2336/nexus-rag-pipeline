from __future__ import annotations

import logging
from collections import Counter
from typing import Any

from elasticsearch import AsyncElasticsearch

from backend.config import Settings
from backend.schemas import IndexedDocument, SourceDocument

logger = logging.getLogger(__name__)


class ElasticsearchService:
    def __init__(self, settings: Settings):
        self._settings = settings
        self.index = settings.elasticsearch_index
        self._client: AsyncElasticsearch | None = None
        if settings.elasticsearch_configured:
            self._client = AsyncElasticsearch(
                settings.elasticsearch_url,
                api_key=settings.elasticsearch_api_key,
                request_timeout=settings.request_timeout_seconds,
                retry_on_timeout=True,
                max_retries=2,
            )

    @property
    def configured(self) -> bool:
        return self._client is not None

    def _require_client(self) -> AsyncElasticsearch:
        if self._client is None:
            raise RuntimeError(
                "Missing ELASTICSEARCH_URL or ELASTICSEARCH_API_KEY. Configure Elasticsearch before retrieval."
            )
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()

    async def ping(self) -> bool:
        if self._client is None:
            return False
        try:
            return bool(await self._client.ping())
        except Exception:
            logger.warning("Elasticsearch ping failed.", exc_info=True)
            return False

    async def ensure_index(self, embedding_dims: int) -> None:
        client = self._require_client()
        if await client.indices.exists(index=self.index):
            return
        await client.indices.create(
            index=self.index,
            body={
                "settings": {"number_of_shards": 1, "number_of_replicas": 0},
                "mappings": {
                    "properties": {
                        "doc_id": {"type": "keyword"},
                        "chunk_id": {"type": "keyword"},
                        "title": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                        "content": {"type": "text"},
                        "source_name": {"type": "keyword"},
                        "created_at": {"type": "date"},
                        "metadata": {"type": "object", "enabled": True},
                        "embedding": {
                            "type": "dense_vector",
                            "dims": embedding_dims,
                            "index": True,
                            "similarity": "cosine",
                        },
                    }
                },
            },
        )

    async def index_chunk(self, *, chunk_id: str, document: dict[str, Any]) -> None:
        client = self._require_client()
        await client.index(index=self.index, id=chunk_id, document=document)

    async def refresh(self) -> None:
        client = self._require_client()
        await client.indices.refresh(index=self.index)

    async def vector_search(self, *, query_vector: list[float], top_k: int) -> list[SourceDocument]:
        client = self._require_client()
        if not await client.indices.exists(index=self.index):
            return []
        try:
            response = await client.search(
                index=self.index,
                body={
                    "size": top_k,
                    "knn": {
                        "field": "embedding",
                        "query_vector": query_vector,
                        "k": top_k,
                        "num_candidates": max(top_k * 8, 40),
                    },
                    "_source": ["doc_id", "chunk_id", "title", "content", "source_name", "metadata"],
                },
            )
            return [_hit_to_source(hit) for hit in response.get("hits", {}).get("hits", [])]
        except Exception:
            logger.warning("Elasticsearch vector search failed; falling back to lexical search.", exc_info=True)
            return []

    async def lexical_search(self, *, query: str, top_k: int) -> list[SourceDocument]:
        client = self._require_client()
        if not await client.indices.exists(index=self.index):
            return []
        response = await client.search(
            index=self.index,
            body={
                "size": top_k,
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title^2", "content", "source_name"],
                        "type": "best_fields",
                    }
                },
                "_source": ["doc_id", "chunk_id", "title", "content", "source_name", "metadata"],
            },
        )
        return [_hit_to_source(hit) for hit in response.get("hits", {}).get("hits", [])]

    async def count_chunks(self) -> int:
        client = self._require_client()
        if not await client.indices.exists(index=self.index):
            return 0
        response = await client.count(index=self.index)
        return int(response.get("count", 0))

    async def list_documents(self, *, limit: int = 100) -> list[IndexedDocument]:
        client = self._require_client()
        if not await client.indices.exists(index=self.index):
            return []
        response = await client.search(
            index=self.index,
            body={
                "size": min(max(limit * 5, 25), 500),
                "sort": [{"created_at": {"order": "desc", "unmapped_type": "date"}}],
                "query": {"match_all": {}},
                "_source": ["doc_id", "title", "source_name", "created_at", "metadata"],
            },
        )
        hits = response.get("hits", {}).get("hits", [])
        chunks_by_doc = Counter((hit.get("_source") or {}).get("doc_id") for hit in hits)
        documents: list[IndexedDocument] = []
        seen: set[str] = set()
        for hit in hits:
            source = hit.get("_source") or {}
            doc_id = str(source.get("doc_id") or hit.get("_id"))
            if doc_id in seen:
                continue
            seen.add(doc_id)
            documents.append(
                IndexedDocument(
                    doc_id=doc_id,
                    title=str(source.get("title") or "Untitled Document"),
                    source_name=source.get("source_name"),
                    chunks=chunks_by_doc.get(doc_id, 1),
                    created_at=source.get("created_at"),
                    metadata=source.get("metadata") or {},
                )
            )
            if len(documents) >= limit:
                break
        return documents


def _hit_to_source(hit: dict[str, Any]) -> SourceDocument:
    source = hit.get("_source") or {}
    return SourceDocument(
        doc_id=str(source.get("doc_id") or hit.get("_id") or ""),
        chunk_id=str(source.get("chunk_id") or hit.get("_id") or ""),
        title=str(source.get("title") or "Untitled Document"),
        content=str(source.get("content") or ""),
        score=float(hit.get("_score") or 0.0),
        source_name=source.get("source_name"),
        metadata=source.get("metadata") or {},
    )

