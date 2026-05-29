// ── Legal Matter ──────────────────────────────────────────────
export interface LegalMatter {
  id: number;
  title: string;
  practice: string;
  court: string;
  query: string;
}

// ── Citation ─────────────────────────────────────────────────
export interface CitationInfo {
  original_text: string;
  pattern_name: string;
  year: number;
  volume: number | null;
  page: number | null;
}

export interface CitationResult {
  citation: CitationInfo;
  status: 'VERIFIED' | 'CORRECTED' | 'UNVERIFIED' | 'REMOVED';
  case_name: string | null;
  ik_doc_id: number | null;
  correction_note: string | null;
  original_text: string;
  reason: string | null;
}

// ── Section Alert ────────────────────────────────────────────
export interface SectionAlert {
  old_text: string;
  new_text: string;
  old_act: string;
  new_act: string;
}

// ── Cost Metrics ─────────────────────────────────────────────
export interface CostMetrics {
  total_searches: number;
  total_docmeta: number;
  total_cost: number;
  savings_from_prefilter: number;
  savings_from_cache: number;
}

// ── Processing Report ────────────────────────────────────────
export interface ProcessingReport {
  total_citations: number;
  verified: number;
  corrected: number;
  unverified: number;
  removed: number;
  accuracy_pct: number;
  api_calls_made: number;
  cost_metrics: CostMetrics;
}

// ── Full API Response ────────────────────────────────────────
export interface ProcessLegalQueryResponse {
  raw_text: string;
  annotated_text: string;
  annotated_html: string;
  citations: CitationResult[];
  section_alerts: SectionAlert[];
  report: ProcessingReport;
  rag_context: RAGContext | null;
}

// ── RAG Pipeline ────────────────────────────────────────────
export interface DocumentChunk {
  id: number;
  doc_id: string;
  doc_title: string;
  chunk_index: number;
  content: string;
  metadata: Record<string, unknown>;
  similarity: number;
}

export interface RAGContext {
  chunks: DocumentChunk[];
  total_chunks_searched: number;
  retrieval_time_ms: number;
}

// ── Dashboard Layout & State ────────────────────────────────
export interface SessionHistoryItem {
  id: string;
  practiceAreaId: number;
  practiceAreaLabel: string;
  querySnippet: string;
  fullQuery: string;
  timestamp: string;
  stats: {
    verified: number;
    corrected: number;
    unverified: number;
    removed: number;
  };
  genericResponse: ProcessLegalQueryResponse | null;
  verifiedResponse: ProcessLegalQueryResponse | null;
}

export interface HistoricCitationMetric {
  id: string;
  citationText: string;
  frequency: number;
  status: 'VERIFIED' | 'CORRECTED' | 'UNVERIFIED' | 'REMOVED';
  savings: number;
}
