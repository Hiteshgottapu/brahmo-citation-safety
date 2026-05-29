"""
Pydantic models for the Brahmo Citation Safety Engine.
Every field specified — no optional shortcuts.
"""

from __future__ import annotations
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Database-backed models
# ---------------------------------------------------------------------------

class CitationPattern(BaseModel):
    """A single citation regex pattern loaded from the citation_patterns table."""
    id: int
    pattern_name: str
    regex_pattern: str
    format_template: str
    jurisdiction: str


class SectionMapping(BaseModel):
    """Old-to-new statute section mapping loaded from section_mappings table."""
    id: int
    old_section: str
    new_section: str
    old_act: str
    new_act: str


# ---------------------------------------------------------------------------
# Core citation domain models
# ---------------------------------------------------------------------------

class Citation(BaseModel):
    """A single citation extracted from text."""
    original_text: str
    pattern_name: str
    year: Optional[int] = None
    volume: Optional[int] = None
    page: Optional[int] = None
    court: Optional[str] = None
    components: dict = Field(default_factory=dict)


class CitationResult(BaseModel):
    """Result of verifying / processing a single citation."""
    citation: Citation
    status: str  # VERIFIED | CORRECTED | UNVERIFIED | REMOVED
    case_name: Optional[str] = None
    ik_doc_id: Optional[int] = None
    correction_note: Optional[str] = None
    original_text: str
    reason: Optional[str] = None


# ---------------------------------------------------------------------------
# Section normalizer models
# ---------------------------------------------------------------------------

class SectionAlert(BaseModel):
    """Alert raised when an old section reference is replaced."""
    old_text: str
    new_text: str
    old_act: str
    new_act: str


class NormalizationResult(BaseModel):
    """Result of running the section normalizer on text."""
    normalized_text: str
    alerts: list[SectionAlert] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Cost & reporting models
# ---------------------------------------------------------------------------

class CostMetrics(BaseModel):
    """Tracks API-call costs and savings."""
    total_searches: int = 0
    total_docmeta: int = 0
    total_cost: float = 0.0
    savings_from_prefilter: float = 0.0
    savings_from_cache: float = 0.0


class ProcessingReport(BaseModel):
    """Summary statistics for a citation-processing run."""
    total_citations: int = 0
    verified: int = 0
    corrected: int = 0
    unverified: int = 0
    removed: int = 0
    accuracy_pct: float = 0.0
    cost_metrics: CostMetrics = Field(default_factory=CostMetrics)
    api_calls_made: int = 0
    total_bill_all_sessions: float = 0.0
    total_savings_all_sessions: float = 0.0


# ---------------------------------------------------------------------------
# API request / response models
# ---------------------------------------------------------------------------

class ProcessLegalQueryRequest(BaseModel):
    """Incoming request to process a legal query."""
    query: str
    matter_id: int
    mode: Literal["generic", "verified"]


class ProcessLegalQueryResponse(BaseModel):
    """Full response returned to the frontend."""
    raw_text: str
    annotated_text: str
    annotated_html: str
    citations: list[CitationResult] = Field(default_factory=list)
    section_alerts: list[SectionAlert] = Field(default_factory=list)
    report: ProcessingReport = Field(default_factory=ProcessingReport)
    rag_context: Optional["RAGContext"] = None


# ---------------------------------------------------------------------------
# Legal matter model
# ---------------------------------------------------------------------------

class LegalMatter(BaseModel):
    """A pre-loaded legal matter for the demo UI."""
    id: int
    title: str
    practice: str
    court: str
    query: str


# ---------------------------------------------------------------------------
# RAG pipeline models
# ---------------------------------------------------------------------------

class DocumentChunk(BaseModel):
    """A single retrieved chunk from the pgvector knowledge base."""
    id: int
    doc_id: str
    doc_title: str
    chunk_index: int
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    similarity: float = 0.0


class RAGContext(BaseModel):
    """Context returned by the RAG retrieval phase."""
    chunks: list[DocumentChunk] = Field(default_factory=list)
    total_chunks_searched: int = 0
    retrieval_time_ms: float = 0.0


class IngestDocumentRequest(BaseModel):
    """Request body for document ingestion endpoint."""
    doc_id: str
    doc_title: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
