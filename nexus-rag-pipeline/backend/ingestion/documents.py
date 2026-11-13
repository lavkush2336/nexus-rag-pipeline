from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from backend.config import Settings
from backend.services.elasticsearch_client import ElasticsearchService
from backend.services.gemini import GeminiService


async def index_upload(
    *,
    file: UploadFile,
    settings: Settings,
    gemini: GeminiService,
    elasticsearch: ElasticsearchService,
) -> tuple[str, str, int]:
    raw = await file.read()
    text = _decode_text(raw)
    title = Path(file.filename or "uploaded-document").stem or "Uploaded Document"
    chunks = chunk_text(
        text,
        chunk_size=settings.chunk_size_chars,
        overlap=settings.chunk_overlap_chars,
    )
    if not chunks:
        raise ValueError("Uploaded document did not contain indexable text.")

    doc_id = uuid4().hex
    created_at = datetime.now(UTC).isoformat()

    first_embedding = await gemini.embed_document(title=title, content=chunks[0])
    await elasticsearch.ensure_index(len(first_embedding))

    for index, chunk in enumerate(chunks):
        chunk_id = f"{doc_id}-{index + 1}"
        embedding = first_embedding if index == 0 else await gemini.embed_document(title=title, content=chunk)
        await elasticsearch.index_chunk(
            chunk_id=chunk_id,
            document={
                "doc_id": doc_id,
                "chunk_id": chunk_id,
                "title": title,
                "content": chunk,
                "source_name": file.filename,
                "created_at": created_at,
                "metadata": {
                    "content_type": file.content_type,
                    "chunk_index": index + 1,
                    "chunk_count": len(chunks),
                },
                "embedding": embedding,
            },
        )

    await elasticsearch.refresh()
    return doc_id, title, len(chunks)


def chunk_text(text: str, *, chunk_size: int, overlap: int) -> list[str]:
    normalized = "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").split("\n")).strip()
    if not normalized:
        return []

    paragraphs = [paragraph.strip() for paragraph in normalized.split("\n\n") if paragraph.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= chunk_size:
            current = candidate
            continue
        if current:
            chunks.append(current)
        if len(paragraph) <= chunk_size:
            current = paragraph
            continue
        for start in range(0, len(paragraph), max(chunk_size - overlap, 1)):
            piece = paragraph[start : start + chunk_size].strip()
            if piece:
                chunks.append(piece)
        current = ""
    if current:
        chunks.append(current)
    return chunks


def _decode_text(raw: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")

