import { useEffect, useState } from 'react';
import './index.css';

import { Shield, Download, Activity } from 'lucide-react';
import ControlPanel from './components/ControlPanel';
import OutputComparison from './components/OutputComparison';
import TelemetryPanel from './components/TelemetryPanel';

import { fetchSessionHistory, saveSessionHistory, processLegalQuery, fetchLegalMatters } from './api';
import type { ProcessLegalQueryResponse, SessionHistoryItem, HistoricCitationMetric, ResponseNode, LegalMatter } from './types';

const MOCK_CITATIONS: HistoricCitationMetric[] = [
  { id: 'c1', citationText: 'AIR 2014 SC 273', frequency: 12, status: 'VERIFIED', savings: 9.60 },
  { id: 'c2', citationText: '(2021) 10 SCC 1', frequency: 8, status: 'CORRECTED', savings: 6.40 },
  { id: 'c3', citationText: 'MANU/SC/0123/2024', frequency: 3, status: 'UNVERIFIED', savings: 0.00 },
  { id: 'c4', citationText: '(2028) 3 SCC 45', frequency: 5, status: 'REMOVED', savings: 4.00 }
];


export default function App() {
  /* ── state ──────────────────────────────────────────────── */
  const [selectedArea, setSelectedArea] = useState(1);
  const [query, setQuery] = useState(
    'Key SC precedents on anticipatory bail in economic offences'
  );

  const [isProcessing, setIsProcessing] = useState(false);
  const [genericResponse, setGenericResponse] =
    useState<ProcessLegalQueryResponse | null>(null);
  const [verifiedResponse, setVerifiedResponse] =
    useState<ProcessLegalQueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [apiConnected, setApiConnected] = useState<boolean | null>(null);

  const [sessionHistory, setSessionHistory] = useState<SessionHistoryItem[]>([]);
  const [historicCitations, setHistoricCitations] = useState<HistoricCitationMetric[]>(MOCK_CITATIONS);
  const [legalMatters, setLegalMatters] = useState<LegalMatter[]>([]);

  /* ── check backend & database on mount ─────────────────────────────── */
  useEffect(() => {
    fetchLegalMatters().then(setLegalMatters);
    fetch('http://localhost:8000/health')
      .then(async (r) => {
        if (r.ok) {
          const data = await r.json();
          // Explicitly rely on Supabase DB connection flag
          setApiConnected(data.db_connected === true);
        } else {
          setApiConnected(false);
        }
      })
      .catch(() => setApiConnected(false));
      
    // Fetch live session history from database
    fetchSessionHistory().then((data: any[]) => {
      const history: SessionHistoryItem[] = data.map((row) => ({
        id: row.id,
        practiceAreaId: 1, // Fallback default
        practiceAreaLabel: row.practice_area,
        querySnippet: row.query_snippet,
        fullQuery: row.cached_query,
        timestamp: row.created_at,
        stats: row.badge_counts || { verified: 0, corrected: 0, unverified: 0, removed: 0 },
        genericResponse: row.cached_raw_text ? { raw_text: row.cached_raw_text } as any : null,
        verifiedResponse: (row.cached_html || row.section_alerts || row.cached_report) ? {
          annotated_nodes: row.cached_html,
          section_alerts: row.section_alerts || [],
          report: row.cached_report || null,
          citations: [],
          rag_context: null,
          raw_text: '',
          annotated_text: ''
        } as ProcessLegalQueryResponse : null
      }));
      setSessionHistory(history);
    });
  }, []);

  /* ── pipeline handler ───────────────────────────────────── */
  const handleRunPipeline = async () => {
    if (!query.trim() || isProcessing) return;
    setIsProcessing(true);
    setError(null);
    setGenericResponse(null);
    setVerifiedResponse(null);

    try {
      // Fire both generic + verified in parallel
      const [generic, verified] = await Promise.all([
        processLegalQuery(query, selectedArea, 'generic'),
        processLegalQuery(query, selectedArea, 'verified'),
      ]);
      setGenericResponse(generic);
      setVerifiedResponse(verified);
      
      const stats = {
        verified: verified?.report?.verified ?? 0,
        corrected: verified?.report?.corrected ?? 0,
        unverified: verified?.report?.unverified ?? 0,
        removed: verified?.report?.removed ?? 0,
      };

      // Generate deterministic, hyper-specific session name
      const matter = legalMatters.find(m => m.id === selectedArea);
      let sessionLabel = 'Verification Audit';
      if (matter) {
        // e.g. "Rajesh Kumar — Anticipatory Bail" -> "Rajesh Kumar — Anticipatory Bail Audit"
        const baseName = matter.title.replace(' — ', ' - ');
        sessionLabel = `${baseName} Audit`;
        if (sessionLabel.length > 55) {
          sessionLabel = sessionLabel.substring(0, 52) + '...';
        }
      }

      // Append to session history dynamically
      const newRun: SessionHistoryItem = {
        id: `run-${Date.now()}`,
        practiceAreaId: selectedArea,
        practiceAreaLabel: sessionLabel.toUpperCase(),
        querySnippet: query.length > 50 ? query.substring(0, 50) + '...' : query,
        fullQuery: query,
        timestamp: new Date().toISOString(),
        stats,
        genericResponse: generic,
        verifiedResponse: verified
      };
      setSessionHistory((prev) => [newRun, ...prev].slice(0, 5));
      
      // Fire off background save telemetry to Supabase
      saveSessionHistory({
        practice_area: sessionLabel,
        query_snippet: newRun.querySnippet,
        cached_query: newRun.fullQuery,
        cached_raw_text: generic?.raw_text,
        cached_html: verified?.annotated_nodes,
        badge_counts: stats,
        section_alerts: verified?.section_alerts ?? [],
        cached_report: verified?.report ?? {}
      });

      // Append new citations to ledger
      if (verified?.citations) {
        setHistoricCitations((prev) => {
          const map = new Map(prev.map(c => [c.citationText, c]));
          for (const c of verified.citations) {
            const existing = map.get(c.citation.original_text);
            if (existing) {
              existing.frequency += 1;
            } else {
              map.set(c.citation.original_text, {
                id: `c-${Date.now()}-${Math.random()}`,
                citationText: c.citation.original_text,
                frequency: 1,
                status: c.status,
                savings: (c.status === 'REMOVED' ? 0.80 : 0)
              });
            }
          }
          return Array.from(map.values()).sort((a,b) => b.frequency - a.frequency);
        });
      }

    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Pipeline failed');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleLoadSession = (item: SessionHistoryItem) => {
    setSelectedArea(item.practiceAreaId);
    setQuery(item.fullQuery); 
    
    // Unconditionally apply the cached responses.
    // If they are null (like the mock data), this correctly triggers the fallback 
    // UI placeholder icons without throwing errors.
    setGenericResponse(item.genericResponse);
    setVerifiedResponse(item.verifiedResponse);
  };

  /* ── export telemetry ───────────────────────────────────── */
  const handleExport = () => {
    const payload = {
      timestamp: new Date().toISOString(),
      query,
      report: verifiedResponse?.report ?? null,
      citations: verifiedResponse?.citations ?? [],
      section_alerts: verifiedResponse?.section_alerts ?? [],
      rag_context: verifiedResponse?.rag_context ?? null,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `brahmo-telemetry-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  /* ── render ─────────────────────────────────────────────── */
  return (
    <div className="flex h-screen flex-col overflow-hidden bg-deep-space">
      {/* ════════════════════════════════════════════════════
          TOP NAVIGATION HEADER
         ════════════════════════════════════════════════════ */}
      <header className="flex shrink-0 items-center justify-between border-b border-border-dim bg-panel px-5 py-3">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-purple-600 to-purple-400">
            <Shield className="h-4 w-4 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-black uppercase tracking-[0.15em] text-white">
              Brahmo Legal Safety Engine
            </h1>
            <p className="text-[9px] font-medium uppercase tracking-[0.3em] text-slate-500">
              Deterministic Citation Verification Pipeline
            </p>
          </div>
        </div>

        {/* Center: Status Beacon */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span
              className={`h-2 w-2 rounded-full ${
                apiConnected
                  ? 'bg-emerald-500 animate-pulse-glow'
                  : apiConnected === false
                  ? 'bg-rose-500'
                  : 'bg-slate-600'
              }`}
            />
            <span className="text-[10px] font-bold uppercase tracking-[0.2em]">
              {apiConnected ? (
                <span className="text-emerald-400">DB: Connected</span>
              ) : apiConnected === false ? (
                <span className="text-rose-400">DB: Offline</span>
              ) : (
                <span className="text-slate-500">Checking...</span>
              )}
            </span>
          </div>
          {isProcessing && (
            <div className="flex items-center gap-1.5">
              <Activity className="h-3 w-3 animate-pulse text-purple-400" />
              <span className="text-[10px] font-bold uppercase tracking-wider text-purple-400">
                Pipeline Active
              </span>
            </div>
          )}
        </div>

        {/* Right: Export */}
        <button
          onClick={handleExport}
          disabled={!verifiedResponse}
          className="flex items-center gap-2 rounded-lg border border-border-dim bg-slate-800/50 px-4 py-2 text-[10px] font-bold uppercase tracking-wider text-slate-400 transition-all hover:border-border-glow hover:text-white disabled:opacity-30 disabled:cursor-not-allowed"
        >
          <Download className="h-3.5 w-3.5" />
          Export Telemetry
        </button>
      </header>

      {/* Error Banner */}
      {error && (
        <div className="shrink-0 bg-rose-900/30 border-b border-rose-500/20 px-5 py-2 text-center text-xs text-rose-300">
          ⚠️ {error}
        </div>
      )}

      {/* ════════════════════════════════════════════════════
          THREE-COLUMN MASTER GRID
         ════════════════════════════════════════════════════ */}
      <div className="flex flex-1 overflow-hidden">
        {/* Column 1: Control Panel (25%) */}
        <div className="w-1/4 shrink-0 flex flex-col overflow-hidden border-r border-border-dim p-3">
          <ControlPanel
            selectedArea={selectedArea}
            onSelectArea={setSelectedArea}
            query={query}
            onQueryChange={setQuery}
            onRunPipeline={handleRunPipeline}
            isProcessing={isProcessing}
            sessionHistory={sessionHistory}
            onLoadSession={handleLoadSession}
          />
        </div>

        {/* Column 2: Output Comparison (50%) */}
        <div className="flex-1 overflow-hidden p-3">
          <OutputComparison
            rawText={genericResponse?.raw_text ?? null}
            annotatedNodes={verifiedResponse?.annotated_nodes ?? null}
            ragContext={verifiedResponse?.rag_context ?? null}
            isProcessing={isProcessing}
          />
        </div>

        {/* Column 3: Telemetry (25%) */}
        <div className="w-1/4 shrink-0 flex flex-col overflow-hidden border-l border-border-dim p-3">
          <TelemetryPanel
            report={verifiedResponse?.report ?? null}
            sectionAlerts={verifiedResponse?.section_alerts ?? []}
            isProcessing={isProcessing}
            historicCitations={historicCitations}
          />
        </div>
      </div>
    </div>
  );
}
