import React, { useEffect, useState } from "react";
import { Download, Search } from "lucide-react";
import { complianceApi } from "../services/complianceApi.js";

const ACTION_COLORS = {
  CREATE: "bg-emerald-100 text-emerald-700",
  CREATED: "bg-emerald-100 text-emerald-700",
  UPDATE: "bg-blue-100 text-blue-700",
  UPDATED: "bg-blue-100 text-blue-700",
  DELETE: "bg-red-100 text-red-700",
  DELETED: "bg-red-100 text-red-700",
  LOGIN_FAILED: "bg-orange-100 text-orange-700",
  ACCOUNT_LOCKED: "bg-orange-100 text-orange-700",
  PERMISSION_DENIED: "bg-orange-100 text-orange-700",
};

function actionClass(action = "") {
  const hit = Object.keys(ACTION_COLORS).find((key) => action.includes(key));
  return ACTION_COLORS[hit] || "bg-slate-100 text-slate-700";
}

export default function AuditLogs() {
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [filters, setFilters] = useState({ user_id: "", action: "", resource_type: "", date_from: "", date_to: "", page: 1, page_size: 20 });
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);

  const cleanParams = () => Object.fromEntries(Object.entries(filters).filter(([, v]) => v !== ""));

  const load = async () => {
    setLoading(true);
    const res = await complianceApi.getAuditLogs(cleanParams());
    if (res.ok) {
      setLogs(res.data.logs || []);
      setTotal(res.data.total_count || 0);
    }
    setLoading(false);
  };

  useEffect(() => { load(); }, [filters.page]);

  const openDetail = async (id) => {
    const res = await complianceApi.getAuditLogDetail(id);
    if (res.ok) setSelected(res.data);
  };

  const exportCsv = async () => {
    const res = await complianceApi.exportAuditLogs(cleanParams());
    if (res.ok) {
      const url = URL.createObjectURL(res.blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "audit_logs.csv";
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  const visible = logs.filter((log) => {
    const term = search.toLowerCase();
    return !term || [log.action, log.resource_type, log.resource_id, log.user_email_masked, log.ip_address].some((v) => String(v || "").toLowerCase().includes(term));
  });

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-6">
      <div className="mx-auto max-w-7xl">
        <header className="mb-5 flex items-center justify-between border-b pb-5">
          <div>
            <h1 className="text-2xl font-semibold">Audit Logs</h1>
            <p className="text-sm text-slate-500">{total} compliance events</p>
          </div>
          <button onClick={exportCsv} className="inline-flex items-center gap-2 rounded border px-3 py-2 text-sm hover:bg-white">
            <Download className="h-4 w-4" /> Export CSV
          </button>
        </header>

        <section className="mb-4 grid gap-3 md:grid-cols-6">
          <div className="flex items-center gap-2 rounded border bg-white px-3 py-2 md:col-span-2">
            <Search className="h-4 w-4 text-slate-400" />
            <input className="w-full text-sm outline-none" placeholder="Search logs" value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
          {[
            ["user_id", "User ID"],
            ["action", "Action"],
            ["resource_type", "Resource"],
            ["date_from", "From"],
            ["date_to", "To"],
          ].map(([key, label]) => (
            <input
              key={key}
              type={key.startsWith("date") ? "date" : "text"}
              className="rounded border px-3 py-2 text-sm"
              placeholder={label}
              value={filters[key]}
              onChange={(e) => setFilters({ ...filters, [key]: e.target.value, page: 1 })}
            />
          ))}
          <button onClick={load} className="rounded bg-slate-900 px-3 py-2 text-sm text-white">Apply</button>
        </section>

        <div className="overflow-x-auto rounded border bg-white">
          <table className="w-full text-left text-sm">
            <thead className="border-b bg-slate-50">
              <tr>
                {["Timestamp", "User", "Action", "Resource Type", "Resource ID", "Status", "IP Address"].map((h) => <th key={h} className="px-3 py-3">{h}</th>)}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={7} className="px-3 py-8 text-center text-slate-400">Loading audit logs...</td></tr>
              ) : visible.length === 0 ? (
                <tr><td colSpan={7} className="px-3 py-8 text-center text-slate-400">No audit logs found.</td></tr>
              ) : visible.map((log) => (
                <tr key={log.id} onClick={() => openDetail(log.id)} className="cursor-pointer border-b hover:bg-slate-50">
                  <td className="px-3 py-3 text-xs text-slate-500">{new Date(log.created_at).toLocaleString()}</td>
                  <td className="px-3 py-3">{log.user_email_masked || log.user_id || "System"}</td>
                  <td className="px-3 py-3"><span className={`rounded px-2 py-1 text-xs font-medium ${actionClass(log.action)}`}>{log.action}</span></td>
                  <td className="px-3 py-3">{log.resource_type}</td>
                  <td className="max-w-xs truncate px-3 py-3 text-slate-500">{log.resource_id}</td>
                  <td className="px-3 py-3">{log.status}</td>
                  <td className="px-3 py-3 text-slate-500">{log.ip_address || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-4 flex items-center justify-between">
          <button disabled={filters.page <= 1} onClick={() => setFilters({ ...filters, page: filters.page - 1 })} className="rounded border px-3 py-2 text-sm disabled:opacity-40">Previous</button>
          <span className="text-sm text-slate-500">Page {filters.page}</span>
          <button onClick={() => setFilters({ ...filters, page: filters.page + 1 })} className="rounded border px-3 py-2 text-sm">Next</button>
        </div>
      </div>

      {selected && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="max-h-[90vh] w-full max-w-3xl overflow-auto rounded border bg-white p-5 shadow-xl">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-semibold">Audit Detail</h2>
              <button onClick={() => setSelected(null)} className="text-xl text-slate-400 hover:text-slate-700">&times;</button>
            </div>
            <pre className="overflow-auto rounded bg-slate-50 p-4 text-xs">{JSON.stringify(selected, null, 2)}</pre>
          </div>
        </div>
      )}
    </main>
  );
}
