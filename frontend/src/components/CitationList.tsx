import { useState } from 'react';
import type { CitationResult } from '../types';

interface CitationListProps {
  citations: CitationResult[];
}

const STATUS_CONFIG: Record<string, {
  emoji: string;
  label: string;
  textColor: string;
  bgColor: string;
  borderColor: string;
  glowClass: string;
}> = {
  REMOVED: {
    emoji: '❌', label: 'REMOVED',
    textColor: 'text-red-400', bgColor: 'bg-red-500/5', borderColor: 'border-red-500/15', glowClass: 'glow-red',
  },
  CORRECTED: {
    emoji: '⚠️', label: 'CORRECTED',
    textColor: 'text-amber-400', bgColor: 'bg-amber-500/5', borderColor: 'border-amber-500/15', glowClass: 'glow-amber',
  },
  UNVERIFIED: {
    emoji: '⚠️', label: 'UNVERIFIED',
    textColor: 'text-orange-400', bgColor: 'bg-orange-500/5', borderColor: 'border-orange-500/15', glowClass: 'glow-orange',
  },
  VERIFIED: {
    emoji: '✅', label: 'VERIFIED',
    textColor: 'text-emerald-400', bgColor: 'bg-emerald-500/5', borderColor: 'border-emerald-500/15', glowClass: 'glow-green',
  },
};

const STATUS_ORDER = ['REMOVED', 'CORRECTED', 'UNVERIFIED', 'VERIFIED'];

function CitationCard({ result }: { result: CitationResult }) {
  const config = STATUS_CONFIG[result.status] ?? STATUS_CONFIG.UNVERIFIED;

  return (
    <div className={`rounded-xl border ${config.borderColor} ${config.bgColor} px-4 py-3 transition-all duration-300 hover:scale-[1.01]`}>
      <div className="flex items-start gap-3">
        <span className="text-lg leading-none mt-0.5">{config.emoji}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`font-mono text-sm font-semibold ${
              result.status === 'REMOVED' ? 'line-through text-red-400/60' : config.textColor
            }`}>
              {result.original_text}
            </span>
            <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${config.textColor} ${config.bgColor} border ${config.borderColor}`}>
              {config.label}
            </span>
          </div>

          {result.case_name && (
            <p className="mt-1 text-xs text-[#94a3b8]">
              <span className="text-[#64748b]">Case:</span> {result.case_name}
            </p>
          )}
          {result.correction_note && (
            <p className="mt-1 text-xs italic text-amber-400/70">
              {result.correction_note}
            </p>
          )}
          {result.reason && (
            <p className="mt-1 text-xs italic text-red-400/70">
              {result.reason}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export default function CitationList({ citations }: CitationListProps) {
  const [showVerified, setShowVerified] = useState(false);

  if (citations.length === 0) return null;

  // Group by status in priority order
  const grouped: Record<string, CitationResult[]> = {};
  for (const s of STATUS_ORDER) {
    grouped[s] = citations.filter((c) => c.status === s);
  }

  const verifiedCount = grouped.VERIFIED.length;
  const problemCitations = [
    ...grouped.REMOVED,
    ...grouped.CORRECTED,
    ...grouped.UNVERIFIED,
  ];

  return (
    <div className="rounded-2xl border border-white/[0.06] bg-[#111827]/80 backdrop-blur-sm overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-white/[0.06] px-6 py-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500/10">
          <svg className="h-4 w-4 text-indigo-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M4 6h16M4 10h16M4 14h16M4 18h16" />
          </svg>
        </div>
        <h3 className="text-sm font-bold uppercase tracking-wider text-[#f1f5f9]">
          Citation Details
        </h3>
        <span className="ml-auto text-xs text-[#64748b]">
          {citations.length} citation{citations.length !== 1 ? 's' : ''} found
        </span>
      </div>

      <div className="p-5 space-y-3">
        {/* Problem citations — always visible */}
        {problemCitations.map((c, i) => (
          <CitationCard key={`problem-${i}`} result={c} />
        ))}

        {/* Verified citations — collapsible */}
        {verifiedCount > 0 && (
          <>
            <button
              onClick={() => setShowVerified(!showVerified)}
              className="flex w-full items-center gap-3 rounded-xl border border-emerald-500/10 bg-emerald-500/[0.03] px-4 py-3 text-left transition-all duration-300 hover:bg-emerald-500/[0.06] cursor-pointer"
            >
              <span className="text-sm">✅</span>
              <span className="text-sm font-medium text-emerald-400">
                {verifiedCount} citation{verifiedCount !== 1 ? 's' : ''} verified
              </span>
              <svg
                className={`ml-auto h-4 w-4 text-emerald-400 transition-transform duration-300 ${showVerified ? 'rotate-180' : ''}`}
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </button>

            {showVerified && (
              <div className="space-y-2 pl-2">
                {grouped.VERIFIED.map((c, i) => (
                  <CitationCard key={`verified-${i}`} result={c} />
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
