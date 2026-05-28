import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Activity, AlertTriangle, Clock, RefreshCw,
  Users, Zap, FileX, TrendingUp, ShieldAlert, BarChart3
} from "lucide-react";
import { monitoringApi } from "../services/monitoringApi.js";

const RISK_COLORS = {
  low: "bg-emerald-50 border-emerald-200 text-emerald-800",
  medium: "bg-yellow-50 border-yellow-200 text-yellow-800",
  high: "bg-orange-50 border-orange-200 text-orange-800",
  critical: "bg-red-50 border-red-200 text-red-800",
};

const SEVERITY_BADGE = {
  critical: "bg-red-100 text-red-700",
  high: "bg-orange-100 text-orange-700",
  medium: "bg-yellow-100 text-yellow-700",
  low: "bg-blue-100 text-blue-700",
};

function StatCard({ icon: Icon, label, value, sub, color = "slate" }) {
  const colors = { slate: "bg-white", green: "bg-emerald-50", red: "bg-red-50", yellow: "bg-yellow-50", blue: "bg-blue-50" };
  return (
    <div className={`rounded border p-4 shadow-sm ${colors[color]}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-500">{label}</span>
        <Icon className="h-4 w-4 text-slate-400" />
      </div>
      <div className="mt-2 text-2xl font-semibold text-slate-900">{value ?? "—"}</div>
      {sub && <div className="mt-1 text-xs text-slate-400">{sub}</div>}
    </div>
  );
}

function SimpleBar({ label, value, max, color = "bg-blue-400" }) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0;
  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="w-48 truncate text-slate-600">{label}</span>
      <div className="flex-1 rounded bg-slate-100 h-2">
        <div className={`h-2 rounded ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-12 text-right text-slate-500">{value}</span>
    </div>
  );
}

export default function MonitoringDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);

  const load = async () => {
    setLoading(true);
    const res = await monitoringApi.getDashboard();
    if (res.ok) { setData(res.data); setLastUpdated(new Date()); }
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const m = data?.system_metrics;
  const health = data?.health_summary;
  const riskColor = RISK_COLORS[health?.risk_level] || RISK_COLORS.low;
  const maxCalls = Math.max(...(data?.top_endpoints || []).map(e => e.call_count), 1);

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-6">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <header className="mb-6 flex flex-col gap-3 border-b pb-5 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">Monitoring Dashboard</h1>
            <p className="text-sm text-slate-500">
              {lastUpdated ? `Updated ${lastUpdated.toLocaleTimeString()}` : "Loading…"}
            </p>
          </div>
          <div className="flex flex-wrap gap-2 text-sm">
            {[
              { label: "Alerts", to: "/monitoring/alerts" },
              { label: "AI Trust", to: "/monitoring/ai-trust" },
              { label: "Debugging", to: "/monitoring/debugging" },
            ].map(({ label, to }) => (
              <Link key={label} to={to} className="rounded border px-3 py-1.5 text-slate-600 hover:bg-white">{label}</Link>
            ))}
            <button onClick={load} className="flex items-center gap-1 rounded border px-3 py-1.5 hover:bg-white">
              <RefreshCw className="h-4 w-4" /> Refresh
            </button>
          </div>
        </header>

        {loading && !data ? (
          <p className="text-sm text-slate-400">Loading monitoring data…</p>
        ) : (
          <>
            {/* Health banner */}
            {health && (
              <div className={`mb-6 rounded border p-4 ${riskColor}`}>
                <div className="flex items-start gap-3">
                  <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0" />
                  <div>
                    <p className="font-semibold capitalize">System risk: {health.risk_level}</p>
                    <p className="mt-1 text-sm">{health.summary_text}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Stats row */}
            <div className="mb-6 grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
              <StatCard icon={Users} label="Active Users" value={m?.active_users} />
              <StatCard icon={Activity} label="API Calls" value={m?.total_api_calls} sub={`${m?.period || "24h"} period`} />
              <StatCard
                icon={AlertTriangle}
                label="Error Rate"
                value={`${m?.error_rate_percent ?? 0}%`}
                color={m?.error_rate_percent > 10 ? "red" : "green"}
              />
              <StatCard
                icon={Clock}
                label="Avg Response"
                value={`${m?.avg_response_time_ms ?? 0}ms`}
                color={m?.avg_response_time_ms > 3000 ? "yellow" : "slate"}
              />
              <StatCard icon={Zap} label="AI Queries" value={m?.total_ai_queries} />
            </div>

            <div className="grid gap-6 lg:grid-cols-2">
              {/* Response time trend */}
              <div className="rounded border bg-white p-4">
                <h2 className="mb-4 flex items-center gap-2 font-semibold text-slate-800">
                  <TrendingUp className="h-4 w-4" /> Response Time Trend (24h)
                </h2>
                {(data?.response_time_trend || []).length === 0 ? (
                  <p className="text-sm text-slate-400">No data available.</p>
                ) : (
                  <div className="space-y-1.5">
                    {(data.response_time_trend || []).slice(-12).map((pt, i) => (
                      <SimpleBar
                        key={i}
                        label={pt.timestamp ? new Date(pt.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : ""}
                        value={Math.round(pt.avg_response_time_ms)}
                        max={Math.max(...(data.response_time_trend || []).map(p => p.avg_response_time_ms), 1)}
                        color={pt.avg_response_time_ms > 3000 ? "bg-red-400" : "bg-blue-400"}
                      />
                    ))}
                  </div>
                )}
              </div>

              {/* Error trend */}
              <div className="rounded border bg-white p-4">
                <h2 className="mb-4 flex items-center gap-2 font-semibold text-slate-800">
                  <FileX className="h-4 w-4" /> Error Trend (24h)
                </h2>
                {(data?.error_trend || []).length === 0 ? (
                  <p className="text-sm text-slate-400">No errors recorded.</p>
                ) : (
                  <div className="space-y-1.5">
                    {(data.error_trend || []).slice(-12).map((pt, i) => (
                      <SimpleBar
                        key={i}
                        label={pt.timestamp ? new Date(pt.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : ""}
                        value={pt.error_count}
                        max={Math.max(...(data.error_trend || []).map(p => p.error_count), 1)}
                        color="bg-red-400"
                      />
                    ))}
                  </div>
                )}
              </div>

              {/* Active alerts */}
              <div className="rounded border bg-white p-4">
                <h2 className="mb-4 flex items-center gap-2 font-semibold text-slate-800">
                  <AlertTriangle className="h-4 w-4" /> Active Alerts
                </h2>
                {(data?.active_alerts || []).length === 0 ? (
                  <p className="text-sm text-emerald-600">No active alerts. System looks healthy.</p>
                ) : (
                  <ul className="divide-y divide-slate-100">
                    {(data.active_alerts || []).map((alert) => (
                      <li key={alert.id} className="py-2">
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-sm font-medium text-slate-800">{alert.title}</span>
                          <span className={`rounded px-2 py-0.5 text-xs font-medium ${SEVERITY_BADGE[alert.severity] || ""}`}>
                            {alert.severity}
                          </span>
                        </div>
                        <p className="text-xs text-slate-400">{alert.affected_service}</p>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              {/* Top endpoints */}
              <div className="rounded border bg-white p-4">
                <h2 className="mb-4 flex items-center gap-2 font-semibold text-slate-800">
                  <BarChart3 className="h-4 w-4" /> Top Endpoints (24h)
                </h2>
                {(data?.top_endpoints || []).length === 0 ? (
                  <p className="text-sm text-slate-400">No endpoint data available.</p>
                ) : (
                  <div className="space-y-1.5">
                    {(data.top_endpoints || []).map((ep, i) => (
                      <SimpleBar
                        key={i}
                        label={ep.endpoint}
                        value={ep.call_count}
                        max={maxCalls}
                        color="bg-slate-600"
                      />
                    ))}
                  </div>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </main>
  );
}
