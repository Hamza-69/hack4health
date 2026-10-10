import { useEffect, useState } from "react";
import { useOutletContext } from "react-router";
import { api, type Ticket, type TicketStatus } from "../api";
import type { LayoutContext } from "../Layout";

const STATUSES: TicketStatus[] = ["active", "awaiting_user", "resolved", "archived"];

const statusClass: Record<TicketStatus, string> = {
  active: "bg-blue-100 text-blue-800",
  awaiting_user: "bg-amber-100 text-amber-800",
  resolved: "bg-green-100 text-green-800",
  archived: "bg-gray-200 text-gray-700",
};

export default function Tickets() {
  const { modules } = useOutletContext<LayoutContext>();
  const [status, setStatus] = useState("");
  const [kind, setKind] = useState("");
  const [tickets, setTickets] = useState<Ticket[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const query = new URLSearchParams();
    if (status) query.set("status", status);
    if (kind) query.set("kind", kind);
    api<Ticket[]>(`/admin/tickets?${query}`)
      .then(setTickets)
      .catch((e) => setError(e.message));
  }, [status, kind]);

  return (
    <div className="mx-auto max-w-5xl p-6">
      <div className="mb-4 flex items-center gap-3">
        <h1 className="mr-auto text-xl font-semibold">Tickets</h1>
        <select value={kind} onChange={(e) => setKind(e.target.value)} className="rounded-md border border-gray-300 px-2 py-1 text-sm">
          <option value="">All modules</option>
          {modules.map((m) => (
            <option key={m.name} value={m.name}>
              {m.title}
            </option>
          ))}
        </select>
        <select value={status} onChange={(e) => setStatus(e.target.value)} className="rounded-md border border-gray-300 px-2 py-1 text-sm">
          <option value="">All statuses</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s.replace("_", " ")}
            </option>
          ))}
        </select>
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
      {tickets?.length === 0 && <p className="text-sm text-gray-500">No tickets.</p>}
      {tickets && tickets.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-gray-200 text-gray-500">
              <tr>
                <th className="px-4 py-2 font-medium">Title</th>
                <th className="px-4 py-2 font-medium">Module</th>
                <th className="px-4 py-2 font-medium">Status</th>
                <th className="px-4 py-2 font-medium">Resolution</th>
                <th className="px-4 py-2 font-medium">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {tickets.map((t) => (
                <tr key={t.id}>
                  <td className="px-4 py-2">
                    <div className="font-medium">{t.title}</div>
                    {t.details && <div className="text-gray-500">{t.details}</div>}
                  </td>
                  <td className="px-4 py-2">{modules.find((m) => m.name === t.kind)?.title ?? t.kind}</td>
                  <td className="px-4 py-2">
                    <span className={`rounded-full px-2 py-0.5 text-xs whitespace-nowrap ${statusClass[t.status]}`}>
                      {t.status.replace("_", " ")}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-gray-600">{t.resolution ?? "—"}</td>
                  <td className="px-4 py-2 whitespace-nowrap text-gray-500">{new Date(t.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
