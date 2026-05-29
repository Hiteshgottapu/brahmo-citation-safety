import { useState } from 'react';
import { ChevronDown, ChevronUp, Database, FileText, Search } from 'lucide-react';
import type { RAGContext as RAGContextType } from '../types';

interface OutputComparisonProps {
  rawText: string | null;
  safeHtml: string | null;
  ragContext: RAGContextType | null;
  isProcessing: boolean;
}

export default function OutputComparison({
  rawText,
  safeHtml,
  ragContext,
  isProcessing,
}: OutputComparisonProps) {
  const [ragExpanded, setRagExpanded] = useState(false);

  const ragChunks = ragContext?.chunks ?? [];

  // Client-side sanitizer for text payloads and layout typography
  const sanitizedHtml = safeHtml
    ? safeHtml
        // 1. Collapse duplicate statutory acronym suffixes (e.g., "IPC IPC" -> "IPC")
        .replace(/\b([A-Z]{2,})\s+\1\b/g, '$1')
        // 2. Standardize INTERCEPTED USER QUERY heading with mt-4 mb-2
        .replace(
          /<div[^>]*>🎯.*?<\/div>/i,
          '<div class="mt-4 mb-2 font-sans text-[10px] font-bold text-slate-500 tracking-wider uppercase not-italic">🎯 INTERCEPTED USER QUERY</div>'
        )
        // 3. Standardize VERIFIED LEGAL COMPLAINT & ANALYSIS heading with mt-4 mb-2
        .replace(
          /<h3[^>]*>⚖️.*?<\/h3>/i,
          '<h3 class="mt-4 mb-2 text-sm font-bold tracking-wide text-slate-200 uppercase flex items-center gap-2">⚖️ VERIFIED LEGAL COMPLAINT & ANALYSIS</h3>'
        )
    : null;

  return (
    <div className="flex h-full flex-col gap-3 overflow-hidden">
      {/* ── Split Comparison ─────────────────────────────── */}
      <div className="grid flex-1 grid-rows-2 gap-3 overflow-hidden">
        {/* Panel A: Raw LLM Output */}
        <div className="flex flex-col overflow-hidden rounded-xl border-2 border-rose-500/30 bg-panel">
          <div className="flex items-center gap-2 border-b border-rose-500/20 bg-rose-500/5 px-4 py-2.5">
            <span className="h-2 w-2 rounded-full bg-rose-500 shadow-[0_0_6px_rgba(244,63,94,0.6)]" />
            <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-rose-400">
              Raw LLM Output (Unprotected)
            </span>
          </div>
          <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
            {isProcessing ? (
              <div className="flex h-full items-center justify-center">
                <div className="flex flex-col items-center gap-3 text-slate-500">
                  <div className="h-6 w-6 animate-spin rounded-full border-2 border-slate-700 border-t-rose-400" />
                  <span className="text-xs uppercase tracking-widest font-bold">Generating unprotected output...</span>
                </div>
              </div>
            ) : rawText ? (
              <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-slate-300">
                {rawText.replace(/\b([A-Z]{2,})\s+\1\b/g, '$1')}
              </pre>
            ) : (
              <div className="flex h-full items-center justify-center">
                <div className="text-center">
                  <FileText className="mx-auto mb-2 h-8 w-8 text-slate-700" />
                  <p className="text-xs uppercase tracking-widest font-bold text-slate-600">
                    Raw output will appear here
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Panel B: Brahmo Safe Output */}
        <div className="flex flex-col overflow-hidden rounded-xl border-2 border-emerald-500/30 bg-panel">
          <div className="flex items-center gap-2 border-b border-emerald-500/20 bg-emerald-500/5 px-4 py-2.5">
            <span className="h-2 w-2 rounded-full bg-emerald-500 shadow-[0_0_6px_rgba(52,211,153,0.6)]" />
            <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-emerald-400">
              Brahmo Safe Output
            </span>
          </div>
          <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
            {isProcessing ? (
              <div className="flex h-full items-center justify-center">
                <div className="flex flex-col items-center gap-3 text-slate-500">
                  <div className="h-6 w-6 animate-spin rounded-full border-2 border-slate-700 border-t-emerald-400" />
                  <span className="text-xs uppercase tracking-widest font-bold">Running safety pipeline...</span>
                </div>
              </div>
            ) : sanitizedHtml ? (
              <div
                className="prose-sm prose-invert max-w-none leading-relaxed text-slate-300"
                dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
              />
            ) : (
              <div className="flex h-full items-center justify-center">
                <div className="text-center">
                  <Search className="mx-auto mb-2 h-8 w-8 text-slate-700" />
                  <p className="text-xs text-slate-600">
                    Verified safe output will appear here
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── RAG Sources Accordion ────────────────────────── */}
      <div className="shrink-0 rounded-xl border border-border-dim bg-panel">
        <button
          onClick={() => setRagExpanded(!ragExpanded)}
          className="flex w-full items-center gap-2 px-4 py-2.5 text-left transition-colors hover:bg-white/[0.02]"
        >
          <Database className="h-3.5 w-3.5 text-cyan-400" />
          <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">
            Retrieved RAG Sources
          </span>
          <span className="ml-1 rounded-full bg-cyan-500/10 px-2 py-0.5 text-[9px] font-bold text-cyan-400">
            {ragChunks.length}
          </span>
          <span className="ml-auto">
            {ragExpanded ? (
              <ChevronUp className="h-3.5 w-3.5 text-slate-600" />
            ) : (
              <ChevronDown className="h-3.5 w-3.5 text-slate-600" />
            )}
          </span>
        </button>

        {ragExpanded && (
          <div className="max-h-48 overflow-y-auto border-t border-border-dim px-4 py-3">
            {ragChunks.length === 0 ? (
              <p className="text-center text-xs text-slate-600">
                No knowledge base chunks retrieved
              </p>
            ) : (
              <div className="space-y-2">
                {ragChunks.map((chunk, i) => {
                  const pct = (chunk.similarity * 100).toFixed(1);
                  const pctNum = chunk.similarity * 100;
                  const barColor =
                    pctNum >= 70
                      ? 'bg-emerald-500'
                      : pctNum >= 50
                      ? 'bg-cyan-500'
                      : 'bg-amber-500';
                  const textColor =
                    pctNum >= 70
                      ? 'text-emerald-400'
                      : pctNum >= 50
                      ? 'text-cyan-400'
                      : 'text-amber-400';

                  return (
                    <div
                      key={chunk.id ?? i}
                      className="flex items-start gap-3 rounded-lg bg-slate-900/50 p-3 border border-border-dim"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-[10px] font-bold text-cyan-400 truncate">
                            {chunk.doc_title}
                          </span>
                          {chunk.metadata &&
                            typeof chunk.metadata === 'object' &&
                            Object.entries(chunk.metadata)
                              .filter(
                                ([k]) => k !== 'doc_id' && k !== 'doc_title'
                              )
                              .slice(0, 2)
                              .map(([key, val]) => (
                                <span
                                  key={key}
                                  className="rounded bg-slate-800 px-1.5 py-0.5 text-[8px] text-slate-500"
                                >
                                  {String(val)}
                                </span>
                              ))}
                        </div>
                        <p className="text-[10px] leading-relaxed text-slate-500 line-clamp-2">
                          {chunk.content}
                        </p>
                      </div>
                      <div className="flex shrink-0 flex-col items-end gap-1">
                        <span className={`text-xs font-black tabular-nums ${textColor}`}>
                          {pct}%
                        </span>
                        <div className="h-1 w-14 overflow-hidden rounded-full bg-slate-800">
                          <div
                            className={`h-full rounded-full ${barColor}`}
                            style={{ width: `${pctNum}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
