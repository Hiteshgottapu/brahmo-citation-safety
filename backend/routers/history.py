"""
Session History router for telemetry persistence.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from database import get_supabase

router = APIRouter(
    prefix="/api/history",
    tags=["History"],
)

class SessionHistorySaveRequest(BaseModel):
    practice_area: str
    query_snippet: str
    cached_query: str
    cached_raw_text: Optional[str] = None
    cached_html: Optional[str] = None
    badge_counts: Dict[str, Any] = Field(default_factory=dict)
    section_alerts: List[Dict[str, Any]] = Field(default_factory=list)
    cached_report: Dict[str, Any] = Field(default_factory=dict)

@router.post("/save")
async def save_session_history(request: SessionHistorySaveRequest):
    try:
        supabase = await get_supabase()
        response = await (
            supabase.table("session_history")
            .insert({
                "practice_area": request.practice_area,
                "query_snippet": request.query_snippet,
                "cached_query": request.cached_query,
                "cached_raw_text": request.cached_raw_text,
                "cached_html": request.cached_html,
                "badge_counts": request.badge_counts,
                "section_alerts": request.section_alerts,
                "cached_report": request.cached_report
            })
            .execute()
        )
        return {"status": "success", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fetch")
async def fetch_session_history():
    try:
        supabase = await get_supabase()
        response = await (
            supabase.table("session_history")
            .select("*")
            .order("created_at", desc=True)
            .limit(5)
            .execute()
        )
        return {"status": "success", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
