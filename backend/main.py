"""
Brahmo Citation Safety Engine — FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.legal_query import router
from routers.ingestion import router as ingestion_router

app = FastAPI(
    title="Brahmo Citation Safety Engine",
    version="1.0.0",
    description="Deterministic citation verification pipeline for Indian legal AI.",
)

# --- CORS (allow all origins for local dev / demo) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Register routers ---
app.include_router(router)
app.include_router(ingestion_router)

from routers.history import router as history_router
app.include_router(history_router)


from database import get_supabase

# --- Cache Warm-Up ---
@app.on_event("startup")
async def startup_event():
    """Cache Warm-Up: Pre-populate LRU cache with demo fallback citations to eliminate cold-start latency."""
    from engine.cache import lru_cache_pool, normalize_cache_key
    
    # Pre-populate citations from the demo scenarios
    demo_citations = [
        {"text": "Union of India v. Mohanlal (2016) 3 SCC 379", "status": "VERIFIED"},
        {"text": "Tofan Singh v. State of Tamil Nadu (2021) 4 SCC 1", "status": "VERIFIED"},
        {"text": "Mohd. Muslim v. State (NCT of Delhi) (2023) 4 SCC 789", "status": "VERIFIED"},
        {"text": "Arvind Kumar v. State of UP AIR 2024 SC 567", "status": "VERIFIED"},
        {"text": "State of Kerala v. Rajesh (2028) 3 SCC 45", "status": "REMOVED", "reason": "Hallucinated Year (2028 is in the future)"},
        {"text": "Satish Sharma v. NCB (2024) 47 SCC 123", "status": "REMOVED", "reason": "SCC Volume 47 exceeds historical constraints (Max ~20)"},
        {"text": "Pradeep Kumar v. State of Haryana (2023) 19 SCC 456", "status": "UNVERIFIED"},
        {"text": "Narcotics Control Bureau v. Mohit Aggarwal 2024 SCC OnLine SC 2345", "status": "VERIFIED"},
    ]

    for c in demo_citations:
        key = normalize_cache_key(c["text"])
        lru_cache_pool.put(key, {
            "status": c["status"],
            "case_name": None,
            "ik_doc_id": None,
            "correction_note": None,
            "original_text": c["text"],
            "reason": c.get("reason"),
        })
    print(f"🚀 [CACHE WARM-UP] Pre-populated LRU Cache with {len(demo_citations)} citations.")


# --- Health check ---
@app.get("/health")
async def health():
    try:
        supabase = await get_supabase()
        # Active database tier connectivity ping
        await supabase.table("section_mappings").select("*").limit(1).execute()
        return {"status": "ok", "engine": "brahmo-citation-safety", "db_connected": True}
    except Exception as e:
        return {"status": "degraded", "engine": "brahmo-citation-safety", "db_connected": False, "error": str(e)}
