import { useState, type FormEvent } from "react";
import { Navigate, useNavigate } from "react-router";
import { useAuth } from "../auth";

export default function Login() {
  const { admin, login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (admin) return <Navigate to="/" replace />;

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(email, password);
      navigate("/");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <form onSubmit={submit} className="w-full max-w-sm space-y-4 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-3">
          <img src="/favicon.svg" alt="" className="h-10 w-10 rounded-[11px]" />
          <div>
            <h1 className="text-lg font-semibold">Wasel · Ministry console</h1>
            <p className="text-xs text-gray-500">وزارة الصحة العامة · Ministry of Public Health</p>
          </div>
        </div>
        <label className="block text-sm">
          Email
          <input
            type="email"
            required
            autoFocus
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2"
          />
        </label>
        <label className="block text-sm">
          Password
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2"
          />
        </label>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          disabled={busy}
          className="w-full rounded-md bg-[#0d5c48] px-3 py-2 text-sm font-medium text-white hover:bg-[#0b4f3e] disabled:opacity-50"
        >
          {busy ? "Logging in…" : "Log in"}
        </button>
      </form>
    </div>
  );
}
