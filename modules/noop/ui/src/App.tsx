import { useAdmin, useApi } from "@h4h/module-ui";
import { useCallback, useEffect, useState } from "react";

type Request = {
  ticket_id: string;
  title: string;
  details: string | null;
  status: string;
  created_at: string;
  answer: string | null;
  answered_by: string | null;
};

export default function App() {
  const api = useApi();
  const admin = useAdmin();
  const [requests, setRequests] = useState<Request[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    api<Request[]>("/requests")
      .then(setRequests)
      .catch((e) => setError(e.message));
  }, [api]);

  useEffect(load, [load]);

  return (
    <div className="mx-auto max-w-5xl p-6">
      <div className="mb-6 flex items-baseline justify-between">
        <h1 className="text-xl font-semibold">Noop requests</h1>
        <span className="text-sm text-gray-500">{admin.email}</span>
      </div>
      {error && <p className="mb-4 text-sm text-red-600">{error}</p>}
      {requests?.length === 0 && (
        <p className="text-sm text-gray-500">
          No requests yet. Open one with <code>uv run h4h tools call noop__open_request</code>.
        </p>
      )}
      <ul className="space-y-3">
        {requests?.map((r) => <RequestCard key={r.ticket_id} request={r} onAnswered={load} />)}
      </ul>
    </div>
  );
}

function RequestCard({ request, onAnswered }: { request: Request; onAnswered: () => void }) {
  const api = useApi();
  const [text, setText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const open = request.status === "active" || request.status === "awaiting_user";

  async function answer() {
    setBusy(true);
    setError(null);
    try {
      await api(`/requests/${request.ticket_id}/answer`, { method: "POST", body: JSON.stringify({ text }) });
      setText("");
      onAnswered();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <li className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="font-medium">{request.title}</div>
          {request.details && <p className="mt-1 text-sm text-gray-600">{request.details}</p>}
        </div>
        <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs whitespace-nowrap text-gray-700">
          {request.status.replace("_", " ")}
        </span>
      </div>
      {request.answer && (
        <p className="mt-3 rounded-md bg-gray-50 p-3 text-sm">
          {request.answer}
          <span className="mt-1 block text-xs text-gray-500">— {request.answered_by}</span>
        </p>
      )}
      {open && (
        <div className="mt-3 flex gap-2">
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder={request.answer ? "Send another update" : "Answer the user"}
            className="flex-1 rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          />
          <button
            onClick={answer}
            disabled={busy || !text.trim()}
            className="rounded-md bg-gray-900 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
          >
            Send
          </button>
        </div>
      )}
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </li>
  );
}
