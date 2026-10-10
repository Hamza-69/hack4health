/** Client for the core's admin API. Requests go to /api, which Vite forwards to the core. */

export type Admin = { id: string; email: string; role: "operator" | "supplier"; modules: string[] };
export type Module = { name: string; title: string; ui_url: string };
export type TicketStatus = "active" | "awaiting_user" | "resolved" | "archived";
export type Ticket = {
  id: string;
  kind: string;
  title: string;
  details: string | null;
  status: TicketStatus;
  resolution: string | null;
  created_at: string;
  resolved_at: string | null;
};

const SESSION_KEY = "h4h.session";

export const session = {
  get: () => localStorage.getItem(SESSION_KEY),
  set: (token: string) => localStorage.setItem(SESSION_KEY, token),
  clear: () => localStorage.removeItem(SESSION_KEY),
};

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = session.get();
  const response = await fetch(`/api${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  });
  if (response.status === 401 && token) {
    // Session expired or revoked: back to the login page.
    session.clear();
    window.location.assign("/login");
  }
  if (!response.ok) {
    const detail = (await response.json().catch(() => null))?.detail;
    throw new Error(typeof detail === "string" ? detail : response.statusText);
  }
  return response.json();
}
