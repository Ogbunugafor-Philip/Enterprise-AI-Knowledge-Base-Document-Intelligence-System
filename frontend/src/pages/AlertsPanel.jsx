import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { AlertTriangle, CheckCircle, Eye, Filter, RefreshCw, X } from "lucide-react";
import { monitoringApi } from "../services/monitoringApi.js";

const SEVERITY_BADGE = {
  critical: "bg-red-100 text-red-700 border-red-200",
  high: "bg-orange-100 text-orange-700 border-orange-200",
  medium: "bg-yellow-100 text-yellow-700 border-yellow-200",
  low: "bg-blue-100 text-blue-700 border-blue-200",
};

export default function AlertsPanel() {
  const [alerts, setAlerts] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState("");
  const [selected, setSelected] = useState(null);
  const [toast, setToast] = useState("");

  const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(""), 3000); };

  const load = async () => {
    setLoading(true);
    const [aRes, iRes] = await Promise.all([
      monitoringApi.getAlerts(severityFilter || undefined),
      monitoringApi.getIncidents(),
    ]);
    if (aRes.ok) setAlerts(aRes.data || []);
    if (iRes.ok) setIncidents(iRes.data || []);
    setLoading(false);
  };

  useEffect(() => { load(); }, [severityFilter]);

  const updateStatus = async (id, status) => {
    const res = await monitoringApi.updateAlertStatus(id, { status });
    if (res.ok) { showToast(`Alert marked ${status}.`); load(); setSelected(null); }
    else showToast("Update failed: " + res.error);
  };

  const viewAlert = async (id) => {
    const res = await monitoringApi.getAlert(id);
    if (res.ok) setSelected(res.data);
  };

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-6">
      {toast && (
        <div className="fixed top-4 right-4 z-50 rounded bg-slate-900 px-4 py-2 text-sm text-white shadow">{toast}</div>
      )}

      {selected && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-xl rounded-lg border bg-white shadow-xl">
            <div className="flex items-center justify-between border-b px-5 py-4">
              <h2 className="font-semibold text-slate-900">Alert Details</h2>
              <button onClick={() => setSelected(null)}><X className="h-5 w-5 text-slate-400" /></button>
            </div>
            <div className="px-5 py-4 space-y-4 max-h-[70vh] overflow-y-auto">
              <div>
                <span className={`rounded border px-2 py-0.5 text-xs font-medium ${SEVERITY_BADGE[selected.alert?.severity] || ""}`}>
                  {selected.alert?.severity}
                </span>
                <p className="mt-2 font-semibold text-slate-900">{selected.alert?.title}</p>
                <p className="text-sm text-slate-500">{selected.alert?.affected_service}</p>
              </div>
              {selected.debugging_analysis && (
                <div className="rounded border bg-slate-50 p-4 space-y-2 text-sm">
                  <p className="font-medium text-slate-700">AI Debugging Analysis</p>
                  <p><strong>What happened:</strong> {selected.debugging_analysis.plain_english_explanation}</p>
                  <p><strong>Possible cause:</strong> {selected.debugging_analysis.possible_cause}</p>
                  <p><strong>Business impact:</strong> {selected.debugging_analysis.business_impact}</p>
                  <div>
                    <strong>Recommended steps:</strong>
                    <ol className="ml-4 mt-1 list-decimal space-y-1">
                      {(selected.debugging_analysis.recommended_steps || []).map((s, i) => (
                        <li key={i} className="text-slate-600">{s}</li>
                      ))}
                    </ol>
                  </div>
                </div>
              )}
              {selected.alert?.recommended_action && (
                <p className="text-sm text-slate-600"><strong>Recommendation:</strong> {selected.alert.recommended_action}</p>
              )}
              <div className="flex gap-2 pt-2">
                <button onClick={() => updateStatus(selected.alert.id, "investigating")} className="rounded border border-yellow-300 px-3 py-1.5 text-sm text-yellow-700 hover:bg-yellow-50">Mark Investigating</button>
                <button onClick={() => updateStatus(selected.alert.id, "resolved")} className="rounded border border-emerald-300 px-3 py-1.5 text-sm text-emerald-700 hover:bg-emerald-50">Mark Resolved</button>
                <button onClick={() => updateStatus(selected.alert.id, "ignored")} className="rounded border px-3 py-1.5 text-sm text-slate-500 hover:bg-slate-50">Ignore</button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="mx-auto max-w-6xl">
        <header className="mb-6 flex flex-col gap-3 border-b pb-5 md:flex-row md:items-center md:justify-between">
          <div>
            <Link to="/monitoring" className="text-sm text-slate-500 hover:text-slate-700">← Monitoring</Link>
            <h1 className="mt-1 text-2xl font-semibold">Alerts & Incidents</h1>
            <p className="text-sm text-slate-500">{alerts.length} active alerts</p>
          </div>
          <div className="flex gap-2">
            <select value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)} className="rounded border border-slate-300 px-3 py-1.5 text-sm">
              <option value="">All severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
            <button onClick={load} className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-white">
              <RefreshCw className="h-4 w-4" />
            </button>
          </div>
        </header>

        {/* Alerts */}
        <div className="mb-8 overflow-x-auto rounded border bg-white">
          <table className="w-full text-left text-sm">
            <thead className="border-b bg-slate-50">
              <tr>
                <th className="px-4 py-3">Alert</th>
                <th className="px-4 py-3">Severity</th>
                <th className="px-4 py-3">Service</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Created</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-slate-400">Loading…</td></tr>
              ) : alerts.length === 0 ? (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-emerald-600">No active alerts.</td></tr>
              ) : (
                alerts.map((alert) => (
                  <tr key={alert.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3 font-medium text-slate-900 max-w-xs truncate">{alert.title}</td>
                    <td className="px-4 py-3">
                      <span className={`rounded border px-2 py-0.5 text-xs font-medium ${SEVERITY_BADGE[alert.severity] || ""}`}>
                        {alert.severity}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-500">{alert.affected_service || "—"}</td>
                    <td className="px-4 py-3"><span className="rounded bg-slate-100 px-2 py-0.5 text-xs">{alert.status}</span></td>
                    <td className="px-4 py-3 text-slate-400 text-xs">{new Date(alert.created_at).toLocaleString()}</td>
                    <td className="px-4 py-3">
                      <div className="flex gap-1">
                        <button onClick={() => viewAlert(alert.id)} className="rounded border px-2 py-1 text-xs hover:bg-slate-100"><Eye className="h-3.5 w-3.5" /></button>
                        <button onClick={() => updateStatus(alert.id, "resolved")} className="rounded border border-emerald-300 px-2 py-1 text-xs text-emerald-600"><CheckCircle className="h-3.5 w-3.5" /></button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Incidents */}
        <h2 className="mb-4 font-semibold text-slate-800">Incident Reports</h2>
        {incidents.length === 0 ? (
          <p className="text-sm text-slate-400">No incidents recorded.</p>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {incidents.map((inc) => (
              <div key={inc.id} className="rounded border bg-white p-4 shadow-sm">
                <div className="flex items-start justify-between gap-2">
                  <p className="font-medium text-slate-900">{inc.title}</p>
                  <span className={`rounded border px-2 py-0.5 text-xs font-medium ${SEVERITY_BADGE[inc.severity] || ""}`}>{inc.severity}</span>
                </div>
                <p className="mt-1 text-sm text-slate-500 line-clamp-2">{inc.description}</p>
                <div className="mt-2 flex items-center justify-between text-xs text-slate-400">
                  <span>Errors: {inc.error_count}</span>
                  <span className="rounded bg-slate-100 px-2 py-0.5">{inc.status}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
