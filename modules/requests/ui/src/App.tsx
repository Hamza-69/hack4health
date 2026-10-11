import { useAdmin, useApi } from "@h4h/module-ui";
import { type ReactNode, useCallback, useEffect, useState } from "react";

type Status = "submitted" | "needs_info" | "approved" | "declined";

type Summary = {
  number: number;
  code: string;
  service_title: string;
  service_title_ar: string;
  patient: string;
  status: Status;
  documents: number;
  created_at: string;
  updated_at: string;
  decision_due: string;
  overdue: boolean;
};

type Label = { key: string; label_en: string; label_ar: string };

type Detail = Omit<Summary, "documents"> & {
  desk: string;
  desk_contact: string;
  how_it_works_today: string;
  source_urls: string[];
  fields: (Label & { value: string })[];
  documents: { kind: string; url: string; description: string; added_at: string; label_en: string; label_ar: string }[];
  checklist: (Label & { required: boolean; received: boolean })[];
  history: { at: string; by: string; action: string; message: string }[];
};

const POLL_MS = 3000;

const STATUS: Record<Status, { label: string; className: string }> = {
  submitted: { label: "New", className: "bg-blue-50 text-blue-700 ring-blue-200" },
  needs_info: { label: "Waiting for patient", className: "bg-amber-50 text-amber-800 ring-amber-200" },
  approved: { label: "Approved", className: "bg-emerald-50 text-emerald-700 ring-emerald-200" },
  declined: { label: "Declined", className: "bg-rose-50 text-rose-700 ring-rose-200" },
};

const ACTION_LABEL: Record<string, string> = {
  submitted: "Submitted by Wasel",
  documents_added: "Documents added",
  needs_info: "Asked for more",
  approved: "Approved",
  declined: "Declined",
};

function usePoll<T>(path: string | null) {
  const api = useApi();
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(() => {
    if (!path) return;
    api<T>(path)
      .then((d) => {
        setData(d);
        setError(null);
      })
      .catch((e) => setError(e.message));
  }, [api, path]);
  useEffect(() => {
    setData(null);
    load();
    const id = setInterval(load, POLL_MS);
    return () => clearInterval(id);
  }, [load]);
  return { data, error, reload: load, setData };
}

function ago(iso: string) {
  const s = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.floor(s / 60)} min ago`;
  if (s < 86400) return `${Math.floor(s / 3600)} h ago`;
  return new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short" });
}

function when(iso: string) {
  return new Date(iso).toLocaleString(undefined, { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}

function Badge({ status }: { status: Status }) {
  const s = STATUS[status];
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium whitespace-nowrap ring-1 ring-inset ${s.className}`}>
      {s.label}
    </span>
  );
}

export default function App() {
  const admin = useAdmin();
  const [filter, setFilter] = useState<"open" | "all">("open");
  const [selected, setSelected] = useState<number | null>(null);
  const { data: requests, error } = usePoll<Summary[]>("/requests");

  const open = requests?.filter((r) => r.status === "submitted" || r.status === "needs_info") ?? [];
  const shown = filter === "open" ? open : (requests ?? []);
  const counts = (s: Status) => requests?.filter((r) => r.status === s).length ?? 0;

  useEffect(() => {
    if (selected === null && shown.length) setSelected(shown[0].number);
  }, [selected, shown]);

  return (
    <div className="flex h-screen flex-col bg-gray-50 text-gray-900">
      <header className="flex items-end justify-between border-b border-gray-200 bg-white px-6 py-4">
        <div>
          <h1 className="text-xl font-semibold">Ministry Inbox</h1>
          <p className="text-sm text-gray-500">Requests prepared and checked by Wasel, ready for a decision</p>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <Count n={counts("submitted")} label="new" className="text-blue-700" />
          <Count n={counts("needs_info")} label="waiting for patient" className="text-amber-700" />
          <Count n={counts("approved")} label="approved" className="text-emerald-700" />
          <Count n={counts("declined")} label="declined" className="text-rose-700" />
          <span className="border-l border-gray-200 pl-4 text-gray-500">{admin.email}</span>
        </div>
      </header>

      <div className="flex min-h-0 flex-1">
        <aside className="flex w-96 shrink-0 flex-col border-r border-gray-200 bg-white">
          <div className="flex gap-1 border-b border-gray-200 px-3 py-2">
            {(["open", "all"] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`rounded-md px-3 py-1 text-sm ${filter === f ? "bg-gray-900 text-white" : "text-gray-600 hover:bg-gray-100"}`}
              >
                {f === "open" ? `Open (${open.length})` : `All (${requests?.length ?? 0})`}
              </button>
            ))}
          </div>
          {error && <p className="p-4 text-sm text-rose-600">{error}</p>}
          {requests && shown.length === 0 && (
            <p className="p-6 text-sm text-gray-500">
              {filter === "open" ? "No open requests. New ones appear here as soon as Wasel submits them." : "No requests yet."}
            </p>
          )}
          <ul className="flex-1 overflow-auto">
            {shown.map((r) => (
              <li key={r.number}>
                <button
                  onClick={() => setSelected(r.number)}
                  className={`w-full border-b border-gray-100 px-4 py-3 text-left hover:bg-gray-50 ${
                    selected === r.number ? "bg-gray-100" : ""
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-mono text-sm font-semibold">{r.code}</span>
                    <Badge status={r.status} />
                  </div>
                  <div className="mt-1 truncate text-sm font-medium">{r.patient || "—"}</div>
                  <div className="truncate text-xs text-gray-500">{r.service_title}</div>
                  <div className="mt-1 flex justify-between text-xs text-gray-400">
                    <span>{ago(r.created_at)}</span>
                    {r.overdue && <span className="font-medium text-rose-600">Past due</span>}
                  </div>
                </button>
              </li>
            ))}
          </ul>
        </aside>

        <main className="min-w-0 flex-1 overflow-auto">
          {selected !== null ? (
            <RequestDetail key={selected} number={selected} />
          ) : (
            <div className="flex h-full items-center justify-center text-sm text-gray-400">Select a request</div>
          )}
        </main>
      </div>
    </div>
  );
}

function Count({ n, label, className }: { n: number; label: string; className: string }) {
  return (
    <span className="text-gray-500">
      <span className={`text-base font-semibold ${className}`}>{n}</span> {label}
    </span>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-lg border border-gray-200 bg-white">
      <h3 className="border-b border-gray-100 px-4 py-2 text-xs font-semibold tracking-wide text-gray-500 uppercase">{title}</h3>
      <div className="p-4">{children}</div>
    </section>
  );
}

function RequestDetail({ number }: { number: number }) {
  const api = useApi();
  const { data: r, error, setData } = usePoll<Detail>(`/requests/${number}`);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  if (error && !r) return <p className="p-6 text-sm text-rose-600">{error}</p>;
  if (!r) return <p className="p-6 text-sm text-gray-400">Loading…</p>;

  const missing = r.checklist.filter((c) => c.required && !c.received);
  const decided = r.status === "approved" || r.status === "declined";

  async function decide(action: "approve" | "ask" | "decline") {
    setBusy(action);
    setActionError(null);
    try {
      const updated = await api<Detail>(`/requests/${number}/${action}`, {
        method: "POST",
        body: JSON.stringify({ message }),
      });
      setData(updated);
      setMessage("");
    } catch (e) {
      setActionError((e as Error).message);
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="mx-auto max-w-4xl space-y-4 p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="font-mono text-2xl font-semibold">{r.code}</h2>
            <Badge status={r.status} />
          </div>
          <div className="mt-1 text-gray-700">{r.service_title}</div>
          <div className="text-gray-500" dir="rtl" lang="ar">
            {r.service_title_ar}
          </div>
        </div>
        <div className="text-right text-sm text-gray-500">
          <div>Submitted {when(r.created_at)}</div>
          <div className={r.overdue ? "font-medium text-rose-600" : ""}>Decision due {when(r.decision_due)}</div>
        </div>
      </div>

      {missing.length === 0 ? (
        <div className="rounded-lg bg-emerald-50 px-4 py-3 text-sm text-emerald-800 ring-1 ring-emerald-200 ring-inset">
          ✓ Checked by Wasel: every required document and detail is here.
        </div>
      ) : (
        <div className="rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-800 ring-1 ring-amber-200 ring-inset">
          Still missing: {missing.map((m) => m.label_en).join(", ")}
        </div>
      )}

      <Section title="Application form">
        <dl className="divide-y divide-gray-100">
          {r.fields.map((f) => (
            <div key={f.key} className="grid grid-cols-5 gap-4 py-2 text-sm">
              <dt className="col-span-2 text-gray-500">
                {f.label_en}
                <div className="text-xs text-gray-400" dir="rtl" lang="ar">
                  {f.label_ar}
                </div>
              </dt>
              <dd className="col-span-3 font-medium">{f.value || <span className="text-gray-400">—</span>}</dd>
            </div>
          ))}
        </dl>
      </Section>

      <Section title={`Documents (${r.documents.length})`}>
        <ul className="mb-4 space-y-1 text-sm">
          {r.checklist.map((c) => (
            <li key={c.key} className="flex items-start gap-2">
              <span className={c.received ? "text-emerald-600" : c.required ? "text-rose-600" : "text-gray-300"}>
                {c.received ? "✓" : c.required ? "✗" : "○"}
              </span>
              <span className={c.received || c.required ? "" : "text-gray-400"}>
                {c.label_en}
                {!c.required && " (if applicable)"}
              </span>
            </li>
          ))}
        </ul>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {r.documents.map((d, i) => (
            <a
              key={i}
              href={d.url}
              target="_blank"
              rel="noreferrer"
              className="group overflow-hidden rounded-md border border-gray-200 hover:border-gray-400"
            >
              <Thumb url={d.url} />
              <div className="p-2">
                <div className="text-xs font-medium">{d.label_en}</div>
                {d.description && <div className="mt-0.5 line-clamp-2 text-xs text-gray-500">{d.description}</div>}
              </div>
            </a>
          ))}
        </div>
      </Section>

      <div className="grid gap-4 md:grid-cols-2">
        <Section title="Responsible desk">
          <div className="text-sm font-medium">{r.desk}</div>
          <div className="mt-1 text-sm text-gray-500">{r.desk_contact}</div>
          <div className="mt-3 text-xs text-gray-500">
            <span className="font-medium text-gray-600">Without Wasel: </span>
            {r.how_it_works_today}
          </div>
          {r.source_urls.map((u) => (
            <a key={u} href={u} target="_blank" rel="noreferrer" className="mt-2 block truncate text-xs text-blue-600 hover:underline">
              {u}
            </a>
          ))}
        </Section>
        <Section title="History">
          <ol className="space-y-3">
            {r.history.map((h, i) => (
              <li key={i} className="text-sm">
                <div className="flex justify-between gap-2">
                  <span className="font-medium">{ACTION_LABEL[h.action] ?? h.action}</span>
                  <span className="text-xs whitespace-nowrap text-gray-400">{when(h.at)}</span>
                </div>
                {h.message && <div className="text-gray-600">{h.message}</div>}
                <div className="text-xs text-gray-400">{h.by}</div>
              </li>
            ))}
          </ol>
        </Section>
      </div>

      {!decided && (
        <Section title="Decision">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            rows={2}
            placeholder="Note to the patient: required to ask for more or to decline, optional to approve"
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none"
          />
          <p className="mt-1 text-xs text-gray-500">Wasel tells the patient on WhatsApp, in their own language, as soon as you decide.</p>
          <div className="mt-3 flex gap-2">
            <button
              onClick={() => decide("approve")}
              disabled={busy !== null}
              className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
            >
              {busy === "approve" ? "Approving…" : "Approve"}
            </button>
            {r.status === "submitted" && (
              <button
                onClick={() => decide("ask")}
                disabled={busy !== null || !message.trim()}
                className="rounded-md bg-amber-500 px-4 py-2 text-sm font-medium text-white hover:bg-amber-600 disabled:opacity-50"
              >
                {busy === "ask" ? "Sending…" : "Ask for more"}
              </button>
            )}
            <button
              onClick={() => decide("decline")}
              disabled={busy !== null || !message.trim()}
              className="rounded-md border border-rose-300 px-4 py-2 text-sm font-medium text-rose-700 hover:bg-rose-50 disabled:opacity-50"
            >
              {busy === "decline" ? "Declining…" : "Decline"}
            </button>
          </div>
          {actionError && <p className="mt-2 text-sm text-rose-600">{actionError}</p>}
        </Section>
      )}
    </div>
  );
}

function Thumb({ url }: { url: string }) {
  const [failed, setFailed] = useState(false);
  if (failed)
    return <div className="flex h-32 items-center justify-center bg-gray-100 text-xs text-gray-400">Open file ↗</div>;
  return <img src={url} alt="" onError={() => setFailed(true)} className="h-32 w-full bg-gray-100 object-cover" />;
}
