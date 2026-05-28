import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Bug, Filter, RefreshCw, Download } from "lucide-react";
import { monitoringApi } from "../services/monitoringApi.js";

const SEVERITY_BADGE = {
  critical: "bg-red-100 text-red-700",
  high: "bg-orange-100 text-orange-700",
  medium: "bg-yellow-100 text-yellow-700",
  low: "bg-blue-100 text-blue-700",
};

function ErrorCard({ entry }) {
  const a = entry;
  return (
    <div className="rounded border bg-white p-5 shadow-sm space-y-3">
      <div className="flex items-start justify-between gap-3">
        <p className="font-semibold text-slate-900 leading-snug">{a.title}</p>
        <span className={`shrink-0 rounded px-2 py-0.5 text-xs font-medium ${SEVERITY_BADGE[a.severity] || ""}`}>
          {a.severity}
        </span>
      </div>
      {a.description && (
        <div className="space-y-1 text-sm text-slate-600">
          {a.description.split("\n").filter(Boolean).map((line, i) => (
            <p key={i}>{line}</p>
          ))}
        </div>
      )}
      {a.recommended_action && (
        <div>
          <p className="text-xs font-medium text-slate-700 mb-1">Recommended Steps</p>
          <ol className="ml-4 list-decimal space-y-1 text-sm text-slate-600">
            {a.recommended_action.split("\n").filter(Boolean).map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ol>
        </div>
      )}
      <div className="flex items-center justify-between text-xs text-slate-400">
        <span>Service: {a.affected_service || "—"}</span>
        <span>{new Date(a.created_at).toLocaleString()}</span>
      </div>
    </div>
  );
}

export default function DebuggingAssistant() {
  const [history, setHistory] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState("");
  const [page, setPage] = useState(1);

  const load = async (p = 1) => {
    setLoading(true);
    const params = { page: p, page_size: 20 };
    if (severityFilter) params.severity = severityFilter;
    const [hRes, iRes] = await Promise.all([
      monitoringApi.getDebuggingHistory(params),
      monitoringApi.getIncidents(),
    ]);
    if (hRes.ok) setHistory(hRes.data || []);
    if (iRes.ok) setIncidents(iRes.data || []);
    setLoading(false);
  };

  useEffect(() => { load(page); }, [page, severityFilter]);

  const exportReport = () => {
    const content = JSON.stringify(history, null, 2);
    const blob = new Blob([content], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `debugging_report_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-6">
      <div className="mx-auto max-w-6xl">
        <header className="mb-6 flex flex-col gap-3 border-b pb-5 md:flex-row md:items-center md:justify-between">
          <div>
            <Link to="/monitoring" className="text-sm text-slate-500 hover:text-slate-700">← Monitoring</Link>
            <h1 className="mt-1 flex items-center gap-2 text-2xl font-semibold">
              <Bug className="h-6 w-6 text-slate-600" /> Debugging Assistant
            </h1>
            <p className="text-sm text-slate-500">Super Admin only — AI-analyzed error logs with plain English explanations</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <select value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)} className="rounded border border-slate-300 px-3 py-1.5 text-sm">
              <option value="">All severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
            <button onClick={() => load(page)} className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-white">
              <RefreshCw className="h-4 w-4" />
            </button>
            <button onClick={exportReport} className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-white">
              <Download className="h-4 w-4" /> Export
            </button>
          </div>
        </header>

        {/* Error analysis cards */}
        <section className="mb-8">
          <h2 className="mb-4 font-semibold text-slate-700">Analyzed Errors</h2>
          {loading ? (
            <p className="text-sm text-slate-400">Loading…</p>
          ) : history.length === 0 ? (
            <p className="rounded border border-dashed border-slate-300 p-8 text-center text-sm text-slate-400">
              No analyzed errors yet. The system analyzes new errors every 10 minutes.
            </p>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {history.map((entry) => <ErrorCard key={entry.id} entry={entry} />)}
            </div>
          )}
          {/* Pagination */}
          <div className="mt-4 flex gap-3 text-sm text-slate-500">
            <button disabled={page <= 1} onClick={() => setPage(p => p - 1)} className="rounded border px-3 py-1.5 disabled:opacity-40">Previous</button>
            <span>Page {page}</span>
            <button onClick={() => setPage(p => p + 1)} disabled={history.length < 20} className="rounded border px-3 py-1.5 disabled:opacity-40">Next</button>
          </div>
        </section>

        {/* Incident reports */}
        <section>
          <h2 className="mb-4 font-semibold text-slate-700">Incident Reports with AI Summaries</h2>
          {incidents.length === 0 ? (
            <p className="text-sm text-slate-400">No incidents recorded.</p>
          ) : (
            <div className="space-y-3">
              {incidents.map((inc) => (
                <div key={inc.id} className="rounded border bg-white p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-medium text-slate-900">{inc.title}</p>
                      <p className="text-sm text-slate-500 mt-1">{inc.description}</p>
                    </div>
                    <span className={`shrink-0 rounded px-2 py-0.5 text-xs font-medium ${SEVERITY_BADGE[inc.severity] || ""}`}>
                      {inc.severity}
                    </span>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-4 text-xs text-slate-400">
                    <span>Errors: {inc.error_count}</span>
                    <span>Status: {inc.status}</span>
                    {inc.first_occurrence && <span>First: {new Date(inc.first_occurrence).toLocaleDateString()}</span>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
