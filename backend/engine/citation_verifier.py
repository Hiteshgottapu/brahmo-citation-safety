"""
Citation Verifier — verifies citations against the Indian Kanoon API.

Handles:
  • Cache-gate: check Supabase verification_cache before hitting IK
  • Parallel IK verification via asyncio.gather
  • Cost tracking (searches, docmeta, savings)
  • Graceful error handling — API failures result in UNVERIFIED, never crashes
"""

from __future__ import annotations

import asyncio
from typing import Optional

from config import (
    COST_PER_DOCMETA,
    COST_PER_SEARCH,
)
from database import get_supabase
from models import Citation, CitationResult, CostMetrics


class CitationVerifier:
    """Async verifier that resolves cache hits and processes cache misses."""

    def __init__(self) -> None:
        self.cost_metrics = CostMetrics(
            total_searches=0,
            total_docmeta=0,
            total_cost=0.0,
            savings_from_prefilter=0.0,
            savings_from_cache=0.0,
        )

    # ------------------------------------------------------------------
    # Cache gate
    # ------------------------------------------------------------------

    async def check_cache_gate(
        self, citations: list[Citation]
    ) -> tuple[list[CitationResult], list[Citation]]:
        """Check the LRU Memory Pool, then verification_cache table for each citation.

        Returns
        -------
        (cache_hits, cache_misses)
        """
        supabase = await get_supabase()
        cache_hits: list[CitationResult] = []
        cache_misses: list[Citation] = []

        from engine.cache import lru_cache_pool, normalize_cache_key, get_cached_citation

        for citation in citations:
            key = normalize_cache_key(citation.original_text)
            cached_val = get_cached_citation(citation.original_text)

            # 1. Check LRU In-Memory Cache
            if cached_val is not None:
                print(f"⚡ [CACHE HIT] Citation found in local memory pool: {key}")
                result = CitationResult(
                    citation=citation,
                    status=cached_val["status"],
                    case_name=cached_val.get("case_name"),
                    ik_doc_id=cached_val.get("ik_doc_id"),
                    original_text=cached_val["original_text"],
                    reason=cached_val.get("reason"),
                )
                if cached_val.get("correction_note"):
                    result.correction_note = cached_val["correction_note"]
                cache_hits.append(result)
                continue

            # 2. Check Database Layer (Supabase) if LRU misses
            print(f"🔍 [CACHE MISS] Citation not found in LRU pool. Proceeding to database/API tier: {key}")
            try:
                response = (
                    await supabase.table("verification_cache")
                    .select("*")
                    .eq("citation_text", citation.original_text)
                    .execute()
                )
                rows = response.data or []

                if rows:
                    row = rows[0]
                    result = CitationResult(
                        citation=citation,
                        status=row.get("status", "UNVERIFIED"),
                        case_name=row.get("case_name"),
                        ik_doc_id=row.get("ik_doc_id"),
                        original_text=citation.original_text,
                        reason=row.get("reason"),
                    )
                    cache_hits.append(result)
                    
                    # Hydrate LRU Cache for next time
                    lru_cache_pool.put(key, {
                        "status": result.status,
                        "case_name": result.case_name,
                        "ik_doc_id": result.ik_doc_id,
                        "correction_note": result.correction_note,
                        "original_text": result.original_text,
                        "reason": result.reason
                    })
                else:
                    cache_misses.append(citation)
            except Exception:
                # On any DB error, treat as cache miss
                cache_misses.append(citation)

        # Track savings: ₹0.80 per cached citation
        self.cost_metrics.savings_from_cache = len(cache_hits) * (
            COST_PER_SEARCH + COST_PER_DOCMETA
        )

        return cache_hits, cache_misses

    # ------------------------------------------------------------------
    # Cache miss processing (Local only)
    # ------------------------------------------------------------------

    async def process_cache_misses(
        self,
        cache_misses: list[Citation],
        prefilter_results: dict[str, tuple[str, str]],
    ) -> list[CitationResult]:
        """Process citations that were not found in the cache.
        Since external API verification was removed, this marks them UNVERIFIED
        or REMOVED based on local prefilter.
        """
        if not cache_misses:
            return []

        results = []
        for citation in cache_misses:
            prefilter = prefilter_results.get(citation.original_text, ("PASS", ""))

            if prefilter[0] == "REMOVED":
                result = CitationResult(
                    citation=citation,
                    status="REMOVED",
                    original_text=citation.original_text,
                    reason=prefilter[1],
                )
            elif prefilter[0] == "SUSPICIOUS":
                result = CitationResult(
                    citation=citation,
                    status="REMOVED",
                    original_text=citation.original_text,
                    reason="Flagged as suspicious locally",
                )
            else:
                result = CitationResult(
                    citation=citation,
                    status="UNVERIFIED",
                    original_text=citation.original_text,
                    reason="External verification disabled",
                )

            await self._write_cache(result)
            results.append(result)

        return results

    # ------------------------------------------------------------------
    # Cache writer
    # ------------------------------------------------------------------

    async def _write_cache(self, result: CitationResult) -> None:
        """Upsert the verification result into the LRU pool and cache table."""
        from engine.cache import lru_cache_pool, normalize_cache_key
        key = normalize_cache_key(result.original_text)
        lru_cache_pool.put(key, {
            "status": result.status,
            "case_name": result.case_name,
            "ik_doc_id": result.ik_doc_id,
            "correction_note": result.correction_note,
            "original_text": result.original_text,
            "reason": result.reason
        })

        try:
            supabase = await get_supabase()
            row = {
                "citation_text": result.original_text,
                "status": result.status,
                "case_name": result.case_name,
                "ik_doc_id": result.ik_doc_id,
                "reason": result.reason,
            }
            await (
                supabase.table("verification_cache")
                .upsert(row, on_conflict="citation_text")
                .execute()
            )
        except Exception:
            # Cache write failure is non-critical — proceed silently
            pass
