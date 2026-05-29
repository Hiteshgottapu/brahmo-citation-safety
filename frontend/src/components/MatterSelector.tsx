import type { LegalMatter } from '../types';

interface MatterSelectorProps {
  matters: LegalMatter[];
  selectedId: number | null;
  onSelect: (matter: LegalMatter) => void;
}

const PRACTICE_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  Criminal: { bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500/20' },
  Corporate: { bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/20' },
  Property: { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/20' },
  Family: { bg: 'bg-purple-500/10', text: 'text-purple-400', border: 'border-purple-500/20' },
};

export default function MatterSelector({ matters, selectedId, onSelect }: MatterSelectorProps) {
  const selected = matters.find((m) => m.id === selectedId) ?? null;
  const colors = selected ? PRACTICE_COLORS[selected.practice] ?? PRACTICE_COLORS.Criminal : null;

  return (
    <div className="space-y-3">
      <label className="block text-xs font-semibold uppercase tracking-wider text-[#64748b]">
        Legal Matter
      </label>

      <div className="relative">
        <select
          value={selectedId ?? ''}
          onChange={(e) => {
            const matter = matters.find((m) => m.id === Number(e.target.value));
            if (matter) onSelect(matter);
          }}
          className="w-full appearance-none rounded-xl border border-white/[0.06] bg-[#111827] px-4 py-3.5 pr-10 text-sm font-medium text-[#f1f5f9] outline-none transition-all duration-300 hover:border-emerald-500/30 focus:border-emerald-500/40 focus:ring-2 focus:ring-emerald-500/10 cursor-pointer"
        >
          <option value="" disabled>
            Select a legal matter...
          </option>
          {matters.map((m) => (
            <option key={m.id} value={m.id} className="bg-[#111827]">
              {m.title}
            </option>
          ))}
        </select>

        {/* Custom dropdown arrow */}
        <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2">
          <svg className="h-5 w-5 text-[#64748b]" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clipRule="evenodd" />
          </svg>
        </div>
      </div>

      {/* Selected matter details */}
      {selected && colors && (
        <div className="flex flex-wrap items-center gap-2 animate-[fadeIn_0.3s_ease-out]">
          <span
            className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold ${colors.bg} ${colors.text} ${colors.border}`}
          >
            <span className="h-1.5 w-1.5 rounded-full bg-current" />
            {selected.practice}
          </span>
          <span className="inline-flex items-center gap-1.5 rounded-full border border-white/[0.06] bg-white/[0.03] px-3 py-1 text-xs font-medium text-[#94a3b8]">
            <svg className="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 21h18M3 10h18M5 6l7-3 7 3M4 10v11M20 10v11M8 14v3M12 14v3M16 14v3" />
            </svg>
            {selected.court}
          </span>
        </div>
      )}
    </div>
  );
}
