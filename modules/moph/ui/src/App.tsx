import { useApi } from "@h4h/module-ui";
import { useCallback, useEffect, useState } from "react";

type Tab = "overview" | "facts" | "gaps" | "searches";

const TABS: { id: Tab; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "facts", label: "Official facts" },
  { id: "gaps", label: "Unanswered" },
  { id: "searches", label: "Searches" },
];

export default function App() {
  const [tab, setTab] = useState<Tab>("overview");
  return (
    <div className="mx-auto max-w-5xl p-6">
      <h1 className="mb-4 text-xl font-semibold">Ministry Info</h1>
      <nav className="mb-6 flex gap-1 border-b border-gray-200">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`-mb-px border-b-2 px-3 py-2 text-sm ${
              tab === t.id ? "border-gray-900 font-medium text-gray-900" : "border-transparent text-gray-500 hover:text-gray-800"
            }`}
          >
            {t.label}
          </button>
        ))}
      </nav>
      {tab === "overview" && <Overview />}
      {tab === "facts" && <Facts />}
      {tab === "gaps" && <Gaps />}
      {tab === "searches" && <Searches />}
    </div>
  );
}

function useLoad<T>(path: string) {
  const api = useApi();
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(() => {
    api<T>(path)
      .then((d) => {
        setData(d);
        setError(null);
      })
      .catch((e) => setError(e.message));
  }, [api, path]);
  useEffect(load, [load]);
  return { data, error, load, setError };
}

function ErrorText({ error }: { error: string | null }) {
  return error ? <p className="mb-4 text-sm text-red-600">{error}</p> : null;
}

const date = (iso: string) => new Date(iso).toLocaleString();

// Overview

type OverviewData = {
  data: Record<string, number>;
  last_load: { at: string; data_date: string; by: string } | null;
  data_dir: string;
  open_gaps: number;
  searches_7d: number;
  empty_searches_7d: number;
};

function Overview() {
  const api = useApi();
  const { data, error, load, setError } = useLoad<OverviewData>("/overview");
  const [busy, setBusy] = useState(false);

  async function reload() {
    setBusy(true);
    try {
      await api("/reload", { method: "POST" });
      load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  if (!data) return <ErrorText error={error} />;
  return (
    <div className="space-y-6">
      <ErrorText error={error} />
      <div className="grid grid-cols-3 gap-3">
        <Stat label="Unanswered questions" value={data.open_gaps} />
        <Stat label="Searches, last 7 days" value={data.searches_7d} />
        <Stat label="Searches with no result" value={data.empty_searches_7d} />
      </div>
      <section className="rounded-lg border border-gray-200 bg-white p-4">
        <div className="mb-3 flex items-start justify-between gap-4">
          <div>
            <h2 className="font-medium">Ministry data</h2>
            <p className="text-sm text-gray-500">
              {data.last_load
                ? `Crawled ${data.last_load.data_date}, loaded ${date(data.last_load.at)} by ${data.last_load.by}`
                : "Not loaded yet."}
            </p>
          </div>
          <button
            onClick={reload}
            disabled={busy}
            className="rounded-md bg-gray-900 px-3 py-1.5 text-sm font-medium whitespace-nowrap text-white disabled:opacity-50"
          >
            {busy ? "Loading…" : "Reload from files"}
          </button>
        </div>
        <dl className="grid grid-cols-3 gap-y-2 text-sm">
          {Object.entries(data.data).map(([key, value]) => (
            <div key={key}>
              <dt className="text-gray-500">{key.replaceAll("_", " ")}</dt>
              <dd className="font-medium">{value.toLocaleString()}</dd>
            </div>
          ))}
        </dl>
        <p className="mt-3 text-xs text-gray-400">Files: {data.data_dir}. Official facts and logs are kept on reload.</p>
      </section>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="text-2xl font-semibold">{value}</div>
      <div className="text-sm text-gray-500">{label}</div>
    </div>
  );
}

// Facts

type Fact = {
  id?: number;
  topic: string;
  rule: string;
  who_is_eligible: string;
  where: string;
  effective_date: string;
  source_url: string;
  source_date: string;
  confidence: "high" | "medium" | "low";
  note: string;
  active: boolean;
  updated_by?: string;
  updated_at?: string;
};

const EMPTY_FACT: Fact = {
  topic: "",
  rule: "",
  who_is_eligible: "",
  where: "",
  effective_date: "",
  source_url: "",
  source_date: "",
  confidence: "high",
  note: "",
  active: true,
};

const confidenceClass = {
  high: "bg-green-100 text-green-800",
  medium: "bg-amber-100 text-amber-800",
  low: "bg-gray-200 text-gray-700",
};

function Facts() {
  const { data, error, load } = useLoad<Fact[]>("/facts");
  const [editing, setEditing] = useState<Fact | null>(null);
  const [filter, setFilter] = useState("");

  const shown = data?.filter((f) => `${f.topic} ${f.rule} ${f.who_is_eligible}`.toLowerCase().includes(filter.toLowerCase()));
  return (
    <div>
      <p className="mb-4 text-sm text-gray-500">
        The agent treats these as the most authoritative answers on coverage and eligibility. Keep each one dated and
        sourced; switch a fact off when it is superseded.
      </p>
      <ErrorText error={error} />
      <div className="mb-4 flex gap-2">
        <input
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Filter"
          className="flex-1 rounded-md border border-gray-300 px-3 py-1.5 text-sm"
        />
        <button onClick={() => setEditing(EMPTY_FACT)} className="rounded-md bg-gray-900 px-3 py-1.5 text-sm font-medium text-white">
          Add fact
        </button>
      </div>
      {editing && (
        <FactForm
          fact={editing}
          onDone={() => {
            setEditing(null);
            load();
          }}
        />
      )}
      <ul className="space-y-2">
        {shown?.map((f) => (
          <li key={f.id} className={`rounded-lg border border-gray-200 bg-white p-4 ${f.active ? "" : "opacity-50"}`}>
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0">
                <div className="mb-1 flex flex-wrap items-center gap-2 text-xs">
                  <span className="font-medium text-gray-700">{f.topic.replaceAll("_", " ")}</span>
                  <span className={`rounded-full px-2 py-0.5 ${confidenceClass[f.confidence]}`}>{f.confidence}</span>
                  {!f.active && <span className="rounded-full bg-gray-100 px-2 py-0.5 text-gray-600">off</span>}
                  {f.effective_date && <span className="text-gray-500">{f.effective_date}</span>}
                </div>
                <p dir="auto" className="text-sm">
                  {f.rule}
                </p>
                {f.who_is_eligible && <p className="mt-1 text-xs text-gray-500">Who: {f.who_is_eligible}</p>}
                {f.source_url && (
                  <a href={f.source_url} target="_blank" rel="noreferrer" className="mt-1 block truncate text-xs text-blue-700">
                    {f.source_url}
                  </a>
                )}
              </div>
              <button onClick={() => setEditing(f)} className="text-sm text-gray-600 hover:text-gray-900">
                Edit
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

function FactForm({ fact, onDone }: { fact: Fact; onDone: () => void }) {
  const api = useApi();
  const [draft, setDraft] = useState(fact);
  const [error, setError] = useState<string | null>(null);
  const set = (key: keyof Fact) => (e: { target: { value: string } }) => setDraft({ ...draft, [key]: e.target.value });

  async function save() {
    try {
      const { id, updated_by, updated_at, ...body } = draft;
      await api(id ? `/facts/${id}` : "/facts", { method: id ? "PUT" : "POST", body: JSON.stringify(body) });
      onDone();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function remove() {
    if (!draft.id) return;
    try {
      await api(`/facts/${draft.id}`, { method: "DELETE" });
      onDone();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  const input = "w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm";
  return (
    <div className="mb-4 space-y-3 rounded-lg border border-gray-300 bg-gray-50 p-4">
      <div className="grid grid-cols-2 gap-3">
        <Field label="Topic">
          <input value={draft.topic} onChange={set("topic")} placeholder="e.g. dialysis" className={input} />
        </Field>
        <Field label="Confidence">
          <select value={draft.confidence} onChange={set("confidence")} className={input}>
            <option value="high">high</option>
            <option value="medium">medium</option>
            <option value="low">low</option>
          </select>
        </Field>
      </div>
      <Field label="Rule">
        <textarea dir="auto" value={draft.rule} onChange={set("rule")} rows={3} className={input} />
      </Field>
      <div className="grid grid-cols-2 gap-3">
        <Field label="Who is eligible">
          <input dir="auto" value={draft.who_is_eligible} onChange={set("who_is_eligible")} className={input} />
        </Field>
        <Field label="Where">
          <input dir="auto" value={draft.where} onChange={set("where")} className={input} />
        </Field>
        <Field label="In force since">
          <input value={draft.effective_date} onChange={set("effective_date")} placeholder="2026-07-02" className={input} />
        </Field>
        <Field label="Source date">
          <input value={draft.source_date} onChange={set("source_date")} placeholder="YYYY-MM-DD" className={input} />
        </Field>
      </div>
      <Field label="Source URL">
        <input value={draft.source_url} onChange={set("source_url")} className={input} />
      </Field>
      <Field label="Note for editors (the agent sees it too)">
        <input dir="auto" value={draft.note} onChange={set("note")} className={input} />
      </Field>
      <label className="flex items-center gap-2 text-sm">
        <input type="checkbox" checked={draft.active} onChange={(e) => setDraft({ ...draft, active: e.target.checked })} />
        Active (the agent uses it)
      </label>
      <ErrorText error={error} />
      <div className="flex gap-2">
        <button
          onClick={save}
          disabled={!draft.topic.trim() || !draft.rule.trim()}
          className="rounded-md bg-gray-900 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
        >
          Save
        </button>
        <button onClick={onDone} className="rounded-md px-3 py-1.5 text-sm text-gray-600">
          Cancel
        </button>
        {draft.id && (
          <button onClick={remove} className="ml-auto rounded-md px-3 py-1.5 text-sm text-red-600">
            Delete
          </button>
        )}
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs text-gray-500">{label}</span>
      {children}
    </label>
  );
}

// Unanswered questions

type Gap = { id: number; question: string; reason: string; status: "open" | "resolved"; resolution: string; created_at: string };

function Gaps() {
  const [status, setStatus] = useState<"open" | "resolved">("open");
  const { data, error, load } = useLoad<Gap[]>(`/gaps?status=${status}`);
  return (
    <div>
      <div className="mb-4 flex items-center gap-3">
        <p className="mr-auto text-sm text-gray-500">
          Questions the agent could not answer from our data. Add a fact or fix the data, then mark them resolved.
        </p>
        <select value={status} onChange={(e) => setStatus(e.target.value as Gap["status"])} className="rounded-md border border-gray-300 px-2 py-1 text-sm">
          <option value="open">Open</option>
          <option value="resolved">Resolved</option>
        </select>
      </div>
      <ErrorText error={error} />
      {data?.length === 0 && <p className="text-sm text-gray-500">Nothing here.</p>}
      <ul className="space-y-2">
        {data?.map((g) => <GapCard key={g.id} gap={g} onChange={load} />)}
      </ul>
    </div>
  );
}

function GapCard({ gap, onChange }: { gap: Gap; onChange: () => void }) {
  const api = useApi();
  const [note, setNote] = useState(gap.resolution);
  const [error, setError] = useState<string | null>(null);

  async function update(status: Gap["status"]) {
    try {
      await api(`/gaps/${gap.id}`, { method: "PATCH", body: JSON.stringify({ status, resolution: note }) });
      onChange();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <li className="rounded-lg border border-gray-200 bg-white p-4">
      <p dir="auto" className="font-medium">
        {gap.question}
      </p>
      <p className="mt-1 text-sm text-gray-500">
        {gap.reason} · {date(gap.created_at)}
      </p>
      <div className="mt-3 flex gap-2">
        <input
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="What was done (e.g. added fact on IVF)"
          className="flex-1 rounded-md border border-gray-300 px-3 py-1.5 text-sm"
        />
        {gap.status === "open" ? (
          <button onClick={() => update("resolved")} className="rounded-md bg-gray-900 px-3 py-1.5 text-sm font-medium text-white">
            Resolve
          </button>
        ) : (
          <button onClick={() => update("open")} className="rounded-md border border-gray-300 px-3 py-1.5 text-sm">
            Reopen
          </button>
        )}
      </div>
      <ErrorText error={error} />
    </li>
  );
}

// Searches

type Search = { tool: string; query: string; results: number; created_at: string };

function Searches() {
  const [emptyOnly, setEmptyOnly] = useState(false);
  const { data, error } = useLoad<Search[]>(`/searches?empty_only=${emptyOnly}`);
  return (
    <div>
      <div className="mb-4 flex items-center gap-3">
        <p className="mr-auto text-sm text-gray-500">What the agent searched for, newest first. No user details are stored.</p>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={emptyOnly} onChange={(e) => setEmptyOnly(e.target.checked)} />
          No results only
        </label>
      </div>
      <ErrorText error={error} />
      {data?.length === 0 && <p className="text-sm text-gray-500">No searches yet.</p>}
      {data && data.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-gray-200 text-gray-500">
              <tr>
                <th className="px-4 py-2 font-medium">Query</th>
                <th className="px-4 py-2 font-medium">Tool</th>
                <th className="px-4 py-2 text-right font-medium">Results</th>
                <th className="px-4 py-2 font-medium">When</th>
              </tr>
            </thead>
            <tbody>
              {data.map((s, i) => (
                <tr key={i} className="border-b border-gray-100 last:border-0">
                  <td dir="auto" className="px-4 py-2">
                    {s.query}
                  </td>
                  <td className="px-4 py-2 text-gray-500">{s.tool.replaceAll("_", " ")}</td>
                  <td className={`px-4 py-2 text-right ${s.results === 0 ? "font-medium text-red-600" : ""}`}>{s.results}</td>
                  <td className="px-4 py-2 whitespace-nowrap text-gray-500">{date(s.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
