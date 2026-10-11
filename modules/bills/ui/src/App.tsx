import { useAdmin, useApi } from "@h4h/module-ui";
import { type ReactNode, useCallback, useEffect, useState } from "react";

type Status = "submitted" | "needs_info" | "taken_up" | "closed";

type Hospital = {
  id: string;
  name: string;
  name_ar: string;
  kind: "government" | "private";
  on_100_percent_list: boolean;
  caza?: string;
  phone?: string;
  url?: string;
  demo?: boolean;
};

type Source = { key: string; date: string; title: string; url: string; says: string };

type Summary = {
  number: number;
  code: string;
  hospital: Hospital;
  patient: string;
  incident_date: string;
  amount: string;
  paid: boolean;
  status: Status;
  created_at: string;
};

type Detail = Summary & {
  situation: { patient_cover: string; injury: string };
  rule: { verdict: string; condition?: string | null; rule: string; patient_pays: string; limits?: string; sources: Source[] };
  documents: { kind: string; url: string; description: string; added_at: string }[];
  note: string;
  history: { at: string; by: string; action: string; message: string }[];
};

type Group = {
  hospital: Hospital;
  reports: number;
  open: number;
  taken_up: number;
  amounts: string[];
  codes: string[];
  last_at: string;
};

type Rules = {
  timeline: (Source & { change: string })[];
  list: { pdf: string; note: string };
  listed: { name_ar: string; kind: string }[];
};

const POLL_MS = 3000;

const STATUS: Record<Status, { label: string; className: string }> = {
  submitted: { label: "New", className: "bg-blue-50 text-blue-700 ring-blue-200" },
  needs_info: { label: "Waiting for patient", className: "bg-amber-50 text-amber-800 ring-amber-200" },
  taken_up: { label: "Taken up", className: "bg-emerald-50 text-emerald-700 ring-emerald-200" },
  closed: { label: "Closed", className: "bg-gray-100 text-gray-600 ring-gray-200" },
};

const ACTION_LABEL: Record<string, string> = {
  submitted: "Reported through Wasel",
  added: "Patient added more",
  needs_info: "Asked for more",
  taken_up: "Taken up with the hospital",
  closed: "Closed",
};

const COVER: Record<string, string> = {
  uninsured_lebanese: "Lebanese, no other cover",
  nssf: "NSSF",
  cooperative: "Civil servants' cooperative",
  army_or_security: "Army or security forces",
  insurance: "Insurance",
  not_lebanese: "Not Lebanese",
  unknown: "Not said",
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
  return { data, error, setData };
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

function day(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}

function Badge({ status }: { status: Status }) {
  const s = STATUS[status];
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium whitespace-nowrap ring-1 ring-inset ${s.className}`}>
      {s.label}
    </span>
  );
}

function Kind({ h }: { h: Hospital }) {
  return (
    <span className="text-xs text-gray-500">
      {h.kind === "government" ? "Government" : "Private"}
      {h.on_100_percent_list && " · on the 100% list"}
      {h.demo && " · demo hospital (fictional)"}
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

type Tab = "reports" | "hospitals" | "rules";

export default function App() {
  const admin = useAdmin();
  const [tab, setTab] = useState<Tab>("reports");
  const { data: reports } = usePoll<Summary[]>("/reports");
  const count = (s: Status) => reports?.filter((r) => r.status === s).length ?? 0;
  const tabs: [Tab, string][] = [
    ["reports", "Reports"],
    ["hospitals", "By hospital"],
    ["rules", "Rules Wasel applies"],
  ];

  return (
    <div className="flex h-screen flex-col bg-gray-50 text-gray-900">
      <header className="border-b border-gray-200 bg-white px-6 pt-4">
        <div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-3">
          <div>
            <h1 className="text-xl font-semibold whitespace-nowrap">Hospital Bills</h1>
            <p className="text-sm text-gray-500">Patients the ministry covers in full who were charged anyway, with the bill</p>
          </div>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-gray-500">
            <span><span className="text-base font-semibold text-blue-700">{count("submitted")}</span> new</span>
            <span><span className="text-base font-semibold text-amber-700">{count("needs_info")}</span> waiting for patient</span>
            <span><span className="text-base font-semibold text-emerald-700">{count("taken_up")}</span> taken up</span>
            <span className="hidden border-l border-gray-200 pl-4 xl:inline">{admin.email}</span>
          </div>
        </div>
        <nav className="mt-3 flex gap-1">
          {tabs.map(([t, label]) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`border-b-2 px-3 py-2 text-sm ${tab === t ? "border-gray-900 font-medium" : "border-transparent text-gray-500 hover:text-gray-800"}`}
            >
              {label}
            </button>
          ))}
        </nav>
      </header>
      <div className="min-h-0 flex-1">
        {tab === "reports" && <Reports reports={reports} />}
        {tab === "hospitals" && <ByHospital />}
        {tab === "rules" && <RulesView />}
      </div>
    </div>
  );
}

function Reports({ reports }: { reports: Summary[] | null }) {
  const [filter, setFilter] = useState<"open" | "all">("open");
  const [selected, setSelected] = useState<number | null>(null);
  const open = reports?.filter((r) => r.status === "submitted" || r.status === "needs_info") ?? [];
  const shown = filter === "open" ? open : (reports ?? []);

  useEffect(() => {
    if (selected === null && shown.length) setSelected(shown[0].number);
  }, [selected, shown]);

  return (
    <div className="flex h-full flex-col lg:flex-row">
      <aside className="flex max-h-72 w-full shrink-0 flex-col border-b border-gray-200 bg-white lg:max-h-none lg:w-80 lg:border-r lg:border-b-0 xl:w-96">
        <div className="flex gap-1 border-b border-gray-200 px-3 py-2">
          {(["open", "all"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`rounded-md px-3 py-1 text-sm ${filter === f ? "bg-gray-900 text-white" : "text-gray-600 hover:bg-gray-100"}`}
            >
              {f === "open" ? `Open (${open.length})` : `All (${reports?.length ?? 0})`}
            </button>
          ))}
        </div>
        {reports && shown.length === 0 && (
          <p className="p-6 text-sm text-gray-500">
            {filter === "open" ? "No open reports. New ones appear here as soon as a patient files one." : "No reports yet."}
          </p>
        )}
        <ul className="flex-1 overflow-auto">
          {shown.map((r) => (
            <li key={r.number}>
              <button
                onClick={() => setSelected(r.number)}
                className={`w-full border-b border-gray-100 px-4 py-3 text-left hover:bg-gray-50 ${selected === r.number ? "bg-gray-100" : ""}`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-sm font-semibold">{r.code}</span>
                  <Badge status={r.status} />
                </div>
                <div className="mt-1 truncate text-sm font-medium">{r.hospital.name}</div>
                <div className="truncate text-xs text-gray-500">
                  {r.amount} · {r.paid ? "paid" : "asked"}
                </div>
                <div className="mt-1 text-xs text-gray-400">{ago(r.created_at)}</div>
              </button>
            </li>
          ))}
        </ul>
      </aside>
      <main className="min-w-0 flex-1 overflow-auto">
        {selected !== null ? (
          <ReportDetail key={selected} number={selected} />
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-gray-400">Select a report</div>
        )}
      </main>
    </div>
  );
}

function ReportDetail({ number }: { number: number }) {
  const api = useApi();
  const { data: r, error, setData } = usePoll<Detail>(`/reports/${number}`);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  if (error && !r) return <p className="p-6 text-sm text-rose-600">{error}</p>;
  if (!r) return <p className="p-6 text-sm text-gray-400">Loading…</p>;
  const decided = r.status === "taken_up" || r.status === "closed";

  async function decide(action: "take_up" | "ask" | "close") {
    setBusy(action);
    setActionError(null);
    try {
      setData(await api<Detail>(`/reports/${number}/${action}`, { method: "POST", body: JSON.stringify({ message }) }));
      setMessage("");
    } catch (e) {
      setActionError((e as Error).message);
    } finally {
      setBusy(null);
    }
  }

  const facts: [string, ReactNode][] = [
    ["Hospital", <>{r.hospital.name}<div className="text-xs text-gray-500" lang="ar">{r.hospital.name_ar}</div><Kind h={r.hospital} /></>],
    ["Patient", r.patient],
    ["Patient's cover", COVER[r.situation.patient_cover] ?? r.situation.patient_cover],
    ...(r.situation.injury !== "none" ? [["Injury", r.situation.injury === "war" ? "Wounded in the war" : "Wounded in the port explosion"] as [string, ReactNode]] : []),
    ["Date", r.incident_date],
    ["Amount", `${r.amount} (${r.paid ? "paid" : "asked, not paid"})`],
    ...(r.note ? [["What happened", r.note] as [string, ReactNode]] : []),
  ];

  return (
    <div className="mx-auto max-w-4xl space-y-4 p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="font-mono text-2xl font-semibold">{r.code}</h2>
            <Badge status={r.status} />
          </div>
          <div className="mt-1 text-gray-700">Charged while covered in full</div>
        </div>
        <div className="text-sm text-gray-500">Reported {when(r.created_at)}</div>
      </div>

      <div className="rounded-lg bg-blue-50 px-4 py-3 text-sm text-blue-900 ring-1 ring-blue-200 ring-inset">
        <div className="font-medium">The ministry's rule Wasel applied</div>
        <div className="mt-1">{r.rule.rule}{r.rule.condition && ` Only ${r.rule.condition}.`}</div>
        {r.rule.limits && <div className="mt-1 text-blue-800/80">{r.rule.limits}</div>}
        <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1">
          {r.rule.sources.map((s) => (
            <a key={s.key} href={s.url} target="_blank" rel="noreferrer" className="text-xs text-blue-700 hover:underline">
              {day(s.date)}: {s.title}
            </a>
          ))}
        </div>
      </div>
      <p className="text-xs text-gray-500">
        Wasel does not judge items or prices on the bill, and accuses no one. This report is for the desk to decide.
      </p>

      <Section title="Report">
        <dl className="divide-y divide-gray-100">
          {facts.map(([label, value]) => (
            <div key={label} className="grid gap-1 py-2 text-sm sm:grid-cols-5 sm:gap-4">
              <dt className="text-gray-500 sm:col-span-2">{label}</dt>
              <dd className="font-medium sm:col-span-3">{value}</dd>
            </div>
          ))}
        </dl>
      </Section>

      <Section title={`Bill and papers (${r.documents.length})`}>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {r.documents.map((d, i) => (
            <a key={i} href={d.url} target="_blank" rel="noreferrer" className="overflow-hidden rounded-md border border-gray-200 hover:border-gray-400">
              <Thumb url={d.url} />
              <div className="p-2">
                <div className="text-xs font-medium">{d.kind === "bill" ? "Bill" : "Other paper"}</div>
                {d.description && <div className="mt-0.5 line-clamp-3 text-xs text-gray-500">{d.description}</div>}
              </div>
            </a>
          ))}
        </div>
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

      {!decided && (
        <Section title="Decision">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            rows={2}
            placeholder="Note to the patient: required to ask for more or to close, optional to take it up"
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none"
          />
          <p className="mt-1 text-xs text-gray-500">Wasel tells the patient on WhatsApp, in their own language, as soon as you decide.</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <button
              onClick={() => decide("take_up")}
              disabled={busy !== null}
              className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
            >
              {busy === "take_up" ? "Sending…" : "Take it up with the hospital"}
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
              onClick={() => decide("close")}
              disabled={busy !== null || !message.trim()}
              className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              {busy === "close" ? "Closing…" : "Close"}
            </button>
          </div>
          {actionError && <p className="mt-2 text-sm text-rose-600">{actionError}</p>}
        </Section>
      )}
    </div>
  );
}

function ByHospital() {
  const { data, error } = usePoll<Group[]>("/hospitals");
  if (error && !data) return <p className="p-6 text-sm text-rose-600">{error}</p>;
  if (!data) return <p className="p-6 text-sm text-gray-400">Loading…</p>;
  return (
    <div className="mx-auto h-full max-w-5xl overflow-auto p-6">
      <p className="mb-4 text-sm text-gray-600">
        Reports per hospital, each with its bill: the evidence for the joint follow-up agreed with the Hospitals Syndicate on 1 Oct 2026.
      </p>
      {data.length === 0 ? (
        <p className="text-sm text-gray-500">No reports yet.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
          <table className="w-full text-sm">
            <thead className="border-b border-gray-200 text-left text-xs text-gray-500 uppercase">
              <tr>
                <th className="px-4 py-2 font-semibold">Hospital</th>
                <th className="px-4 py-2 text-right font-semibold">Reports</th>
                <th className="px-4 py-2 text-right font-semibold">Open</th>
                <th className="px-4 py-2 text-right font-semibold">Taken up</th>
                <th className="px-4 py-2 font-semibold">Amounts asked</th>
                <th className="px-4 py-2 font-semibold">Latest</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.map((g) => (
                <tr key={g.hospital.id} className="align-top">
                  <td className="px-4 py-3">
                    <div className="font-medium">{g.hospital.name}</div>
                    <div className="text-xs text-gray-500" lang="ar">{g.hospital.name_ar}</div>
                    <Kind h={g.hospital} />
                  </td>
                  <td className="px-4 py-3 text-right text-base font-semibold">{g.reports}</td>
                  <td className="px-4 py-3 text-right">{g.open}</td>
                  <td className="px-4 py-3 text-right">{g.taken_up}</td>
                  <td className="px-4 py-3 text-xs text-gray-600">
                    {g.amounts.map((a, i) => (
                      <div key={i}>
                        <span className="font-mono text-gray-400">{g.codes[i]}</span> {a}
                      </div>
                    ))}
                  </td>
                  <td className="px-4 py-3 text-xs whitespace-nowrap text-gray-500">{ago(g.last_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function RulesView() {
  const { data } = usePoll<Rules>("/rules");
  if (!data) return <p className="p-6 text-sm text-gray-400">Loading…</p>;
  const gov = data.listed.filter((h) => h.kind === "government");
  const priv = data.listed.filter((h) => h.kind === "private");
  return (
    <div className="mx-auto h-full max-w-4xl space-y-4 overflow-auto p-6">
      <Section title="How the rule changed">
        <ol className="space-y-3">
          {data.timeline.map((t) => (
            <li key={t.date} className="grid gap-1 text-sm sm:grid-cols-5 sm:gap-4">
              <div className="text-gray-500">{day(t.date)}</div>
              <div className="sm:col-span-4">
                <div className="font-medium">{t.change}</div>
                <a href={t.url} target="_blank" rel="noreferrer" className="text-xs text-blue-600 hover:underline" lang="ar">
                  {t.title}
                </a>
              </div>
            </li>
          ))}
        </ol>
      </Section>
      <Section title={`Hospitals that must give 100% cover (${data.listed.length})`}>
        <p className="mb-3 text-xs text-gray-500">
          From the circular of 14 Mar 2026 (
          <a href={data.list.pdf} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">PDF</a>
          ). {data.list.note}
        </p>
        <div className="grid gap-4 sm:grid-cols-2">
          {[["Government", gov], ["Private", priv]].map(([label, rows]) => (
            <div key={label as string}>
              <div className="mb-1 text-xs font-semibold text-gray-500">{label as string} ({(rows as Rules["listed"]).length})</div>
              <ul className="columns-2 text-sm" lang="ar" dir="rtl">
                {(rows as Rules["listed"]).map((h) => <li key={h.name_ar}>{h.name_ar}</li>)}
              </ul>
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}

function Thumb({ url }: { url: string }) {
  const [failed, setFailed] = useState(false);
  if (failed) return <div className="flex h-32 items-center justify-center bg-gray-100 text-xs text-gray-400">Open file ↗</div>;
  return <img src={url} alt="" onError={() => setFailed(true)} className="h-32 w-full bg-gray-100 object-cover" />;
}
