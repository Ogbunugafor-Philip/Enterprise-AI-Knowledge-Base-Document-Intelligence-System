import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, AlertTriangle, Clock, Users, Zap } from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area,
} from 'recharts';
import AppLayout from '../components/Layout/AppLayout.jsx';
import StatsCard from '../components/UI/StatsCard.jsx';
import { monitoringApi } from '../services/monitoringApi.js';

const SEVERITY_COLORS = {
  critical: 'text-red-700 bg-red-50',
  high: 'text-orange-700 bg-orange-50',
  medium: 'text-yellow-700 bg-yellow-50',
  low: 'text-blue-700 bg-blue-50',
};

const SEVERITY_BADGE = { critical: 'badge-red', high: 'badge-red', medium: 'badge-yellow', low: 'badge-blue' };

function timeAgo(ts) {
  if (!ts) return '';
  const diff = Math.floor((Date.now() - new Date(ts)) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

function fmtHour(ts) {
  if (!ts) return '';
  try { return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }); }
  catch { return ts; }
}

export default function MonitoringDashboard() {
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState(null);
  const [aiQualData, setAiQualData] = useState({});
  const [alerts, setAlerts] = useState([]);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    const [dashRes, alertRes, aiQualRes] = await Promise.all([
      monitoringApi.getDashboard(),
      monitoringApi.getAlerts(),
      monitoringApi.getAIQuality(),
    ]);
    if (dashRes.ok) setDashboard(dashRes.data);
    if (alertRes.ok) setAlerts((alertRes.data?.alerts || alertRes.data || []).slice(0, 5));
    if (aiQualRes.ok) setAiQualData(aiQualRes.data || {});
    setLastUpdated(new Date());
    setLoading(false);
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, [load]);

  const d = dashboard || {};
  const metrics = d.system_metrics || {};
  const responseTimeTrend = d.response_time_trend || [];
  const errorTrend = d.error_trend || [];

  const rejectionRate = aiQualData.total_queries > 0
    ? aiQualData.total_rejected / aiQualData.total_queries
    : 0;

  return (
    <AppLayout
      title="Monitoring"
      subtitle="Real-time system health and performance"
      actions={
        <span className="text-xs text-gray-400">
          {lastUpdated ? `Updated ${timeAgo(lastUpdated)}` : ''}
        </span>
      }
    >
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        <StatsCard title="Active Users"    value={loading ? '…' : (metrics.active_users ?? 0)}                                  icon={Users}          color="blue"   />
        <StatsCard title="Total API Calls" value={loading ? '…' : (metrics.total_api_calls ?? 0)}                               icon={Activity}       color="indigo" />
        <StatsCard title="Error Rate %"    value={loading ? '…' : `${(metrics.error_rate_percent ?? 0).toFixed(1)}%`}           icon={AlertTriangle}  color="red"    />
        <StatsCard title="Avg Response ms" value={loading ? '…' : `${Math.round(metrics.avg_response_time_ms ?? 0)}`}           icon={Clock}          color="yellow" />
        <StatsCard title="AI Queries"      value={loading ? '…' : (metrics.total_ai_queries ?? 0)}                              icon={Zap}            color="purple" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="card p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-4">Response Time (24h)</h2>
          {responseTimeTrend.length === 0 ? (
            <div className="h-48 flex items-center justify-center text-gray-400 text-sm">No data available</div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={responseTimeTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="timestamp" tick={{ fontSize: 11 }} tickFormatter={fmtHour} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip labelFormatter={fmtHour} formatter={v => [`${v} ms`, 'Response Time']} />
                <Line type="monotone" dataKey="avg_response_time_ms" stroke="#3b82f6" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="card p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-4">Errors (24h)</h2>
          {errorTrend.length === 0 ? (
            <div className="h-48 flex items-center justify-center text-gray-400 text-sm">No data available</div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={errorTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="timestamp" tick={{ fontSize: 11 }} tickFormatter={fmtHour} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip labelFormatter={fmtHour} formatter={v => [`${v}`, 'Errors']} />
                <Area type="monotone" dataKey="error_count" stroke="#ef4444" fill="#fee2e2" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-4">AI Quality</h2>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="font-medium text-gray-700">Avg Confidence Score</span>
                <span className="text-gray-900 font-semibold">{((aiQualData.avg_retrieval_confidence ?? 0) * 100).toFixed(0)}%</span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <div className="h-full bg-green-500 rounded-full" style={{ width: `${(aiQualData.avg_retrieval_confidence ?? 0) * 100}%` }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="font-medium text-gray-700">Hallucination Risk</span>
                <span className="text-gray-900 font-semibold">{((aiQualData.avg_hallucination_risk ?? 0) * 100).toFixed(0)}%</span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <div className="h-full bg-red-500 rounded-full" style={{ width: `${(aiQualData.avg_hallucination_risk ?? 0) * 100}%` }} />
              </div>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm font-medium text-gray-700">Rejection Rate</span>
              <span className="text-sm font-bold text-gray-900">{(rejectionRate * 100).toFixed(1)}%</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm font-medium text-gray-700">Total Queries</span>
              <span className="text-sm font-bold text-gray-900">{aiQualData.total_queries ?? 0}</span>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-gray-900">Active Alerts</h2>
            <button onClick={() => navigate('/monitoring/alerts')} className="text-xs text-blue-600 hover:underline font-medium">
              View All →
            </button>
          </div>
          {alerts.length === 0 ? (
            <div className="text-center py-8 text-gray-400 text-sm">No active alerts</div>
          ) : (
            <div className="space-y-2">
              {alerts.map((alert, i) => (
                <div key={alert.id || i} className={`flex items-start gap-3 p-3 rounded-lg ${SEVERITY_COLORS[alert.severity] || 'text-gray-700 bg-gray-50'}`}>
                  <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium truncate">{alert.title || alert.message}</p>
                    <p className="text-xs opacity-70">{alert.affected_service || alert.service} · {timeAgo(alert.created_at)}</p>
                  </div>
                  <span className={`flex-shrink-0 ${SEVERITY_BADGE[alert.severity] || 'badge-gray'}`}>{alert.severity}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
