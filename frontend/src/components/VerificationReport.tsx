import type { ProcessingReport } from '../types';

interface VerificationReportProps {
  report: ProcessingReport;
}

export default function VerificationReport({ report }: VerificationReportProps) {
  const stats = [
    { label: 'Total', value: report.total_citations, color: 'text-[#e2e8f0]', bg: 'bg-white/5', border: 'border-white/[0.06]' },
    { label: 'Verified', value: report.verified, color: 'text-emerald-400', bg: 'bg-emerald-500/5', border: 'border-emerald-500/15', icon: '✅' },
    { label: 'Corrected', value: report.corrected, color: 'text-amber-400', bg: 'bg-amber-500/5', border: 'border-amber-500/15', icon: '⚠️' },
    { label: 'Unverified', value: report.unverified, color: 'text-orange-400', bg: 'bg-orange-500/5', border: 'border-orange-500/15', icon: '⚠️' },
    { label: 'Removed', value: report.removed, color: 'text-red-400', bg: 'bg-red-500/5', border: 'border-red-500/15', icon: '❌' },
  ];

  const accuracyPct = Math.round(report.accuracy_pct * 10) / 10;

  return (
    <div className="rounded-2xl border border-white/[0.06] bg-[#111827]/80 backdrop-blur-sm overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-white/[0.06] px-6 py-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/10">
          <svg className="h-4 w-4 text-blue-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
            <polyline points="10 9 9 9 8 9" />
          </svg>
        </div>
        <h3 className="text-sm font-bold uppercase tracking-wider text-[#f1f5f9]">
          Citation Verification Report
        </h3>
      </div>

      <div className="p-5 space-y-5">
        {/* Stats grid */}
        <div className="grid grid-cols-5 gap-2">
          {stats.map((s) => (
            <div
              key={s.label}
              className={`flex flex-col items-center rounded-xl border ${s.border} ${s.bg} px-2 py-3 text-center transition-all duration-300 hover:scale-105`}
            >
              <span className={`text-2xl font-black ${s.color}`}>{s.value}</span>
              <span className="mt-1 text-[10px] font-semibold uppercase tracking-wider text-[#64748b]">
                {s.icon ? `${s.icon} ` : ''}{s.label}
              </span>
            </div>
          ))}
        </div>

        {/* Accuracy bar */}
        <div>
          <div className="mb-2 flex items-baseline justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-[#64748b]">Accuracy</span>
            <span className="text-lg font-black text-emerald-400">{accuracyPct}%</span>
          </div>
          <div className="h-3 overflow-hidden rounded-full bg-white/[0.04]">
            <div
              className="h-full rounded-full bg-gradient-to-r from-emerald-600 to-emerald-400 transition-all duration-700 ease-out"
              style={{ width: `${Math.min(accuracyPct, 100)}%` }}
            />
          </div>
        </div>

        {/* API calls */}
        <div className="flex items-center justify-between rounded-xl border border-white/[0.06] bg-white/[0.02] px-4 py-2.5">
          <span className="text-xs font-medium text-[#94a3b8]">Indian Kanoon API Calls</span>
          <span className="font-mono text-sm font-bold text-[#e2e8f0]">{report.api_calls_made}</span>
        </div>
      </div>
    </div>
  );
}
