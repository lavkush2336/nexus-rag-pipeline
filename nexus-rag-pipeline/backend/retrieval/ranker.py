from __future__ import annotations

import re

from backend.schemas import SourceDocument

_TOKEN_RE = re.compile(r"[a-z0-9]{3,}", re.IGNORECASE)


def rank_context(query: str, documents: list[SourceDocument], limit: int) -> list[SourceDocument]:
    query_terms = set(_TOKEN_RE.findall(query.lower()))
    ranked: list[SourceDocument] = []
    for document in documents:
        content_terms = set(_TOKEN_RE.findall(f"{document.title} {document.content}".lower()))
        overlap = len(query_terms.intersection(content_terms))
        overlap_score = overlap / max(len(query_terms), 1)
        blended = float(document.score or 0.0) + overlap_score
        ranked.append(document.model_copy(update={"score": round(blended, 5)}))
    ranked.sort(key=lambda item: item.score, reverse=True)
    return ranked[:limit]

