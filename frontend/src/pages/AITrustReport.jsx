import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ShieldCheck, RefreshCw, TrendingUp, AlertTriangle, CheckCircle } from "lucide-react";
import { monitoringApi } from "../services/monitoringApi.js";

const TRUST_COLORS = {
  high: { bg: "bg-emerald-50 border-emerald-200", text: "text-emerald-700", badge: "bg-emerald-100 text-emerald-700" },
  medium: { bg: "bg-yellow-50 border-yellow-200", text: "text-yellow-700", badge: "bg-yellow-100 text-yellow-700" },
  low: { bg: "bg-red-50 border-red-200", text: "text-red-700", badge: "bg-red-100 text-red-700" },
};

function ScoreBar({ label, value, max = 1.0, invert = false }) {
  const pct = Math.min(100, (value / max) * 100);
  const color = invert
    ? value > 0.6 ? "bg-red-400" : value > 0.3 ? "bg-yellow-400" : "bg-emerald-400"
    : value > 0.7 ? "bg-emerald-400" : value > 0.4 ? "bg-yellow-400" : "bg-red-400";
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span className="text-slate-600">{label}</span>
        <span className="font-medium text-slate-900">{(value * 100).toFixed(1)}%</span>
      </div>
      <div className="h-2 w-full rounded bg-slate-100">
        <div className={`h-2 rounded ${color} transition-all`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function AITrustReport() {
  const [report, setReport] = useState(null);
  const [trend, setTrend] = useState([]);
  const [lowFlags, setLowFlags] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    const [rRes, qRes, fRes] = await Promise.all([
      monitoringApi.getAITrustReport(),
      monitoringApi.getAIQuality(30),
      monitoringApi.getAlerts("high"),
    ]);
    if (rRes.ok) setReport(rRes.data);
    if (qRes.ok) setTrend(qRes.data?.response_quality_trend || []);
    if (fRes.ok) setLowFlags((fRes.data || []).filter(a => a.alert_type?.includes("confidence") || a.alert_type?.includes("hallucination")));
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const tc = TRUST_COLORS[report?.trust_level] || TRUST_COLORS.medium;

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-6">
      <div className="mx-auto max-w-5xl">
        <header className="mb-6 flex flex-col gap-3 border-b pb-5 md:flex-row md:items-center md:justify-between">
          <div>
            <Link to="/monitoring" className="text-sm text-slate-500 hover:text-slate-700">← Monitoring</Link>
            <h1 className="mt-1 flex items-center gap-2 text-2xl font-semibold">
              <ShieldCheck className="h-6 w-6 text-slate-600" /> AI Trust Report
            </h1>
            <p className="text-sm text-slate-500">Reliability and hallucination risk metrics for your AI knowledge engine</p>
          </div>
          <button onClick={load} className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-white">
            <RefreshCw className="h-4 w-4" /> Refresh
          </button>
        </header>

        {loading ? (
          <p className="text-sm text-slate-400">Loading AI trust data…</p>
        ) : (
          <>
            {/* Trust level banner */}
            {report && (
              <div className={`mb-6 rounded border p-5 ${tc.bg}`}>
                <div className="flex items-center gap-3">
                  {report.trust_level === "high" ? (
                    <CheckCircle className={`h-6 w-6 ${tc.text}`} />
                  ) : (
                    <AlertTriangle className={`h-6 w-6 ${tc.text}`} />
                  )}
                  <div>
                    <p className={`font-semibold capitalize ${tc.text}`}>
                      AI Trust Level: {report.trust_level}
                    </p>
                    <p className="text-sm text-slate-600 mt-0.5">
                      Based on {report.total_responses} total responses over the last 30 days
                    </p>
                  </div>
                  <span className={`ml-auto rounded px-3 py-1 text-sm font-medium ${tc.badge}`}>
                    {report.rejection_rate_percent}% rejected
                  </span>
                </div>
              </div>
            )}

            {/* Key metrics */}
            {report && (
              <div className="mb-6 grid gap-4 md:grid-cols-2">
                <div className="rounded border bg-white p-5 space-y-4">
                  <h2 className="font-semibold text-slate-800">Quality Scores</h2>
                  <ScoreBar label="Average Confidence Score" value={report.avg_confidence_score} />
                  <ScoreBar label="Hallucination Risk" value={report.avg_hallucination_risk} invert />
                  <ScoreBar label="Acceptance Rate" value={(report.total_responses - report.rejected_responses) / Math.max(1, report.total_responses)} />
                </div>
                <div className="rounded border bg-white p-5 space-y-3">
                  <h2 className="font-semibold text-slate-800">Response Summary</h2>
                  {[
                    ["Total AI Responses", report.total_responses],
                    ["Accepted Responses", report.total_responses - report.rejected_responses],
                    ["Rejected Responses", report.rejected_responses],
                    ["Rejection Rate", `${report.rejection_rate_percent}%`],
                  ].map(([label, value]) => (
                    <div key={label} className="flex justify-between text-sm">
                      <span className="text-slate-500">{label}</span>
                      <span className="font-medium text-slate-900">{value}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* AI-generated trust report text */}
            {report?.report_text && (
              <div className="mb-6 rounded border bg-white p-5">
                <h2 className="mb-3 font-semibold text-slate-800">AI Trust Analysis</h2>
                <p className="text-sm leading-relaxed text-slate-600 whitespace-pre-line">{report.report_text}</p>
                {report.generated_at && (
                  <p className="mt-3 text-xs text-slate-400">
                    Generated at {new Date(report.generated_at).toLocaleString()}
                  </p>
                )}
              </div>
            )}

            {/* Low confidence flags */}
            {lowFlags.length > 0 && (
              <div className="mb-6 rounded border bg-white p-5">
                <h2 className="mb-3 font-semibold text-slate-800">Low Confidence Alerts</h2>
                <ul className="divide-y divide-slate-100">
                  {lowFlags.map((flag) => (
                    <li key={flag.id} className="py-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-700">{flag.title}</span>
                        <span className="text-xs text-slate-400">{new Date(flag.created_at).toLocaleDateString()}</span>
                      </div>
                      <p className="text-xs text-slate-400">{flag.affected_service}</p>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Problematic documents */}
            {(report?.problematic_documents || []).length > 0 && (
              <div className="rounded border bg-white p-5">
                <h2 className="mb-3 font-semibold text-slate-800">Problematic Documents</h2>
                <table className="w-full text-sm">
                  <thead><tr className="border-b"><th className="py-2 text-left">Document</th><th className="py-2 text-right">Flags</th></tr></thead>
                  <tbody>
                    {report.problematic_documents.map((doc, i) => (
                      <tr key={i} className="border-b">
                        <td className="py-2 text-slate-700">{doc.document_title || doc.document_id}</td>
                        <td className="py-2 text-right text-red-600">{doc.flag_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </div>
    </main>
  );
}
