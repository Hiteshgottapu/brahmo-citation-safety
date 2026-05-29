import { Briefcase, FileText, Zap, Loader2, History } from 'lucide-react';
import type { SessionHistoryItem } from '../types';

const PRACTICE_AREAS = [
  { id: 1, label: 'Anticipatory Bail Application', sample: 'Key SC precedents on anticipatory bail in economic offences' },
  { id: 3, label: 'NDPS Bail Overview', sample: 'Summarize SC approach to bail in NDPS cases over last 5 years' },
  { id: 4, label: 'Section 482 BNSS Scope', sample: 'Key Delhi HC decisions on Section 482 BNSS powers in last 2 years' },
  { id: 2, label: 'Cheating Framework (IPC 420)', sample: 'Draft complaint for cheating under Section 420 IPC with criminal breach of trust under Section 406 IPC' },
  { id: 5, label: 'NDA Indian Law Review', sample: 'Review NDA and flag missing clauses for Indian law' },
  { id: 6, label: 'NCLT Oppression & Mismanagement', sample: 'Grounds for NCLT petition — oppression and mismanagement' },
  { id: 7, label: 'Property Specific Performance', sample: 'Specific performance of immovable property sale agreement' },
  { id: 8, label: 'HMA Divorce Grounds', sample: 'Grounds for contested divorce under Hindu Marriage Act Section 13' },
];

interface ControlPanelProps {
  selectedArea: number;
  onSelectArea: (id: number) => void;
  query: string;
  onQueryChange: (text: string) => void;
  onRunPipeline: () => void;
  isProcessing: boolean;
  sessionHistory?: SessionHistoryItem[];
  onLoadSession?: (item: SessionHistoryItem) => void;
}

export default function ControlPanel({
  selectedArea,
  onSelectArea,
  query,
  onQueryChange,
  onRunPipeline,
  isProcessing,
  sessionHistory,
  onLoadSession,
}: ControlPanelProps) {
  const handleAreaChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const id = Number(e.target.value);
    const area = PRACTICE_AREAS.find((a) => a.id === id);
    onSelectArea(id);
    if (area) onQueryChange(area.sample);
  };

  return (
    <div className="flex h-full flex-col gap-4 overflow-hidden">
      {/* ── Practice Area Selection ─────────────────────── */}
      <div className="panel-card p-4">
        <div className="mb-3 flex items-center gap-2">
          <Briefcase className="h-3.5 w-3.5 text-purple-400" />
          <span className="section-header">Practice Area Selection</span>
        </div>
        <select
          value={selectedArea}
          onChange={handleAreaChange}
          className="w-full rounded-lg border border-border-dim bg-slate-900/60 px-3 py-2.5 text-sm text-slate-200 outline-none transition-colors focus:border-purple-500/50 focus:ring-1 focus:ring-purple-500/20"
        >
          {PRACTICE_AREAS.map((area) => (
            <option key={area.id} value={area.id} className="bg-slate-900">
              {area.label}
            </option>
          ))}
        </select>
      </div>

      {/* ── Query Input ────────────────────────────────── */}
      <div className="panel-card flex flex-1 flex-col overflow-hidden p-4">
        <div className="mb-3 flex items-center gap-2">
          <FileText className="h-3.5 w-3.5 text-purple-400" />
          <span className="section-header">Lawyer Query Input</span>
        </div>
        <textarea
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          placeholder="Enter raw legal brief or query..."
          className="flex-1 resize-none rounded-lg border border-border-dim bg-slate-900/60 p-3 font-mono text-xs leading-relaxed text-slate-300 placeholder-slate-600 outline-none transition-colors focus:border-purple-500/50 focus:ring-1 focus:ring-purple-500/20"
        />
        <div className="mt-2 text-right">
          <span className="text-[10px] tabular-nums text-slate-600">
            {query.length} chars
          </span>
        </div>
      </div>

      {/* ── Run Button ─────────────────────────────────── */}
      <button
        onClick={onRunPipeline}
        disabled={isProcessing || !query.trim()}
        className={`shrink-0 flex w-full items-center justify-center gap-2 rounded-xl py-4 text-sm font-bold uppercase tracking-wider text-white transition-all ${
          isProcessing
            ? 'cursor-wait bg-purple-900/50 text-purple-300'
            : 'bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-500 hover:to-purple-400 hover:shadow-[0_0_20px_rgba(147,51,234,0.4)] active:scale-[0.98]'
        } disabled:opacity-50`}
      >
        {isProcessing ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            Processing Pipeline...
          </>
        ) : (
          <>
            <Zap className="h-4 w-4" />
            Run Verification Pipeline
          </>
        )}
      </button>

      {/* ── Past Runs & Brief History ─────────────────── */}
      {sessionHistory && onLoadSession && (
        <div className="panel-card flex flex-1 flex-col overflow-hidden p-4">
          <div className="mb-3 flex items-center gap-2">
            <History className="h-3.5 w-3.5 text-purple-400" />
            <span className="section-header">🕒 RECENT VERIFICATION HANDLES</span>
          </div>
          <div className="flex-1 overflow-y-auto space-y-2 pr-1 custom-scrollbar">
            {sessionHistory.map((item) => (
              <div 
                key={item.id} 
                onClick={() => onLoadSession(item)}
                className="cursor-pointer rounded-lg bg-slate-900/50 p-3 border border-border-dim hover:border-purple-500/50 transition-colors group"
              >
                <div className="flex justify-between items-start mb-1">
                  <span className="text-[10px] font-bold text-slate-300 uppercase truncate group-hover:text-purple-300 transition-colors">
                    {item.practiceAreaLabel}
                  </span>
                  <span className="text-[9px] text-slate-500 shrink-0 tabular-nums">
                    {new Date(item.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                  </span>
                </div>
                <p className="text-[10px] text-slate-500 truncate mb-2">
                  {item.querySnippet}
                </p>
                <div className="flex gap-1 items-center">
                  {item.stats.verified > 0 && (
                    <div className="h-1.5 flex-1 rounded-full bg-emerald-500/80" title={`Verified: ${item.stats.verified}`} />
                  )}
                  {item.stats.corrected > 0 && (
                    <div className="h-1.5 flex-1 rounded-full bg-amber-500/80" title={`Corrected: ${item.stats.corrected}`} />
                  )}
                  {item.stats.unverified > 0 && (
                    <div className="h-1.5 flex-1 rounded-full bg-slate-500/80" title={`Unverified: ${item.stats.unverified}`} />
                  )}
                  {item.stats.removed > 0 && (
                    <div className="h-1.5 flex-1 rounded-full bg-rose-500/80" title={`Removed: ${item.stats.removed}`} />
                  )}
                  {Object.values(item.stats).every(v => v === 0) && (
                    <div className="h-1.5 flex-1 rounded-full bg-slate-800" title="No citations" />
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

