import React, { useState, useEffect } from 'react';
import { Shield, CheckCircle, XCircle, AlertTriangle, Lock, RefreshCw } from 'lucide-react';
import AppLayout from '../components/Layout/AppLayout.jsx';
import StatsCard from '../components/UI/StatsCard.jsx';
import { securityApi } from '../services/securityApi.js';

function formatDate(ts) {
  if (!ts) return '—';
  return new Date(ts).toLocaleString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
}

const SEVERITY_COLOR = {
  critical: 'text-red-600',
  high: 'text-orange-600',
  medium: 'text-yellow-600',
  low: 'text-blue-600',
};

export default function SecurityDashboard() {
  const [checklist, setChecklist] = useState([]);
  const [events, setEvents] = useState([]);
  const [rateLimits, setRateLimits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [resettingKey, setResettingKey] = useState('');

  useEffect(() => {
    async function load() {
      setLoading(true);
      const [checkRes, eventRes, rateRes] = await Promise.all([
        securityApi.getSecurityChecklist(),
        securityApi.getSecurityEvents(),
        securityApi.getRateLimitStatus(),
      ]);
      if (checkRes.ok) setChecklist(checkRes.data?.checks || checkRes.data || []);
      if (eventRes.ok) setEvents(eventRes.data?.events || eventRes.data || []);
      if (rateRes.ok) setRateLimits(rateRes.data?.limits || rateRes.data || []);
      setLoading(false);
    }
    load();
  }, []);

  const passed = checklist.filter(c => c.status === 'PASS').length;
  const failed = checklist.filter(c => c.status === 'FAIL').length;
  const criticalFails = checklist.filter(c => c.status === 'FAIL' && c.severity === 'critical');
  const securityScore = checklist.length > 0 ? Math.round((passed / checklist.length) * 100) : 0;

  async function handleResetRateLimit(key) {
    setResettingKey(key);
    const res = await securityApi.resetRateLimit(key);
    if (!res.ok) alert(res.error);
    setResettingKey('');
  }

  return (
    <AppLayout title="Security" subtitle="System security posture and controls">
      {!loading && criticalFails.length > 0 && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-red-800">Critical Security Issues Detected</p>
            <ul className="mt-1 space-y-1">
              {criticalFails.map((c, i) => (
                <li key={i} className="text-sm text-red-700">• {c.name}: {c.recommendation || c.message}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="card p-6 flex flex-col items-center justify-center">
          <div className={`text-5xl font-black mb-1 ${securityScore >= 80 ? 'text-green-600' : securityScore >= 60 ? 'text-yellow-600' : 'text-red-600'}`}>
            {loading ? '…' : `${securityScore}%`}
          </div>
          <p className="text-sm font-medium text-gray-500">Security Score</p>
        </div>
        <StatsCard title="Checks Passed" value={loading ? '…' : passed} icon={CheckCircle} color="green" />
        <StatsCard title="Checks Failed" value={loading ? '…' : failed} icon={XCircle} color="red" />
        <StatsCard title="Critical Issues" value={loading ? '…' : criticalFails.length} icon={AlertTriangle} color={criticalFails.length > 0 ? 'red' : 'green'} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="card overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100">
            <h2 className="text-base font-semibold text-gray-900">Security Checklist</h2>
          </div>
          <div className="divide-y divide-gray-50 max-h-96 overflow-y-auto">
            {loading ? (
              <div className="p-6 text-center text-gray-400 text-sm">Loading…</div>
            ) : checklist.length === 0 ? (
              <div className="p-6 text-center text-gray-400 text-sm">No checklist data</div>
            ) : checklist.map((check, i) => (
              <div key={i} className="flex items-start gap-3 px-6 py-3">
                {check.status === 'PASS'
                  ? <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                  : <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                }
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium text-gray-900">{check.name || check.check_name}</p>
                    <span className={`text-xs font-medium ${SEVERITY_COLOR[check.severity] || 'text-gray-500'}`}>{check.severity}</span>
                  </div>
                  {check.status === 'FAIL' && check.recommendation && (
                    <p className="text-xs text-gray-500 mt-0.5">{check.recommendation}</p>
                  )}
                </div>
                <span className={check.status === 'PASS' ? 'badge-green' : 'badge-red'}>{check.status}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="card overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100">
            <h2 className="text-base font-semibold text-gray-900">Recent Security Events</h2>
          </div>
          <div className="overflow-x-auto max-h-96 overflow-y-auto">
            <table className="table">
              <thead><tr><th>Event Type</th><th>IP Address</th><th>Endpoint</th><th>Time</th></tr></thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan={4} className="text-center text-gray-400 text-sm py-8">Loading…</td></tr>
                ) : events.length === 0 ? (
                  <tr><td colSpan={4} className="empty-state">No events recorded</td></tr>
                ) : events.slice(0, 20).map((ev, i) => (
                  <tr key={i}>
                    <td><span className="badge-red">{ev.event_type || ev.type}</span></td>
                    <td className="font-mono text-xs">{ev.ip_address || '—'}</td>
                    <td className="font-mono text-xs truncate max-w-xs">{ev.endpoint || '—'}</td>
                    <td className="text-xs">{formatDate(ev.timestamp || ev.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {rateLimits.length > 0 && (
        <div className="card p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-4">Rate Limit Status</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {rateLimits.map((rl, i) => (
              <div key={i} className="p-4 bg-gray-50 rounded-xl flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-800">{rl.key || rl.identifier}</p>
                  <p className="text-xs text-gray-500">
                    {rl.requests ?? 0}/{rl.limit ?? '∞'} · {rl.window || '1m'}
                  </p>
                </div>
                <button
                  onClick={() => handleResetRateLimit(rl.key || rl.identifier)}
                  disabled={resettingKey === (rl.key || rl.identifier)}
                  className="p-1.5 text-blue-600 hover:bg-blue-50 rounded"
                  title="Reset"
                >
                  <RefreshCw className={`w-4 h-4 ${resettingKey === (rl.key || rl.identifier) ? 'animate-spin' : ''}`} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </AppLayout>
  );
}
