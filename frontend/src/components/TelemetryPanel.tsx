import { BarChart3, AlertTriangle, Wallet, BookOpen } from 'lucide-react';
import type { ProcessingReport, SectionAlert, HistoricCitationMetric } from '../types';

interface TelemetryPanelProps {
  report: ProcessingReport | null;
  sectionAlerts: SectionAlert[];
  isProcessing: boolean;
  historicCitations?: HistoricCitationMetric[];
}

export default function TelemetryPanel({
  report,
  sectionAlerts,
  isProcessing,
  historicCitations,
}: TelemetryPanelProps) {
  const cost = report?.cost_metrics;
  const total = report?.total_citations ?? 0;
  const verified = report?.verified ?? 0;
  const corrected = report?.corrected ?? 0;
  const unverified = report?.unverified ?? 0;
  const removed = report?.removed ?? 0;

  // Proportions for segmented bar
  const pVerified = total > 0 ? (verified / total) * 100 : 0;
  const pCorrected = total > 0 ? (corrected / total) * 100 : 0;
  const pUnverified = total > 0 ? (unverified / total) * 100 : 0;
  const pRemoved = total > 0 ? (removed / total) * 100 : 0;

  // Cost computations matching backend CostMetrics model
  const totalApiCalls = (cost?.total_searches ?? 0) + (cost?.total_docmeta ?? 0);
  const savedInr = (cost?.savings_from_prefilter ?? 0) + (cost?.savings_from_cache ?? 0);
  const billedInr = cost?.total_cost ?? 0;

  return (
    <div className="flex h-full flex-col gap-3 overflow-hidden">
      {/* ── 1. Citation Analysis Stats ──────────────────── */}
      <div className="panel-card p-4">
        <div className="mt-4 mb-2 flex items-center gap-2">
          <BarChart3 className="h-3.5 w-3.5 text-blue-400" />
          <span className="section-header uppercase tracking-wider">Citation Analysis Stats</span>
        </div>

        <div className="grid grid-cols-3 gap-3 mb-3">
          <div className="rounded-lg bg-slate-900/50 p-2.5 text-center">
            <div className="stat-value text-white">
              {report ? total : '—'}
            </div>
            <div className="mt-0.5 text-[9px] font-medium uppercase tracking-wider text-slate-500">
              Extracted
            </div>
          </div>
          <div className="rounded-lg bg-slate-900/50 p-2.5 text-center">
            <div className="stat-value text-emerald-400">
              {report ? `${report.accuracy_pct.toFixed(0)}%` : '—'}
            </div>
            <div className="mt-0.5 text-[9px] font-medium uppercase tracking-wider text-slate-500">
              Accuracy
            </div>
          </div>
          <div className="rounded-lg bg-slate-900/50 p-2.5 text-center">
            <div className="stat-value text-rose-400">
              {report ? removed : '—'}
            </div>
            <div className="mt-0.5 text-[9px] font-medium uppercase tracking-wider text-slate-500">
              Removed
            </div>
          </div>
        </div>

        {/* Segmented progress bar */}
        <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800 flex">
          {total > 0 ? (
            <>
              <div className="h-full bg-emerald-500 transition-all" style={{ width: `${pVerified}%` }} />
              <div className="h-full bg-amber-500 transition-all" style={{ width: `${pCorrected}%` }} />
              <div className="h-full bg-slate-500 transition-all" style={{ width: `${pUnverified}%` }} />
              <div className="h-full bg-rose-500 transition-all" style={{ width: `${pRemoved}%` }} />
            </>
          ) : (
            <div className="h-full w-full bg-slate-800" />
          )}
        </div>
        <div className="mt-1.5 flex justify-between text-[8px] font-medium text-slate-600">
          <span className="flex items-center gap-1"><span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />Verified</span>
          <span className="flex items-center gap-1"><span className="h-1.5 w-1.5 rounded-full bg-amber-500" />Corrected</span>
          <span className="flex items-center gap-1"><span className="h-1.5 w-1.5 rounded-full bg-slate-500" />Pending</span>
          <span className="flex items-center gap-1"><span className="h-1.5 w-1.5 rounded-full bg-rose-500" />Removed</span>
        </div>
      </div>
{/* ── 2. Statutory Section Alerts ─────────────────── */}
      <div className="panel-card flex-1 flex flex-col overflow-hidden p-4">
        <div className="mt-4 mb-2 flex items-center gap-2">
          <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />
          <span className="section-header uppercase tracking-wider">Statutory Section Alerts</span>
          {sectionAlerts.length > 0 && (
            <span className="rounded-full bg-amber-500/10 px-2 py-0.5 text-[9px] font-bold text-amber-400">
              {sectionAlerts.length}
            </span>
          )}
        </div>

        <div className="flex-1 overflow-y-auto space-y-1.5 custom-scrollbar pr-1">
          {sectionAlerts.length === 0 ? (
            <div className="flex h-full items-center justify-center">
              <p className="text-xs text-slate-600">
                {isProcessing ? 'Analyzing...' : 'No section alerts'}
              </p>
            </div>
          ) : (
            sectionAlerts.map((alert, i) => {
              const sanitizeAcronyms = (str: string) => str.replace(/\b([A-Z]{2,})\s+\1\b/g, '$1');
              return (
                <div
                  key={i}
                  className="flex items-center gap-2 rounded-lg bg-slate-900/50 px-3 py-2 border border-border-dim animate-slide-up"
                >
                  <span className="text-[11px] font-mono font-medium text-rose-400 line-through truncate">
                    {sanitizeAcronyms(`${alert.old_text} ${alert.old_act}`)}
                  </span>
                  <span className="text-slate-600 shrink-0">➔</span>
                  <span className="text-[11px] font-mono font-medium text-emerald-400 truncate">
                    {sanitizeAcronyms(`${alert.new_text} ${alert.new_act}`)}
                  </span>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* ── 3. Global Citation Audit Ledger ─────────────────── */}
      {historicCitations && (
        <div className="panel-card flex-1 flex flex-col overflow-hidden p-4">
          <div className="mt-4 mb-2 flex items-center gap-2">
            <BookOpen className="h-3.5 w-3.5 text-blue-400" />
            <span className="section-header uppercase tracking-wider">📚 HISTORIC PRECEDENT TELEMETRY</span>
          </div>
          <div className="flex-1 overflow-y-auto space-y-1.5 custom-scrollbar pr-1">
            {historicCitations.map((cit) => (
              <div key={cit.id} className="flex flex-col gap-1 rounded-lg bg-slate-900/50 px-3 py-2 border border-border-dim">
                <div className="flex justify-between items-center">
                  <span className="text-[11px] font-mono font-medium text-slate-200 truncate pr-2">
                    {cit.citationText}
                  </span>
                  <span className="text-[10px] font-bold text-slate-400 tabular-nums shrink-0">
                    x{cit.frequency}
                  </span>
                </div>
                <div className="flex justify-between items-center mt-0.5">
                  <span className={`text-[9px] font-bold tracking-wider px-1.5 py-0.5 rounded-sm ${
                    cit.status === 'VERIFIED' ? 'bg-emerald-500/20 text-emerald-400' :
                    cit.status === 'CORRECTED' ? 'bg-amber-500/20 text-amber-400' :
                    cit.status === 'UNVERIFIED' ? 'bg-slate-500/20 text-slate-400' :
                    'bg-rose-500/20 text-rose-400'
                  }`}>
                    {cit.status}
                  </span>
                  <span className="text-[10px] font-medium text-emerald-400 tabular-nums">
                    ₹{cit.savings.toFixed(2)} Saved
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── 4. API Budget & Ledger ─────────────────────── */}
      <div className="panel-card p-4">
        <div className="mt-4 mb-2 flex items-center gap-2">
          <Wallet className="h-3.5 w-3.5 text-emerald-400" />
          <span className="section-header uppercase tracking-wider">API Budget & Ledger</span>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between rounded-lg bg-slate-900/50 px-3 py-2">
            <span className="text-[10px] uppercase tracking-wider text-slate-500">Live Queries</span>
            <span className="text-sm font-bold tabular-nums text-white">
              {totalApiCalls}
            </span>
          </div>
          <div className="flex items-center justify-between rounded-lg bg-slate-900/50 px-3 py-2">
            <span className="text-[10px] uppercase tracking-wider text-slate-500">Searches</span>
            <span className="text-sm font-bold tabular-nums text-cyan-400">
              {cost?.total_searches ?? 0}
            </span>
          </div>
          <div className="flex items-center justify-between rounded-lg bg-slate-900/50 px-3 py-2">
            <span className="text-[10px] uppercase tracking-wider text-slate-500">System Savings</span>
            <span className="text-sm font-bold tabular-nums text-emerald-400">
              ₹{savedInr.toFixed(2)}
            </span>
          </div>

          {/* Prominent NET BILLED */}
          <div className="flex items-center justify-between rounded-xl border border-amber-500/20 bg-amber-500/5 px-4 py-3">
            <span className="text-[10px] font-bold uppercase tracking-[0.15em] text-amber-400">
              Net Billed
            </span>
            <span className="text-xl font-black tabular-nums text-amber-400">
              ₹{billedInr.toFixed(2)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

