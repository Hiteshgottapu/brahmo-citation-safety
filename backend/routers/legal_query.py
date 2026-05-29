"""
Legal Query Router — orchestrates the full citation safety pipeline.

Endpoints:
  POST /api/process-legal-query  →  ProcessLegalQueryResponse
  GET  /api/legal-matters        →  list of LegalMatter dicts
"""

from __future__ import annotations

from fastapi import APIRouter

from config import (
    COST_PER_DOCMETA,
    COST_PER_SEARCH,
    GEMINI_API_KEY,
)
from data.legal_matters import LEGAL_MATTERS
from engine.citation_annotator import CitationAnnotator
from engine.citation_extractor import CitationExtractor
from engine.citation_repair import CitationRepair
from engine.citation_verifier import CitationVerifier
from engine.hallucination_detector import HallucinationDetector
from engine.section_normalizer import SectionNormalizer
from engine.rag_retriever import RAGRetriever
from models import (
    CitationResult,
    CostMetrics,
    ProcessingReport,
    ProcessLegalQueryRequest,
    ProcessLegalQueryResponse,
)

router = APIRouter()

# ======================================================================
# Engine Singletons (Global Lifetime Pattern)
# ======================================================================
normalizer = SectionNormalizer()
extractor = CitationExtractor()
repair = CitationRepair()
detector = HallucinationDetector()
verifier = CitationVerifier()
annotator = CitationAnnotator()

# ======================================================================
# LLM integration — Gemini with hardcoded fallback
# ======================================================================

_SYSTEM_PROMPT = (
    "You are an Indian legal research assistant. Provide well-cited legal "
    "analysis using Supreme Court and High Court case citations in standard "
    "Indian formats (SCC, AIR, SCC OnLine). Include specific case citations "
    "with proper formatting."
)

# ---------------------------------------------------------------------------
# Hardcoded fallback responses (from the Setup Guide sample AI outputs)
# ---------------------------------------------------------------------------

_FALLBACK_ANTICIPATORY_BAIL = """The Supreme Court has established comprehensive principles for anticipatory bail in economic offences:

In Siddharth v. State of UP (2021) 10 SCC 1, the Court laid down guidelines that anticipatory bail should not be denied merely because the accusation involves economic offences.

In Satender Kumar Antil v. CBI (2022) 10 SCC 51, the Court classified offences into categories for bail purposes.

In Arnesh Kumar v. State of Bihar (2014) 8 SCC 273, the Court issued comprehensive guidelines on arrest, directly relevant to anticipatory bail.

In Sushila Aggarwal v. State (NCT of Delhi) (2020) 5 SCC 1, the Court clarified that anticipatory bail can be granted without time limit.

The Delhi High Court in 2024 SCC OnLine Del 3456 granted anticipatory bail in a Section 318 BNS case citing the accused's cooperation with investigation."""

_FALLBACK_CHEATING_COMPLAINT = """COMPLAINT UNDER SECTION 420 IPC AND SECTION 406 IPC

The complainant respectfully submits that the accused has committed offences punishable under Section 420 of the Indian Penal Code (cheating and dishonestly inducing delivery of property) read with Section 120B IPC (criminal conspiracy) and Section 34 IPC (common intention).

The accused, acting in conspiracy, induced the complainant to part with Rs. 50,00,000 under the false pretense of a business partnership.

The complainant prays that an FIR be registered under Sections 420, 406, 120B and 34 of the Indian Penal Code against the accused persons."""

_FALLBACK_NDPS_BAIL = """The Supreme Court's approach to bail in NDPS cases over the last 5 years has evolved significantly:

In Union of India v. Mohanlal (2016) 3 SCC 379, the Court laid the foundation by interpreting Section 37 of the NDPS Act strictly.

In Tofan Singh v. State of Tamil Nadu (2021) 4 SCC 1, the Court held that statements recorded under Section 67 of the NDPS Act are inadmissible as confessions.

In Mohd. Muslim v. State (NCT of Delhi) (2023) 4 SCC 789, the Court addressed the question of whether commercial quantity necessitates denial of bail.

In Arvind Kumar v. State of UP AIR 2024 SC 567, the Court reiterated that prolonged incarceration without trial is a valid ground for bail even in NDPS cases.

In State of Kerala v. Rajesh (2028) 3 SCC 45, the Court set out a comprehensive framework for bail in NDPS cases.

In Satish Sharma v. NCB (2024) 47 SCC 123, the Court addressed the role of electronic evidence in NDPS prosecutions.

In Pradeep Kumar v. State of Haryana (2023) 19 SCC 456, the Court discussed the interplay between Section 37 NDPS Act and Article 21.

In Narcotics Control Bureau v. Mohit Aggarwal 2024 SCC OnLine SC 2345, the Court provided clarity on the meaning of "reasonable grounds" under Section 37."""

_FALLBACK_SECTION_482 = """Key Delhi High Court decisions on Section 482 BNSS (formerly Section 482 CrPC) powers in the last 2 years:

In Rajiv Gupta v. State of NCT of Delhi 2024 SCC OnLine Del 3456, the Court discussed the scope of inherent powers.

In Smt. Kavita v. State AIR 2024 Del 234, the Court held that Section 482 powers should be exercised sparingly.

In Mohd. Salim v. State of NCT of Delhi (2023) 5 SCC 123, the Court addressed quashing of FIRs in matrimonial disputes.

In Priya Sharma v. State 2024 SCC OnLine Del 7890, the Court reiterated the Bhajan Lal guidelines.

In Ashok Kumar v. State of NCT of Delhi (2024) 3 SCC 456, the Court discussed the parameters for exercising inherent jurisdiction.

In State v. Harish Chand MANU/DE/4567/2024, the Court provided guidance on quashing proceedings at the charge stage."""

_FALLBACK_GENERIC = """Based on the legal query, the relevant case law and statutory provisions include the following analysis:

The Supreme Court in Vishaka v. State of Rajasthan (1997) 6 SCC 241 established foundational principles that continue to guide the legal framework.

In Maneka Gandhi v. Union of India (1978) 1 SCC 248, the Court expanded the scope of Article 21 to include the right to live with dignity.

The Delhi High Court in 2024 SCC OnLine Del 1234 applied these principles in a recent matter.

Further, in K.S. Puttaswamy v. Union of India (2017) 10 SCC 1, the right to privacy was recognized as a fundamental right.

These precedents collectively establish a comprehensive legal framework applicable to the matter at hand."""


def _get_fallback_response(query: str) -> str:
    """Pick the best matching fallback based on clear, explicit keywords."""
    q_lower = query.lower()
    if "anticipatory bail" in q_lower or "economic offence" in q_lower:
        return _FALLBACK_ANTICIPATORY_BAIL
    if "cheating" in q_lower or "section 420" in q_lower or "section 406" in q_lower:
        return _FALLBACK_CHEATING_COMPLAINT
    if "ndps" in q_lower or "narcotics" in q_lower:
        return _FALLBACK_NDPS_BAIL
    if "quash" in q_lower or "inherent powers" in q_lower:
        return _FALLBACK_SECTION_482
    return _FALLBACK_GENERIC


async def _fetch_ledger_totals() -> tuple[float, float]:
    """Fetch total bill and savings across all sessions atomically."""
    from database import get_supabase
    try:
        supabase = await get_supabase()
        res = await supabase.table("session_history").select("cached_report").execute()
        total_bill = 0.0
        total_savings = 0.0
        for row in res.data:
            report = row.get("cached_report") or {}
            metrics = report.get("cost_metrics") or {}
            total_bill += float(metrics.get("total_cost", 0.0))
            total_savings += float(metrics.get("savings_from_prefilter", 0.0)) + float(metrics.get("savings_from_cache", 0.0))
        return total_bill, total_savings
    except Exception:
        # Graceful evaluation to 0.00 if DB is empty or connection fails
        return 0.0, 0.0


async def _call_llm(prompt: str) -> str:
    """Call Gemini if API key is set, otherwise return a hardcoded fallback."""
    if GEMINI_API_KEY:
        try:
            import asyncio
            from google import genai

            client = genai.Client(api_key=GEMINI_API_KEY)

            # The new SDK's generate_content is synchronous;
            # wrap in run_in_executor to avoid blocking the event loop.
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=f"{_SYSTEM_PROMPT}\n\nUser query: {prompt}",
                ),
            )
            return response.text
        except Exception:
            # LLM call failed — fall through to fallback
            pass

    return _get_fallback_response(prompt)


# ======================================================================
# Endpoints
# ======================================================================

@router.post("/api/process-legal-query", response_model=ProcessLegalQueryResponse)
async def process_legal_query(
    request: ProcessLegalQueryRequest,
) -> ProcessLegalQueryResponse:
    """Full citation safety pipeline."""

    # (Engine singletons are instantiated globally at the module level)

    # ==================================================================
    # MODE: generic — raw LLM output, no processing
    # ==================================================================
    if request.mode == "generic":
        llm_response = await _call_llm(request.query)
        return ProcessLegalQueryResponse(
            raw_text=llm_response,
            annotated_text="",
            annotated_html="",
            citations=[],
            section_alerts=[],
            report=ProcessingReport(
                total_citations=0,
                verified=0,
                corrected=0,
                unverified=0,
                removed=0,
                accuracy_pct=0.0,
                cost_metrics=CostMetrics(),
                api_calls_made=0,
            ),
        )

    # ==================================================================
    # MODE: verified — full pipeline
    # ==================================================================

    # a) Pass 1 — normalize the user's query
    norm_result_1 = await normalizer.normalize_text(request.query)

    # a2) RAG retrieval — semantic search for relevant knowledge chunks
    retriever = RAGRetriever()
    rag_context = await retriever.retrieve(norm_result_1.normalized_text, top_k=5)

    # a3) Assemble RAG-augmented prompt (pre-normalizes retrieved chunks)
    augmented_prompt = await retriever.assemble_prompt(
        norm_result_1.normalized_text, rag_context
    )

    # b) Call LLM with RAG-augmented prompt
    raw_llm = await _call_llm(augmented_prompt)

    # d) Pass 2 — normalize the LLM output
    norm_result_2 = await normalizer.normalize_text(raw_llm)

    # e) Merge alerts from both passes (deduplicate by old_text)
    seen_alerts: set[str] = set()
    all_alerts = []
    for alert in norm_result_1.alerts + norm_result_2.alerts:
        key = f"{alert.old_text}_{alert.old_act}"
        if key not in seen_alerts:
            seen_alerts.add(key)
            all_alerts.append(alert)

    # f) Extract citations from BOTH user query AND LLM output
    query_citations = await extractor.extract_citations(
        norm_result_1.normalized_text
    )
    llm_citations = await extractor.extract_citations(
        norm_result_2.normalized_text
    )

    # Build combined text: user query + separator + LLM output
    # This ensures sabotage citations in the user's input get annotated
    combined_text = (
        f"[USER QUERY]\n{norm_result_1.normalized_text}\n\n"
        f"[LLM ANALYSIS]\n{norm_result_2.normalized_text}"
    )

    # Deduplicate citations by original_text
    seen_citations: set[str] = set()
    all_citations: list = []
    for c in query_citations + llm_citations:
        if c.original_text not in seen_citations:
            seen_citations.add(c.original_text)
            all_citations.append(c)

    # g) Repair citations
    repaired_citations = []
    corrected_notes: dict[str, str] = {}
    for c in all_citations:
        repaired, was_modified, note = repair.repair_citation(c)
        repaired_citations.append(repaired)
        if was_modified:
            corrected_notes[repaired.original_text] = note

    # h) Hallucination pre-filter
    prefilter_results: dict[str, tuple[str, str]] = {}
    for c in repaired_citations:
        status, reason = detector.detect(c)
        prefilter_results[c.original_text] = (status, reason)

    # i) Cache gate
    cache_hits, cache_misses = await verifier.check_cache_gate(repaired_citations)

    # j) Split cache misses by prefilter outcome
    remaining_misses: list = []
    removed_by_prefilter: list = []

    for c in cache_misses:
        pf = prefilter_results.get(c.original_text, ("PASS", ""))
        if pf[0] == "REMOVED":
            removed_by_prefilter.append(c)
        else:
            remaining_misses.append(c)

    prefilter_removed_results = [
        CitationResult(
            citation=c,
            status="REMOVED",
            original_text=c.original_text,
            reason=prefilter_results[c.original_text][1],
        )
        for c in removed_by_prefilter
    ]

    # Track prefilter savings
    verifier.cost_metrics.savings_from_prefilter = len(removed_by_prefilter) * (
        COST_PER_SEARCH + COST_PER_DOCMETA
    )

    # k) Process remaining misses locally (External API removed)
    ik_results = await verifier.process_cache_misses(
        remaining_misses, prefilter_results
    )

    # l) Merge all results and apply corrected notes
    all_results = cache_hits + prefilter_removed_results + ik_results

    for r in all_results:
        if r.original_text in corrected_notes:
            r.correction_note = corrected_notes[r.original_text]
            if r.status == "VERIFIED":
                r.status = "CORRECTED"

    # m) Annotate the combined text (user query + LLM output)
    annotated_text, annotated_html = annotator.annotate_text(
        combined_text, all_results
    )

    # n) Generate report
    report = annotator.generate_report(all_results, verifier.cost_metrics)

    # ==========================================================================
    # TELEMETRY PERSISTENCE & LEDGER AGGREGATION
    # ==========================================================================
    
    # Extract practice area for telemetry
    practice_area = "Unknown"
    for m in LEGAL_MATTERS:
        if m["id"] == request.matter_id:
            practice_area = m["practice"]
            break

    try:
        from database import get_supabase
        supabase = await get_supabase()
        
        # 1. State-Writing: Persist the current session explicitly BEFORE aggregation
        await supabase.table("session_history").insert({
            "practice_area": practice_area,
            "query_snippet": request.query[:100],
            "cached_query": request.query,
            "cached_raw_text": raw_llm,
            "cached_html": annotated_html,
            "badge_counts": {
                "verified": report.verified,
                "corrected": report.corrected,
                "unverified": report.unverified,
                "removed": report.removed
            },
            "section_alerts": [a.model_dump() for a in all_alerts],
            "cached_report": report.model_dump()
        }).execute()
    except Exception:
        pass  # Maintain robust exception boundaries
    
    # 2. Financial-Summing: Calculate global system-wide roll-up totals
    total_bill, total_savings = await _fetch_ledger_totals()
    report.total_bill_all_sessions = total_bill
    report.total_savings_all_sessions = total_savings

    # o) Cleanup (Removed 'await verifier.close()' to maintain open connection pool)
    # p) Return response
    return ProcessLegalQueryResponse(
        raw_text=raw_llm,
        annotated_text=annotated_text,
        annotated_html=annotated_html,
        citations=all_results,
        section_alerts=all_alerts,
        report=report,
        rag_context=rag_context,
    )


@router.get("/api/legal-matters")
async def get_legal_matters():
    """Return the 8 pre-loaded legal matters."""
    return LEGAL_MATTERS
