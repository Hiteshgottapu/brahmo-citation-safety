import type { ProcessLegalQueryResponse } from '../types';

interface ResponseComparisonProps {
  genericResponse: ProcessLegalQueryResponse | null;
  verifiedResponse: ProcessLegalQueryResponse | null;
  isLoadingGeneric: boolean;
  isLoadingVerified: boolean;
}

function Skeleton() {
  return (
    <div className="space-y-4 p-6">
      {[100, 85, 92, 60, 95, 78, 88, 70].map((w, i) => (
        <div
          key={i}
          className="skeleton-shimmer h-4 rounded"
          style={{ width: `${w}%` }}
        />
      ))}
    </div>
  );
}

function EmptyPanel({ label }: { label: string }) {
  return (
    <div className="flex h-full min-h-[300px] items-center justify-center p-8 text-center">
      <div>
        <svg className="mx-auto mb-3 h-10 w-10 text-[#334155]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <rect x="3" y="3" width="18" height="18" rx="2" />
          <path d="M3 9h18M9 21V9" />
        </svg>
        <p className="text-sm text-[#475569]">{label}</p>
      </div>
    </div>
  );
}

export default function ResponseComparison({
  genericResponse,
  verifiedResponse,
  isLoadingGeneric,
  isLoadingVerified,
}: ResponseComparisonProps) {
  return (
    <section className="grid gap-0 overflow-hidden rounded-2xl border border-white/[0.06] lg:grid-cols-2">
      {/* ── Left: Generic AI ──────────────────────────────── */}
      <div className="border-b border-white/[0.06] lg:border-b-0 lg:border-r">
        {/* Header */}
        <div className="flex items-center gap-2 border-b border-white/[0.06] bg-[#111827] px-5 py-3">
          <span className="h-2 w-2 rounded-full bg-[#64748b]" />
          <span className="text-xs font-bold uppercase tracking-widest text-[#64748b]">
            Generic AI Response
          </span>
          <span className="ml-auto text-[10px] text-[#475569]">No verification</span>
        </div>

        {/* Body */}
        <div className="bg-[#0d1117] min-h-[300px]">
          {isLoadingGeneric ? (
            <Skeleton />
          ) : genericResponse ? (
            <div className="p-5">
              <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-[#cbd5e1]">
                {genericResponse.raw_text}
              </pre>
            </div>
          ) : (
            <EmptyPanel label="Click 'Ask Generic AI' to see the raw AI response" />
          )}
        </div>
      </div>

      {/* ── Right: Verified & Safe ────────────────────────── */}
      <div>
        {/* Header */}
        <div className="flex items-center gap-2 border-b border-white/[0.06] bg-[#111827] px-5 py-3">
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-xs font-bold uppercase tracking-widest text-emerald-400">
            Verified &amp; Safe Response
          </span>
          <span className="ml-auto text-[10px] text-emerald-500/60">Citation Safety Engine Active</span>
        </div>

        {/* Body */}
        <div className="bg-[#0d1117] min-h-[300px]">
          {isLoadingVerified ? (
            <Skeleton />
          ) : verifiedResponse ? (
            <div className="p-5">
              {verifiedResponse.annotated_nodes && verifiedResponse.annotated_nodes.length > 0 ? (
                <div className="annotated-nodes-container prose-sm prose-invert max-w-none leading-relaxed text-[#cbd5e1]">
                  {verifiedResponse.annotated_nodes.map((node, i) => {
                    if (node.type === 'text') {
                      return <span key={i} className="whitespace-pre-wrap">{node.content}</span>;
                    }
                    if (node.type === 'heading') {
                      return <div key={i} className="font-bold my-2">{node.content}</div>;
                    }
                    if (node.type === 'strong') {
                      return <strong key={i} className="font-bold">{node.content}</strong>;
                    }
                    if (node.type === 'badge') {
                      return (
                        <span key={i} className={`citation-${node.variant}`}>
                          {node.content} <span className={`badge badge-${node.variant}`}>
                            {node.variant === 'verified' ? '✅ VERIFIED' : node.variant === 'removed' ? '❌ REMOVED' : '⚠️ ' + node.variant.toUpperCase()}
                          </span>
                        </span>
                      );
                    }
                    return null;
                  })}
                </div>
              ) : (
                <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-[#cbd5e1]">
                  {verifiedResponse.annotated_text || verifiedResponse.raw_text}
                </pre>
              )}
            </div>
          ) : (
            <EmptyPanel label="Click 'Ask with Citation Verification' to see the verified output" />
          )}
        </div>
      </div>
    </section>
  );
}
