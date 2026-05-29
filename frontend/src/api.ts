import type { LegalMatter, ProcessLegalQueryResponse } from './types';

// ── API Base URL ─────────────────────────────────────────────
// In dev: Vite proxy forwards /api/* → localhost:8000
// Fallback: direct connection to backend if proxy fails
const API_BASE = import.meta.env.VITE_API_URL || '';

// ── Fallback data when API is unavailable ────────────────────
const FALLBACK_MATTERS: LegalMatter[] = [
  { id: 1, title: 'Rajesh Kumar — Anticipatory Bail', practice: 'Criminal', court: 'Delhi High Court', query: 'Key SC precedents on anticipatory bail in economic offences' },
  { id: 2, title: 'Criminal Complaint — Cheating', practice: 'Criminal', court: 'Delhi Metropolitan Magistrate', query: 'Draft complaint for cheating under Section 420 IPC with criminal breach of trust under Section 406 IPC' },
  { id: 3, title: 'NDPS Act — Bail Research', practice: 'Criminal', court: 'Supreme Court', query: 'Summarize SC approach to bail in NDPS cases over last 5 years' },
  { id: 4, title: 'Criminal Revision — Delhi HC', practice: 'Criminal', court: 'Delhi High Court', query: 'Key Delhi HC decisions on Section 482 BNSS powers in last 2 years' },
  { id: 5, title: 'Corporate NDA Review', practice: 'Corporate', court: 'N/A', query: 'Review NDA and flag missing clauses for Indian law' },
  { id: 6, title: 'Shareholders Dispute — NCLT', practice: 'Corporate', court: 'NCLT Delhi', query: 'Grounds for NCLT petition — oppression and mismanagement' },
  { id: 7, title: 'Property Dispute — Specific Performance', practice: 'Property', court: 'Civil Court Delhi', query: 'Specific performance of immovable property sale agreement' },
  { id: 8, title: 'Family Law — Divorce', practice: 'Family', court: 'Family Court Delhi', query: 'Grounds for contested divorce under Hindu Marriage Act Section 13' },
];

// ── Smart fetch: tries proxy first, then direct backend ──────
async function apiFetch(path: string, options?: RequestInit): Promise<Response> {
  // Try 1: Vite proxy (relative path)
  try {
    const res = await fetch(`${API_BASE}${path}`, options);
    if (res.ok) return res;
  } catch {
    // proxy failed, try direct
  }

  // Try 2: Direct backend connection
  const directUrl = `http://localhost:8000${path}`;
  return fetch(directUrl, options);
}

// ── Fetch legal matters ──────────────────────────────────────
export async function fetchLegalMatters(): Promise<LegalMatter[]> {
  try {
    const res = await apiFetch('/api/legal-matters');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return data;
  } catch (e) {
    console.warn('⚠️ Backend unavailable — using fallback matters:', e);
    return FALLBACK_MATTERS;
  }
}

// ── Process a legal query ────────────────────────────────────
export async function processLegalQuery(
  query: string,
  matterId: number,
  mode: 'generic' | 'verified'
): Promise<ProcessLegalQueryResponse> {
  const res = await apiFetch('/api/process-legal-query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, matter_id: matterId, mode }),
  });

  if (!res.ok) {
    const errorBody = await res.text().catch(() => '');
    throw new Error(
      `Request failed (${res.status}): ${errorBody || res.statusText}`
    );
  }

  return await res.json();
}

// ── Session History Telemetry ────────────────────────────────
export async function fetchSessionHistory(): Promise<any[]> {
  try {
    const res = await apiFetch('/api/history/fetch');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return data.data || [];
  } catch (e) {
    console.warn('⚠️ Backend unavailable — history fetch failed:', e);
    return [];
  }
}

export async function saveSessionHistory(payload: any): Promise<void> {
  try {
    const res = await apiFetch('/api/history/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
  } catch (e) {
    console.error('⚠️ Failed to save session history telemetry:', e);
  }
}
