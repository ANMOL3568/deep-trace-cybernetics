export type User = { id: number; name: string; email: string; role: 'ADMIN'|'MANAGER'|'USER'; is_active: boolean; created_at: string };
export type Tenant = { name: string; slug: string };
export type Campaign = { id: number; title: string; description: string; status: string; created_at: string; members?: User[] };
export type SecurityEvent = { id: number; event_type: string; description: string; severity: string; status: string; created_at: string };
export type Audit = { id: number; actor: string; action: string; resource: string; created_at: string };
export type Page<T> = { items: T[]; total: number; page: number; page_size: number };
export type Dashboard = { users: number; campaigns: number; active_campaigns: number; open_events: number; critical_events: number; severity_counts: Record<string, number>; trend: {day: string; count: number}[]; recent_events: SecurityEvent[]; recent_campaigns: Campaign[] };

let token = sessionStorage.getItem('deeptrace_token') || '';
export function setToken(value: string) { token = value; if (value) sessionStorage.setItem('deeptrace_token', value); else sessionStorage.removeItem('deeptrace_token'); }
export function hasToken() { return Boolean(token); }
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${import.meta.env.VITE_API_URL || ''}/api${path}`, {
    ...options, headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...options.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    if (response.status === 401 && !path.includes('/login')) { setToken(''); window.dispatchEvent(new Event('session-expired')); }
    const detail = Array.isArray(body.detail) ? body.detail.map((e: {loc: string[]; msg: string}) => `${e.loc.slice(1).join('.')}: ${e.msg}`).join('; ') : body.detail;
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return response.status === 204 ? undefined as T : response.json();
}
export function write<T>(path: string, method: string, body?: unknown) { return api<T>(path, { method, ...(body ? {body: JSON.stringify(body)} : {}) }); }
