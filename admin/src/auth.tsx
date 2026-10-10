import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { Navigate } from "react-router";
import { api, session, type Admin } from "./api";

type Auth = {
  admin: Admin | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<Auth | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [admin, setAdmin] = useState<Admin | null>(null);
  const [loading, setLoading] = useState(Boolean(session.get()));

  useEffect(() => {
    if (!session.get()) return;
    api<Admin>("/admin/me")
      .then(setAdmin)
      .catch(() => session.clear())
      .finally(() => setLoading(false));
  }, []);

  async function login(email: string, password: string) {
    const result = await api<{ token: string; admin: Admin }>("/admin/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    session.set(result.token);
    setAdmin(result.admin);
  }

  function logout() {
    session.clear();
    setAdmin(null);
  }

  if (loading) return null;
  return <AuthContext.Provider value={{ admin, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth(): Auth {
  const auth = useContext(AuthContext);
  if (!auth) throw new Error("useAuth outside <AuthProvider>");
  return auth;
}

export function RequireAuth({ children }: { children: ReactNode }) {
  return useAuth().admin ? children : <Navigate to="/login" replace />;
}
