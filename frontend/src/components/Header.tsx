export default function Header() {
  return (
    <header className="relative overflow-hidden border-b border-white/[0.06]">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-r from-[#0a0e1a] via-[#111827] to-[#0a0e1a]" />
      <div className="absolute inset-0 bg-gradient-to-b from-emerald-500/[0.03] to-transparent" />

      <div className="relative mx-auto max-w-7xl px-6 py-6">
        <div className="flex items-center gap-4">
          {/* Shield icon */}
          <div className="relative flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 ring-1 ring-emerald-500/20">
            <svg
              className="h-8 w-8 text-emerald-400"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              <path d="M9 12l2 2 4-4" />
            </svg>
            <div className="absolute -inset-0.5 rounded-xl bg-emerald-500/10 blur-md" />
          </div>

          <div>
            <h1 className="flex items-baseline gap-3">
              <span className="text-3xl font-black tracking-tight gradient-text-emerald">
                BRAHMO
              </span>
              <span className="hidden sm:inline-block h-5 w-px bg-white/10" />
              <span className="hidden sm:inline text-sm font-medium text-[#94a3b8] tracking-wide uppercase">
                Legal AI Safety
              </span>
            </h1>
            <p className="mt-0.5 text-sm text-[#64748b]">
              Citation Safety Engine & Legal Section Normalizer
            </p>
          </div>

          {/* Right side — decorative gavel */}
          <div className="ml-auto hidden md:flex items-center gap-3">
            <div className="flex items-center gap-2 rounded-full border border-white/[0.06] bg-white/[0.02] px-4 py-1.5">
              <svg className="h-4 w-4 text-emerald-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <rect x="2" y="6" width="20" height="3" rx="1" transform="rotate(-30 12 7.5)" />
                <line x1="6" y1="18" x2="18" y2="18" strokeWidth="2" />
                <line x1="12" y1="12" x2="12" y2="18" strokeWidth="1.5" />
              </svg>
              <span className="text-xs font-medium text-[#94a3b8]">Deterministic Verification</span>
            </div>
            <div className="flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/5 px-4 py-1.5">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs font-medium text-emerald-400">Engine Active</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
