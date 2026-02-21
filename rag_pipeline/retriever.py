"""Retriever — pgvector cosine similarity search for RAG."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from rag_pipeline.embedder import Embedder

logger = logging.getLogger(__name__)


class Retriever:
    """Retrieves the most relevant document chunks from pgvector."""

    def __init__(self):
        self._embedder = Embedder()

    async def retrieve(
        self, query: str, siren: str, db: AsyncSession, top_k: int = 5
    ) -> list[dict]:
        """
        Embed the query, then do cosine similarity search in pgvector.
        Scoped to a single SIREN for focused RAG.
        """
        query_vector = await self._embedder.embed_text(query)

        # pgvector cosine distance operator: <=>
        sql = text(
            """
            SELECT content, section_type, chunk_index,
                   1 - (embedding <=> cast(:vec AS vector)) AS similarity
            FROM document_embeddings
            WHERE siren = :siren
            ORDER BY embedding <=> cast(:vec AS vector)
            LIMIT :top_k
            """
        )

        result = await db.execute(
            sql,
            {
                "vec": f"[{','.join(str(v) for v in query_vector)}]",
                "siren": siren,
                "top_k": top_k,
            },
        )
        rows = result.fetchall()

        return [
            {
                "content": row.content,
                "section_type": row.section_type,
                "chunk_index": row.chunk_index,
                "similarity": float(row.similarity),
            }
            for row in rows
        ]
