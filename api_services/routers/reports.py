"""Reports router — async report generation with SSE streaming."""

import asyncio
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api_services.core.database import get_db
from api_services.core.cache import get_cached, set_cached
from shared.services import (
    dinum_get_company,
    dinum_get_dirigeants,
    dinum_get_finances,
    bodacc_get_announcements,
    news_get_articles,
)
from llm_orchestration.report_generator import ReportGenerator
from rag_pipeline.embedder import Embedder

router = APIRouter()
_llm = ReportGenerator()
_embedder = Embedder()

# In-memory job store (sufficient for single-instance MVP)
_jobs: dict[str, dict] = {}


class ReportRequest(BaseModel):
    siren: str
    report_type: str = "standard"  # quick | standard | full


@router.post("/report/generate")
async def generate_report(
    req: ReportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Start async report generation. Returns job_id immediately."""
    if not req.siren.isdigit() or len(req.siren) != 9:
        raise HTTPException(400, "SIREN must be 9 digits")

    cache_key = f"report:{req.siren}:{req.report_type}"
    cached = await get_cached(cache_key, db)
    if cached:
        return {"job_id": None, "status": "cache_hit", "report": cached}

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "status": "queued",
        "siren": req.siren,
        "report_type": req.report_type,
        "sections": [],
        "error": None,
    }

    background_tasks.add_task(
        _run_pipeline, job_id, req.siren, req.report_type, cache_key
    )
    return {"job_id": job_id, "status": "queued"}


@router.get("/report/{job_id}")
async def get_report(job_id: str):
    """Poll report status and result."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@router.get("/report/{job_id}/stream")
async def stream_report(job_id: str):
    """SSE stream — delivers sections as they are generated."""
    if job_id not in _jobs:
        raise HTTPException(404, "Job not found")

    async def event_generator():
        sent = 0
        while True:
            sections = _jobs[job_id].get("sections", [])
            while sent < len(sections):
                yield f"data: {json.dumps(sections[sent])}\n\n"
                sent += 1
            if _jobs[job_id].get("status") in ("completed", "failed"):
                yield f"data: {json.dumps({'status': _jobs[job_id]['status']})}\n\n"
                break
            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


async def _run_pipeline(job_id: str, siren: str, report_type: str, cache_key: str):
    """Background pipeline: 4-phase data collection + Gemini synthesis."""
    job = _jobs[job_id]
    job["status"] = "processing"

    try:
        # Phase 1 — Identity (DINUM, ~1-3s)
        identity = await dinum_get_company(siren)
        job["sections"].append({"type": "identity", "data": identity})
        company_name = identity.get("nom_complet", siren)

        # Phase 2 — Dirigeants & Financial data via DINUM (free, no key)
        dirigeants = await dinum_get_dirigeants(siren)
        if dirigeants:
            job["sections"].append({"type": "dirigeants", "data": dirigeants})

        finances = await dinum_get_finances(siren)
        if finances:
            job["sections"].append({"type": "finances", "data": finances})

        bodacc = await bodacc_get_announcements(siren)
        if bodacc:
            job["sections"].append({"type": "bodacc", "data": bodacc})

        # Phase 3 — Reputation (skip for "quick")
        if report_type in ("standard", "full"):
            news = await news_get_articles(company_name)
            if news:
                job["sections"].append({"type": "news", "data": news})

        # Phase 4 — Gemini synthesis
        synthesis = await _llm.generate(
            siren=siren,
            sections=job["sections"],
            report_type=report_type,
        )
        job["sections"].append({"type": "synthesis", "data": synthesis})

        # Embed all chunks for RAG chat
        await _embedder.embed_report(siren, job["sections"])

        job["status"] = "completed"
        job["completed_at"] = datetime.now(timezone.utc).isoformat()

    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)
