import type { SectionAlert } from '../types';

interface SectionAlertsProps {
  alerts: SectionAlert[];
}

export default function SectionAlerts({ alerts }: SectionAlertsProps) {
  return (
    <div className="rounded-2xl border border-white/[0.06] bg-[#111827]/80 backdrop-blur-sm overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-white/[0.06] px-6 py-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/10">
          <svg className="h-4.5 w-4.5 text-amber-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
        </div>
        <div>
          <h3 className="text-sm font-bold uppercase tracking-wider text-[#f1f5f9]">
            Statutory Modernization Alerts
          </h3>
          <p className="text-[11px] text-[#64748b]">Repealed law references auto-converted to current statutes</p>
        </div>
        {alerts.length > 0 && (
          <span className="ml-auto rounded-full bg-amber-500/10 px-3 py-0.5 text-xs font-bold text-amber-400 border border-amber-500/20">
            {alerts.length} {alerts.length === 1 ? 'alert' : 'alerts'}
          </span>
        )}
      </div>

      {/* Body */}
      <div className="p-5">
        {alerts.length === 0 ? (
          <div className="flex items-center gap-3 rounded-xl border border-emerald-500/10 bg-emerald-500/5 px-5 py-4">
            <svg className="h-5 w-5 text-emerald-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 11.08V12a10 10 0 11-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" />
            </svg>
            <span className="text-sm font-medium text-emerald-400">
              No outdated statutory references detected — all sections are current
            </span>
          </div>
        ) : (
          <div className="space-y-3">
            {alerts.map((alert, i) => (
              <div
                key={i}
                className="group flex items-start gap-4 rounded-xl border border-amber-500/10 bg-amber-500/[0.03] px-5 py-3.5 transition-all duration-300 hover:border-amber-500/20 hover:bg-amber-500/[0.06]"
              >
                {/* Conversion arrow */}
                <div className="mt-0.5 flex flex-col items-center gap-1">
                  <span className="text-[10px] font-semibold uppercase text-red-400/80">Old</span>
                  <svg className="h-4 w-4 text-amber-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="12" y1="5" x2="12" y2="19" />
                    <polyline points="19 12 12 19 5 12" />
                  </svg>
                  <span className="text-[10px] font-semibold uppercase text-emerald-400/80">New</span>
                </div>

                {/* Text */}
                <div className="flex-1 space-y-1.5">
                  <div className="flex items-center gap-3">
                    <span className="rounded-md bg-red-500/10 px-2.5 py-1 font-mono text-xs font-semibold text-red-400 border border-red-500/15">
                      {alert.old_text}
                    </span>
                    <svg className="h-3.5 w-3.5 text-[#475569]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <line x1="5" y1="12" x2="19" y2="12" />
                      <polyline points="12 5 19 12 12 19" />
                    </svg>
                    <span className="rounded-md bg-emerald-500/10 px-2.5 py-1 font-mono text-xs font-semibold text-emerald-400 border border-emerald-500/15">
                      {alert.new_text}
                    </span>
                  </div>
                  <p className="text-[11px] text-[#64748b]">
                    {alert.old_act} → {alert.new_act}
                    <span className="ml-2 text-amber-400/50">(effective July 1, 2024)</span>
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
