import React, { useState, useEffect } from 'react';
import { Brain, TrendingUp, AlertTriangle, ThumbsDown, Download } from 'lucide-react';
import {
  LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import AppLayout from '../components/Layout/AppLayout.jsx';
import StatsCard from '../components/UI/StatsCard.jsx';
import { monitoringApi } from '../services/monitoringApi.js';

function trustLevel(score) {
  if (score >= 0.85) return { label: 'Excellent', color: 'text-green-600', bg: 'bg-green-50 border-green-200' };
  if (score >= 0.70) return { label: 'Good', color: 'text-blue-600', bg: 'bg-blue-50 border-blue-200' };
  if (score >= 0.55) return { label: 'Fair', color: 'text-yellow-600', bg: 'bg-yellow-50 border-yellow-200' };
  return { label: 'Poor', color: 'text-red-600', bg: 'bg-red-50 border-red-200' };
}

export default function AITrustReport() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  async function load() {
    setLoading(true);
    const res = await monitoringApi.getAITrustReport();
    if (res.ok) setReport(res.data);
    setLoading(false);
  }

  useEffect(() => { load(); }, []);

  async function handleGenerate() {
    setGenerating(true);
    const res = await monitoringApi.getAITrustReport();
    if (res.ok) setReport(res.data);
    setGenerating(false);
  }

  const r = report || {};
  const avgConfidence = r.avg_confidence_score ?? 0;
  const avgHallucination = r.avg_hallucination_risk ?? 0;
  const totalResponses = r.total_responses ?? 0;
  const rejectionRate = r.rejection_rate ?? 0;
  const confidenceTrend = r.confidence_trend || [];
  const hallucinationTrend = r.hallucination_trend || [];
  const problematicDocs = r.problematic_documents || [];
  const reportedHallucinations = r.reported_hallucinations || [];
  const trust = trustLevel(avgConfidence);

  return (
    <AppLayout
      title="AI Trust Report"
      subtitle="AI response quality and reliability analytics"
      actions={
        <button onClick={handleGenerate} disabled={generating} className="btn-primary flex items-center gap-2">
          <Download className="w-4 h-4" />
          {generating ? 'Generating…' : 'Generate Report'}
        </button>
      }
    >
      <div className={`card p-5 mb-6 border-2 flex items-center gap-4 ${trust.bg}`}>
        <Brain className={`w-10 h-10 ${trust.color}`} />
        <div>
          <p className="text-sm font-medium text-gray-600">Overall AI Trust Level</p>
          <p className={`text-2xl font-bold ${trust.color}`}>{trust.label}</p>
        </div>
        <div className="ml-auto text-right">
          <p className="text-sm text-gray-500">Based on confidence score</p>
          <p className={`text-3xl font-bold ${trust.color}`}>{(avgConfidence * 100).toFixed(0)}%</p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <StatsCard title="Avg Confidence Score" value={loading ? '…' : `${(avgConfidence * 100).toFixed(1)}%`} icon={Brain} color="blue" />
        <StatsCard title="Hallucination Risk" value={loading ? '…' : `${(avgHallucination * 100).toFixed(1)}%`} icon={AlertTriangle} color="red" />
        <StatsCard title="Total Responses" value={loading ? '…' : totalResponses} icon={TrendingUp} color="green" />
        <StatsCard title="Rejection Rate %" value={loading ? '…' : `${(rejectionRate * 100).toFixed(1)}%`} icon={ThumbsDown} color="yellow" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="card p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-4">Confidence Score (30 days)</h2>
          {confidenceTrend.length === 0 ? (
            <div className="h-48 flex items-center justify-center text-gray-400 text-sm">No trend data available</div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={confidenceTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                <YAxis domain={[0, 1]} tickFormatter={v => `${(v * 100).toFixed(0)}%`} tick={{ fontSize: 10 }} />
                <Tooltip formatter={v => [`${(v * 100).toFixed(1)}%`, 'Confidence']} />
                <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="card p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-4">Hallucination Risk (30 days)</h2>
          {hallucinationTrend.length === 0 ? (
            <div className="h-48 flex items-center justify-center text-gray-400 text-sm">No trend data available</div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={hallucinationTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                <YAxis domain={[0, 1]} tickFormatter={v => `${(v * 100).toFixed(0)}%`} tick={{ fontSize: 10 }} />
                <Tooltip formatter={v => [`${(v * 100).toFixed(1)}%`, 'Risk']} />
                <Area type="monotone" dataKey="value" stroke="#ef4444" fill="#fee2e2" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-4">Most Problematic Documents</h2>
          {problematicDocs.length === 0 ? (
            <p className="text-center text-gray-400 text-sm py-8">No problematic documents found</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="table">
                <thead><tr><th>Document</th><th>Avg Confidence</th><th>Hallucinations</th><th>Status</th></tr></thead>
                <tbody>
                  {problematicDocs.map((doc, i) => (
                    <tr key={doc.id || i}>
                      <td className="font-medium text-gray-900 max-w-xs truncate">{doc.title || doc.document_title || '—'}</td>
                      <td>{((doc.avg_confidence ?? 0) * 100).toFixed(0)}%</td>
                      <td>{doc.hallucination_count ?? 0}</td>
                      <td><span className={doc.hallucination_count > 5 ? 'badge-red' : 'badge-yellow'}>{doc.hallucination_count > 5 ? 'High Risk' : 'Monitor'}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="card p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-4">Reported Hallucinations</h2>
          {reportedHallucinations.length === 0 ? (
            <p className="text-center text-gray-400 text-sm py-8">No reported hallucinations</p>
          ) : (
            <div className="space-y-3">
              {reportedHallucinations.map((h, i) => (
                <div key={h.id || i} className="p-3 bg-red-50 rounded-lg border border-red-100">
                  <p className="text-sm font-medium text-red-800">{h.reported_issue || h.description || 'Reported issue'}</p>
                  <p className="text-xs text-red-500 mt-1">{h.user_email || h.user || 'Anonymous'} · {h.created_at ? new Date(h.created_at).toLocaleDateString() : ''}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
