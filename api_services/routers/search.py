"""Search router — company lookup via DINUM API with L1/L2 caching."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api_services.core.database import get_db
from api_services.core.cache import get_cached, set_cached
from shared.services import dinum_search, dinum_get_company

router = APIRouter()


@router.get("/search")
async def search_companies(
    q: str = Query(..., min_length=2, description="Company name or SIREN"),
    db: AsyncSession = Depends(get_db),
):
    """Search French companies by name or SIREN number."""
    cache_key = f"search:{q.lower().strip()}"

    cached = await get_cached(cache_key, db)
    if cached:
        return {"source": "cache", "results": cached}

    try:
        results = await dinum_search(q)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Search service unavailable: {e}")

    await set_cached(cache_key, results, "dinum", db)
    return {"source": "live", "results": results}


@router.get("/company/{siren}")
async def get_company(siren: str, db: AsyncSession = Depends(get_db)):
    """Get full company profile by SIREN (9 digits)."""
    if len(siren) != 9 or not siren.isdigit():
        raise HTTPException(status_code=400, detail="SIREN must be 9 digits")

    cache_key = f"company:{siren}"
    cached = await get_cached(cache_key, db)
    if cached:
        return {"source": "cache", "company": cached}

    try:
        company = await dinum_get_company(siren)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Company not found: {e}")

    await set_cached(cache_key, company, "dinum", db)
    return {"source": "live", "company": company}
