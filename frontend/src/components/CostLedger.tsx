import type { CostMetrics } from '../types';

interface CostLedgerProps {
  costMetrics: CostMetrics;
}

function fmt(n: number): string {
  return n.toFixed(2);
}

export default function CostLedger({ costMetrics }: CostLedgerProps) {
  const netCost = costMetrics.total_cost - costMetrics.savings_from_prefilter - costMetrics.savings_from_cache;
  const totalSavings = costMetrics.savings_from_prefilter + costMetrics.savings_from_cache;

  return (
    <div className="rounded-2xl border border-white/[0.06] bg-[#111827]/80 backdrop-blur-sm overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-white/[0.06] px-6 py-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-500/10">
          <svg className="h-4 w-4 text-purple-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="1" x2="12" y2="23" />
            <path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6" />
          </svg>
        </div>
        <h3 className="text-sm font-bold uppercase tracking-wider text-[#f1f5f9]">
          Financial Cost Ledger
        </h3>
      </div>

      <div className="p-5">
        <table className="w-full text-sm">
          <tbody className="divide-y divide-white/[0.04]">
            {/* Search calls */}
            <tr>
              <td className="py-2.5 text-[#94a3b8]">Search API calls</td>
              <td className="py-2.5 text-right font-mono text-[#cbd5e1]">
                {costMetrics.total_searches} × ₹0.50
              </td>
              <td className="py-2.5 text-right font-mono font-semibold text-[#e2e8f0] w-24">
                ₹{fmt(costMetrics.total_searches * 0.5)}
              </td>
            </tr>

            {/* DocMeta calls */}
            <tr>
              <td className="py-2.5 text-[#94a3b8]">DocMeta API calls</td>
              <td className="py-2.5 text-right font-mono text-[#cbd5e1]">
                {costMetrics.total_docmeta} × ₹0.30
              </td>
              <td className="py-2.5 text-right font-mono font-semibold text-[#e2e8f0] w-24">
                ₹{fmt(costMetrics.total_docmeta * 0.3)}
              </td>
            </tr>

            {/* Total cost */}
            <tr className="border-t border-white/[0.08]">
              <td className="py-2.5 font-semibold text-[#e2e8f0]" colSpan={2}>Total API Cost</td>
              <td className="py-2.5 text-right font-mono font-bold text-[#e2e8f0] w-24">
                ₹{fmt(costMetrics.total_cost)}
              </td>
            </tr>

            {/* Savings */}
            {costMetrics.savings_from_prefilter > 0 && (
              <tr>
                <td className="py-2.5 text-emerald-400" colSpan={2}>
                  💡 Saved by Pre-filter
                </td>
                <td className="py-2.5 text-right font-mono font-semibold text-emerald-400 w-24">
                  −₹{fmt(costMetrics.savings_from_prefilter)}
                </td>
              </tr>
            )}
            {costMetrics.savings_from_cache > 0 && (
              <tr>
                <td className="py-2.5 text-emerald-400" colSpan={2}>
                  💡 Saved by Cache
                </td>
                <td className="py-2.5 text-right font-mono font-semibold text-emerald-400 w-24">
                  −₹{fmt(costMetrics.savings_from_cache)}
                </td>
              </tr>
            )}

            {/* Net cost */}
            <tr className="border-t-2 border-white/[0.1]">
              <td className="pt-3 pb-1 text-sm font-bold text-[#f1f5f9]" colSpan={2}>
                Net Cost
              </td>
              <td className="pt-3 pb-1 text-right font-mono text-lg font-black text-emerald-400 w-24">
                ₹{fmt(Math.max(0, netCost))}
              </td>
            </tr>
          </tbody>
        </table>

        {/* Savings highlight */}
        {totalSavings > 0 && (
          <div className="mt-4 rounded-xl border border-emerald-500/15 bg-emerald-500/5 px-4 py-2.5 text-center">
            <span className="text-xs font-semibold text-emerald-400">
              🎯 Total savings: ₹{fmt(totalSavings)} saved by skipping unnecessary API calls
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
