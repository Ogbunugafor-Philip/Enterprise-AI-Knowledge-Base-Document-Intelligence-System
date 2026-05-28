import React, { useEffect, useMemo, useState } from "react";
import { Download, RefreshCw, ShieldCheck, ShieldAlert } from "lucide-react";
import { securityApi } from "../services/securityApi.js";

const SEVERITY = {
  critical: "bg-red-100 text-red-700",
  high: "bg-orange-100 text-orange-700",
  medium: "bg-yellow-100 text-yellow-700",
  low: "bg-blue-100 text-blue-700",
};

export default function SecurityDashboard() {
  const [report, setReport] = useState(null);
  const [rateLimits, setRateLimits] = useState([]);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    const [checkRes, rateRes, eventRes] = await Promise.all([
      securityApi.getSecurityChecklist(),
      securityApi.getRateLimitStatus(),
      securityApi.getSecurityEvents(),
    ]);
    if (checkRes.ok) setReport(checkRes.data);
    if (rateRes.ok) setRateLimits(rateRes.data.items || []);
    if (eventRes.ok) setEvents(eventRes.data || []);
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const score = useMemo(() => {
    const checks = report?.checks || [];
    if (!checks.length) return 0;
    return Math.round((checks.filter((check) => check.status === "PASS").length / checks.length) * 100);
  }, [report]);

  const exportReport = () => {
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "security_report.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-6">
      <div className="mx-auto max-w-7xl">
        <header className="mb-6 flex items-center justify-between border-b pb-5">
          <div>
            <h1 className="text-2xl font-semibold">Security Dashboard</h1>
            <p className="text-sm text-slate-500">Security posture, rate limits, and recent security events.</p>
          </div>
          <div className="flex gap-2">
            <button onClick={load} className="inline-flex items-center gap-2 rounded border px-3 py-2 text-sm hover:bg-white">
              <RefreshCw className="h-4 w-4" /> Refresh
            </button>
            <button onClick={exportReport} disabled={!report} className="inline-flex items-center gap-2 rounded bg-slate-900 px-3 py-2 text-sm text-white disabled:opacity-50">
              <Download className="h-4 w-4" /> Export Report
            </button>
          </div>
        </header>

        {loading && !report ? <p className="text-sm text-slate-400">Loading security data...</p> : (
          <>
            <section className="mb-6 grid gap-4 md:grid-cols-4">
              <div className="rounded border bg-white p-4">
                <p className="text-xs font-medium text-slate-500">Security Score</p>
                <div className="mt-2 flex items-center gap-3">
                  {score >= 80 ? <ShieldCheck className="h-8 w-8 text-emerald-600" /> : <ShieldAlert className="h-8 w-8 text-red-600" />}
                  <span className="text-3xl font-semibold">{score}%</span>
                </div>
              </div>
              <div className="rounded border bg-white p-4">
                <p className="text-xs font-medium text-slate-500">Critical Failures</p>
                <p className="mt-2 text-3xl font-semibold text-red-700">{report?.critical_failures || 0}</p>
              </div>
              <div className="rounded border bg-white p-4">
                <p className="text-xs font-medium text-slate-500">High Failures</p>
                <p className="mt-2 text-3xl font-semibold text-orange-700">{report?.high_failures || 0}</p>
              </div>
              <div className="rounded border bg-white p-4">
                <p className="text-xs font-medium text-slate-500">Overall Status</p>
                <p className={`mt-2 inline-flex rounded px-2 py-1 text-sm font-medium ${report?.overall_status === "PASS" ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"}`}>
                  {report?.overall_status || "UNKNOWN"}
                </p>
              </div>
            </section>

            <section className="mb-6 rounded border bg-white">
              <div className="border-b px-4 py-3 font-semibold">Security Checklist</div>
              <div className="divide-y">
                {(report?.checks || []).map((check) => (
                  <div key={check.check_name} className={`grid gap-3 px-4 py-3 md:grid-cols-[160px_1fr_120px] ${check.status === "FAIL" && check.severity === "critical" ? "bg-red-50" : ""}`}>
                    <div>
                      <span className={`rounded px-2 py-1 text-xs font-semibold ${check.status === "PASS" ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"}`}>{check.status}</span>
                    </div>
                    <div>
                      <p className="font-medium text-slate-900">{check.check_name}</p>
                      <p className="text-sm text-slate-500">{check.description}</p>
                      {check.status === "FAIL" && <p className="mt-1 text-sm text-red-700">{check.recommendation}</p>}
                    </div>
                    <span className={`h-fit rounded px-2 py-1 text-xs font-medium ${SEVERITY[check.severity] || SEVERITY.medium}`}>{check.severity}</span>
                  </div>
                ))}
              </div>
            </section>

            <section className="grid gap-6 lg:grid-cols-2">
              <div className="rounded border bg-white p-4">
                <h2 className="mb-3 font-semibold">Rate Limit Status</h2>
                {(rateLimits || []).length === 0 ? <p className="text-sm text-slate-400">No active in-memory rate limit buckets.</p> : (
                  <div className="space-y-2 text-sm">
                    {rateLimits.map((item) => (
                      <div key={item.key} className="rounded border px-3 py-2">
                        <p className="font-medium">{item.key}</p>
                        <p className="text-xs text-slate-500">Count {item.count} resets {item.reset_at}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="rounded border bg-white p-4">
                <h2 className="mb-3 font-semibold">Recent Security Events</h2>
                {(events || []).length === 0 ? <p className="text-sm text-slate-400">No recent security events.</p> : (
                  <table className="w-full text-left text-sm">
                    <thead><tr className="border-b"><th className="py-2">Time</th><th>Type</th><th>IP</th><th>Endpoint</th></tr></thead>
                    <tbody>
                      {events.map((event, i) => (
                        <tr key={`${event.created_at}-${i}`} className="border-b">
                          <td className="py-2 text-xs text-slate-500">{new Date(event.created_at).toLocaleString()}</td>
                          <td>{event.event_type}</td>
                          <td>{event.ip_address || "-"}</td>
                          <td className="max-w-xs truncate">{event.endpoint || "-"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </section>
          </>
        )}
      </div>
    </main>
  );
}
