"""Chat router — RAG-powered Q&A over a generated report."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api_services.core.database import get_db
from rag_pipeline.retriever import Retriever
from llm_orchestration.report_generator import ReportGenerator

router = APIRouter()
_retriever = Retriever()
_llm = ReportGenerator()


class ChatMessage(BaseModel):
    question: str


@router.post("/chat/{siren}")
async def chat(
    siren: str,
    msg: ChatMessage,
    db: AsyncSession = Depends(get_db),
):
    """Answer a question using RAG over the report's embedded chunks."""
    if not siren.isdigit() or len(siren) != 9:
        raise HTTPException(400, "SIREN must be 9 digits")

    # Retrieve relevant chunks from pgvector
    chunks = await _retriever.retrieve(
        query=msg.question,
        siren=siren,
        db=db,
        top_k=5,
    )

    if not chunks:
        raise HTTPException(404, "No report found for this company. Generate a report first.")

    # Generate answer grounded in retrieved chunks
    answer = await _llm.answer_question(
        question=msg.question,
        context_chunks=chunks,
    )

    return {
        "answer": answer,
        "sources": [{"content": c["content"][:200], "section_type": c["section_type"]} for c in chunks],
    }
