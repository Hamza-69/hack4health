import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type CSSProperties,
  type ReactNode,
} from "react";
import { READY, TOKEN, TOKEN_REQUEST } from "./protocol";

/** Origin of the admin panel shell. `h4h dev` sets it; tokens from any other origin are ignored. */
const SHELL_ORIGIN: string = import.meta.env.VITE_SHELL_ORIGIN ?? "http://localhost:5173";

export type Admin = { id: string; email: string; role: "operator" | "supplier" };

type Shell = { token: string; admin: Admin; refresh: () => void };

const ShellContext = createContext<Shell | null>(null);

function claims(token: string): { sub: string; email: string; role: Admin["role"]; exp: number } {
  const payload = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
  return JSON.parse(atob(payload));
}

/**
 * Wrap the module UI in this. It gets an admin token from the shell over postMessage,
 * renews it before it expires, and renders children once it has one.
 */
export function ShellProvider({ children }: { children: ReactNode }) {
  const embedded = window.parent !== window;
  const [token, setToken] = useState<string | null>(null);
  const [slow, setSlow] = useState(false);

  const ask = useCallback(
    (type: typeof READY | typeof TOKEN_REQUEST) => window.parent.postMessage({ type }, SHELL_ORIGIN),
    [],
  );

  useEffect(() => {
    if (!embedded) return;
    const onMessage = (event: MessageEvent) => {
      if (event.source !== window.parent || event.origin !== SHELL_ORIGIN) return;
      if (event.data?.type === TOKEN) setToken(event.data.token);
    };
    window.addEventListener("message", onMessage);
    ask(READY);
    const timer = setTimeout(() => setSlow(true), 5000);
    return () => {
      window.removeEventListener("message", onMessage);
      clearTimeout(timer);
    };
  }, [embedded, ask]);

  // Ask for a fresh token a minute before this one expires.
  useEffect(() => {
    if (!token) return;
    const wait = claims(token).exp * 1000 - Date.now() - 60_000;
    const timer = setTimeout(() => ask(TOKEN_REQUEST), Math.max(wait, 0));
    return () => clearTimeout(timer);
  }, [token, ask]);

  const shell = useMemo<Shell | null>(() => {
    if (!token) return null;
    const { sub, email, role } = claims(token);
    return { token, admin: { id: sub, email, role }, refresh: () => ask(TOKEN_REQUEST) };
  }, [token, ask]);

  if (!embedded) return <Notice>Open this page from the admin panel.</Notice>;
  if (!shell)
    return (
      <Notice>
        {slow
          ? `No token from the admin panel at ${SHELL_ORIGIN}. Check VITE_SHELL_ORIGIN.`
          : "Connecting to the admin panel…"}
      </Notice>
    );
  return <ShellContext.Provider value={shell}>{children}</ShellContext.Provider>;
}

function useShell(): Shell {
  const shell = useContext(ShellContext);
  if (!shell) throw new Error("use this inside <ShellProvider>");
  return shell;
}

/** The admin using the panel right now. */
export function useAdmin(): Admin {
  return useShell().admin;
}

/** `fetch` for this module's backend: prefixes /api, sends the admin token, returns parsed JSON.
 * The API sits next to the UI's base (/ui/ → /api, /modules/moph/ui/ → /modules/moph/api behind a proxy). */
export function useApi() {
  const { token, refresh } = useShell();
  return useCallback(
    async <T,>(path: string, init: RequestInit = {}): Promise<T> => {
      const response = await fetch(`${import.meta.env.BASE_URL}../api${path}`, {
        ...init,
        headers: { "Content-Type": "application/json", ...init.headers, Authorization: `Bearer ${token}` },
      });
      if (response.status === 401) refresh();
      if (!response.ok) {
        const detail = (await response.json().catch(() => null))?.detail;
        throw new Error(typeof detail === "string" ? detail : detail ? JSON.stringify(detail) : response.statusText);
      }
      return response.json();
    },
    [token, refresh],
  );
}

const noticeStyle: CSSProperties = {
  fontFamily: "system-ui, sans-serif",
  color: "#6b7280",
  padding: 32,
  textAlign: "center",
};

function Notice({ children }: { children: ReactNode }) {
  return <p style={noticeStyle}>{children}</p>;
}
