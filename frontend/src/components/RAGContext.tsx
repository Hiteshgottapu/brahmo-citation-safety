import { useState } from 'react';
import type { RAGContext as RAGContextType } from '../types';

interface RAGContextProps {
  context: RAGContextType;
}

export default function RAGContext({ context }: RAGContextProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!context.chunks.length) return null;

  return (
    <div className="rounded-2xl border border-white/[0.06] bg-[#111827]/80 backdrop-blur-sm overflow-hidden">
      {/* Header — always visible */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex w-full items-center gap-3 border-b border-white/[0.06] px-6 py-4 text-left transition-all duration-300 hover:bg-white/[0.02] cursor-pointer"
      >
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-cyan-500/10">
          <svg className="h-4 w-4 text-cyan-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
        </div>
        <div className="flex-1">
          <h3 className="text-sm font-bold uppercase tracking-wider text-[#f1f5f9]">
            Retrieved Knowledge Sources
          </h3>
          <p className="text-[11px] text-[#64748b]">
            {context.chunks.length} chunk{context.chunks.length !== 1 ? 's' : ''} retrieved
            {' · '}
            {context.retrieval_time_ms.toFixed(0)}ms
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="rounded-full bg-cyan-500/10 px-3 py-0.5 text-xs font-bold text-cyan-400 border border-cyan-500/20">
            RAG
          </span>
          <svg
            className={`h-4 w-4 text-[#64748b] transition-transform duration-300 ${isExpanded ? 'rotate-180' : ''}`}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </div>
      </button>

      {/* Expanded content */}
      {isExpanded && (
        <div className="p-5 space-y-3">
          {context.chunks.map((chunk, i) => {
            const pct = Math.round(chunk.similarity * 100);
            const barColor =
              pct >= 70 ? 'bg-emerald-500' :
              pct >= 50 ? 'bg-cyan-500' :
              'bg-amber-500';

            return (
              <div
                key={chunk.id ?? i}
                className="group rounded-xl border border-white/[0.06] bg-[#0d1117] p-4 transition-all duration-300 hover:border-cyan-500/20"
              >
                {/* Chunk header */}
                <div className="mb-2 flex items-center gap-3">
                  <span className="inline-flex items-center gap-1.5 rounded-md bg-cyan-500/10 px-2 py-0.5 text-[10px] font-bold text-cyan-400 border border-cyan-500/15">
                    <svg className="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                      <polyline points="14 2 14 8 20 8" />
                    </svg>
                    {chunk.doc_title}
                  </span>

                  {/* Similarity bar */}
                  <div className="ml-auto flex items-center gap-2">
                    <div className="h-1.5 w-16 overflow-hidden rounded-full bg-white/[0.06]">
                      <div
                        className={`h-full rounded-full ${barColor} transition-all duration-500`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <span className="text-[10px] font-mono font-bold text-[#94a3b8]">
                      {pct}%
                    </span>
                  </div>
                </div>

                {/* Chunk content — truncated preview */}
                <p className="text-xs leading-relaxed text-[#94a3b8] line-clamp-4">
                  {chunk.content}
                </p>

                {/* Metadata tags */}
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {chunk.metadata && typeof chunk.metadata === 'object' && Object.entries(chunk.metadata)
                    .filter(([k]) => k !== 'doc_id' && k !== 'doc_title')
                    .map(([key, value]) => (
                      <span
                        key={key}
                        className="rounded-full bg-white/[0.04] px-2 py-0.5 text-[9px] font-medium text-[#64748b]"
                      >
                        {key}: {String(value)}
                      </span>
                    ))
                  }
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
