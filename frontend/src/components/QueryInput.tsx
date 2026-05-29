interface QueryInputProps {
  query: string;
  setQuery: (q: string) => void;
  onSubmitGeneric: () => void;
  onSubmitVerified: () => void;
  isLoadingGeneric: boolean;
  isLoadingVerified: boolean;
}

export default function QueryInput({
  query,
  setQuery,
  onSubmitGeneric,
  onSubmitVerified,
  isLoadingGeneric,
  isLoadingVerified,
}: QueryInputProps) {
  const isAnyLoading = isLoadingGeneric || isLoadingVerified;
  const isEmpty = !query.trim();

  return (
    <div className="flex flex-col gap-4">
      <label className="block text-xs font-semibold uppercase tracking-wider text-[#64748b]">
        Legal Query
      </label>

      <textarea
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        rows={4}
        placeholder="Enter your legal question or select a matter above..."
        className="w-full resize-none rounded-xl border border-white/[0.06] bg-[#0a0e1a] px-4 py-3.5 font-sans text-sm leading-relaxed text-[#e2e8f0] placeholder-[#475569] outline-none transition-all duration-300 hover:border-emerald-500/20 focus:border-emerald-500/40 focus:ring-2 focus:ring-emerald-500/10"
      />

      <div className="flex flex-wrap gap-3">
        {/* Generic AI button */}
        <button
          onClick={onSubmitGeneric}
          disabled={isEmpty || isAnyLoading}
          className="group relative inline-flex items-center gap-2 rounded-xl border border-white/[0.08] bg-white/[0.03] px-5 py-2.5 text-sm font-semibold text-[#94a3b8] transition-all duration-300 hover:border-white/[0.15] hover:bg-white/[0.06] hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
        >
          {isLoadingGeneric ? (
            <>
              <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Processing…
            </>
          ) : (
            <>
              <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
              </svg>
              Ask Generic AI
            </>
          )}
        </button>

        {/* Verified button */}
        <button
          onClick={onSubmitVerified}
          disabled={isEmpty || isAnyLoading}
          className="group relative inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-500 px-6 py-2.5 text-sm font-semibold text-white shadow-lg shadow-emerald-500/20 transition-all duration-300 hover:shadow-emerald-500/30 hover:brightness-110 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40 disabled:shadow-none"
        >
          {isLoadingVerified ? (
            <>
              <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Verifying Citations…
            </>
          ) : (
            <>
              <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                <path d="M9 12l2 2 4-4" />
              </svg>
              Ask with Citation Verification
            </>
          )}
        </button>
      </div>
    </div>
  );
}
