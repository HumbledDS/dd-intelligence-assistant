"""Embedder — Gemini text-embedding-004 → pgvector."""

import logging
import json
from google import genai

from api_services.core.config import settings

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 768
MODEL = "text-embedding-004"


class Embedder:
    """Embeds text chunks and stores them in PostgreSQL pgvector."""

    def __init__(self):
        self._client = None

    def _get_client(self) -> genai.Client:
        if self._client is None:
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return self._client

    async def embed_text(self, text: str) -> list[float]:
        """Embed a single text string → 768-dim vector."""
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not set — returning zero vector")
            return [0.0] * EMBEDDING_DIM

        client = self._get_client()
        response = client.models.embed_content(
            model=MODEL,
            contents=text,
        )
        return response.embeddings[0].values

    async def embed_report(self, siren: str, sections: list[dict]) -> None:
        """
        Embed all sections of a report and store in PostgreSQL.
        Called after report generation — enables RAG chat.
        """
        from api_services.core.database import async_session_factory
        from api_services.models import DocumentEmbedding
        from sqlalchemy import delete

        # Clear old embeddings for this SIREN
        async with async_session_factory() as db:
            await db.execute(
                delete(DocumentEmbedding).where(DocumentEmbedding.siren == siren)
            )

            for section in sections:
                section_type = section.get("type", "unknown")
                raw = section.get("data", {})

                # Flatten to text
                if isinstance(raw, dict):
                    text = json.dumps(raw, ensure_ascii=False)
                elif isinstance(raw, list):
                    text = "\n".join(
                        json.dumps(item, ensure_ascii=False) if isinstance(item, dict) else str(item)
                        for item in raw
                    )
                else:
                    text = str(raw)

                if not text.strip():
                    continue

                # Chunk if text > 2000 chars
                chunks = _chunk(text, max_len=2000)
                for i, chunk in enumerate(chunks):
                    try:
                        vector = await self.embed_text(chunk)
                        embedding_record = DocumentEmbedding(
                            siren=siren,
                            section_type=section_type,
                            chunk_index=i,
                            content=chunk,
                            embedding=vector,
                        )
                        db.add(embedding_record)
                    except Exception as e:
                        logger.error(f"Failed to embed chunk {i} for {siren}: {e}")

            await db.commit()
        logger.info(f"Embedded report for SIREN {siren}")


def _chunk(text: str, max_len: int = 2000) -> list[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks, current = [], []
    current_len = 0

    for word in words:
        current.append(word)
        current_len += len(word) + 1
        if current_len >= max_len:
            chunks.append(" ".join(current))
            # 10% overlap
            overlap = max(1, len(current) // 10)
            current = current[-overlap:]
            current_len = sum(len(w) + 1 for w in current)

    if current:
        chunks.append(" ".join(current))

    return chunks
