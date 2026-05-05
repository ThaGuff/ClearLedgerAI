import type { AnalysisResponse } from './types';

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchDemo(): Promise<AnalysisResponse> {
  const r = await fetch(`${API_BASE}/api/demo`, { cache: 'no-store' });
  if (!r.ok) throw new Error(`Demo failed: ${r.status}`);
  return r.json();
}

export async function analyzeFiles(files: File[]): Promise<AnalysisResponse> {
  const fd = new FormData();
  files.forEach((f) => fd.append('files', f));
  const r = await fetch(`${API_BASE}/api/analyze`, {
    method: 'POST',
    body: fd,
  });
  if (!r.ok) {
    const txt = await r.text();
    throw new Error(`Analyze failed (${r.status}): ${txt}`);
  }
  return r.json();
}

export async function fetchCoach(transactions: AnalysisResponse['transactions']): Promise<string> {
  const r = await fetch(`${API_BASE}/api/coach`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ transactions }),
  });
  if (!r.ok) throw new Error(`Coach failed: ${r.status}`);
  const data = await r.json();
  return data.narrative as string;
}
