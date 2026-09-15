const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api';
async function safeJson(res) {
  if (!res.ok) {
    let errorMsg = `HTTP Error ${res.status}: ${res.statusText}`;
    try {
      const errBody = await res.json();
      if (errBody && errBody.error) errorMsg = errBody.error;
    } catch {
      try {
        const text = await res.text();
        if (text) errorMsg = text;
      } catch {
        // fallback
      }
    }
    throw new Error(errorMsg);
  }
  return res.json();
}

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return safeJson(res);
}

export async function fetchOverview() {
  const res = await fetch(`${API_BASE}/dashboard/overview`);
  return safeJson(res);
}

export async function fetchStates() {
  const res = await fetch(`${API_BASE}/dashboard/states`);
  return safeJson(res);
}

export async function fetchCharts() {
  const res = await fetch(`${API_BASE}/analytics/charts`);
  return safeJson(res);
}

export async function fetchSummary(filters = {}) {
  const params = new URLSearchParams();
  if (filters.state && filters.state !== 'ALL') params.set('state', filters.state);
  if (filters.constituency && filters.constituency !== 'ALL') params.set('constituency', filters.constituency);
  if (filters.mp && filters.mp !== 'ALL') params.set('mp', filters.mp);
  if (filters.risk && filters.risk !== 'ALL') params.set('risk', filters.risk);
  if (filters.priority && filters.priority !== 'ALL') params.set('priority', filters.priority);
  if (filters.agreement && filters.agreement !== 'ALL') params.set('agreement', filters.agreement);

  const qs = params.toString();
  const url = qs ? `${API_BASE}/dashboard/summary?${qs}` : `${API_BASE}/dashboard/summary`;
  const res = await fetch(url);
  return safeJson(res);
}

export async function fetchFilters(filters = {}) {
  const params = new URLSearchParams();
  if (filters.state && filters.state !== 'ALL') params.set('state', filters.state);
  if (filters.constituency && filters.constituency !== 'ALL') params.set('constituency', filters.constituency);
  if (filters.mp && filters.mp !== 'ALL') params.set('mp', filters.mp);

  const qs = params.toString();
  const url = qs ? `${API_BASE}/filters?${qs}` : `${API_BASE}/filters`;
  const res = await fetch(url);
  return safeJson(res);
}

export async function fetchAnomalies({
  state,
  constituency,
  mp,
  risk,
  priority,
  agreement,
  search,
  scope = 'candidates',
  limit = 50,
  offset = 0
} = {}) {
  const params = new URLSearchParams();
  if (state && state !== 'ALL') params.set('state', state);
  if (constituency && constituency !== 'ALL') params.set('constituency', constituency);
  if (mp && mp !== 'ALL') params.set('mp', mp);
  if (risk && risk !== 'ALL') params.set('risk', risk);
  if (priority && priority !== 'ALL') params.set('priority', priority);
  if (agreement && agreement !== 'ALL') params.set('agreement', agreement);
  if (search && search.trim()) params.set('search', search.trim());
  if (scope) params.set('scope', scope);
  if (limit) params.set('limit', String(limit));
  if (offset !== undefined && offset !== null) params.set('offset', String(offset));

  const res = await fetch(`${API_BASE}/anomalies?${params.toString()}`);
  return safeJson(res);
}

export async function fetchAnomaly(workId) {
  const res = await fetch(`${API_BASE}/anomalies/${encodeURIComponent(workId)}`);
  return safeJson(res);
}

export async function fetchExplanation(workId) {
  const res = await fetch(`${API_BASE}/anomalies/${encodeURIComponent(workId)}/explanation`);
  return safeJson(res);
}

export async function generateExplanation(workId) {
  const res = await fetch(`${API_BASE}/anomalies/${encodeURIComponent(workId)}/explanation/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  });
  return safeJson(res);
}

export async function triggerReload() {
  const res = await fetch(`${API_BASE}/reload`, { method: 'POST' });
  return safeJson(res);
}
