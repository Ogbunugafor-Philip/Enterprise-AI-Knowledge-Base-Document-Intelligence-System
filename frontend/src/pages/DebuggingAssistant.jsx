import React, { useState, useEffect, useCallback } from 'react';
import { Bug, AlertTriangle, CheckCircle, Clock } from 'lucide-react';
import AppLayout from '../components/Layout/AppLayout.jsx';
import Modal from '../components/UI/Modal.jsx';
import { monitoringApi } from '../services/monitoringApi.js';

const SEVERITY_COLORS = {
  critical: { border: 'border-red-200', bg: 'bg-red-50', badge: 'badge-red', icon: 'text-red-500' },
  high: { border: 'border-orange-200', bg: 'bg-orange-50', badge: 'badge-red', icon: 'text-orange-500' },
  medium: { border: 'border-yellow-200', bg: 'bg-yellow-50', badge: 'badge-yellow', icon: 'text-yellow-500' },
  low: { border: 'border-blue-200', bg: 'bg-blue-50', badge: 'badge-blue', icon: 'text-blue-500' },
};

const SEVERITIES = ['all', 'critical', 'high', 'medium', 'low'];

function timeAgo(ts) {
  if (!ts) return '';
  const diff = Math.floor((Date.now() - new Date(ts)) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

export default function DebuggingAssistant() {
  const [errors, setErrors] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState('all');
  const [selectedIncident, setSelectedIncident] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    const [debugRes, incidentRes] = await Promise.all([
      monitoringApi.getDebuggingHistory(),
      monitoringApi.getIncidents(),
    ]);
    if (debugRes.ok) setErrors(debugRes.data?.errors || debugRes.data || []);
    if (incidentRes.ok) setIncidents(incidentRes.data?.incidents || incidentRes.data || []);
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const filtered = severityFilter === 'all' ? errors : errors.filter(e => e.severity === severityFilter);

  return (
    <AppLayout title="AI Debugging Assistant" subtitle="Technical errors explained in plain English">
      <div className="flex items-center gap-2 mb-6">
        {SEVERITIES.map(s => (
          <button
            key={s}
            onClick={() => setSeverityFilter(s)}
            className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-colors ${severityFilter === s ? 'bg-blue-600 text-white shadow-sm' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'}`}
          >
            {s}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="grid grid-cols-1 gap-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="card p-6 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-1/3 mb-3" />
              <div className="h-3 bg-gray-100 rounded w-full mb-2" />
              <div className="h-3 bg-gray-100 rounded w-2/3" />
            </div>
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="card p-16 flex flex-col items-center gap-3">
          <CheckCircle className="w-12 h-12 text-green-400" />
          <p className="text-lg font-semibold text-gray-700">No errors found</p>
          <p className="text-sm text-gray-400">System is operating normally</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 mb-8">
          {filtered.map((err, i) => {
            const colors = SEVERITY_COLORS[err.severity] || SEVERITY_COLORS.low;
            return (
              <div key={err.id || i} className={`card p-6 border-l-4 ${colors.border} ${colors.bg}`}>
                <div className="flex items-start justify-between gap-4 mb-3">
                  <div className="flex items-center gap-3">
                    <AlertTriangle className={`w-5 h-5 flex-shrink-0 ${colors.icon}`} />
                    <span className={colors.badge}>{err.severity}</span>
                    <span className="text-xs text-gray-500">{err.affected_service || err.service || 'Unknown service'}</span>
                  </div>
                  <div className="flex items-center gap-1 text-xs text-gray-400 flex-shrink-0">
                    <Clock className="w-3.5 h-3.5" />
                    {timeAgo(err.timestamp || err.created_at)}
                  </div>
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">{err.plain_explanation || err.title || err.error_type || 'Unknown Error'}</h3>
                {err.possible_cause && (
                  <p className="text-sm text-gray-600 mb-3"><span className="font-medium">Possible cause:</span> {err.possible_cause}</p>
                )}
                {err.business_impact && (
                  <p className="text-sm text-gray-600 mb-3"><span className="font-medium">Business impact:</span> {err.business_impact}</p>
                )}
                {err.recommended_steps && err.recommended_steps.length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-2">Recommended steps:</p>
                    <ol className="list-decimal list-inside space-y-1">
                      {err.recommended_steps.map((step, j) => (
                        <li key={j} className="text-sm text-gray-600">{step}</li>
                      ))}
                    </ol>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {incidents.length > 0 && (
        <div className="card p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-4">AI-Generated Incident Summaries</h2>
          <div className="space-y-3">
            {incidents.map((inc, i) => (
              <button
                key={inc.id || i}
                onClick={() => setSelectedIncident(inc)}
                className="w-full text-left p-4 bg-gray-50 hover:bg-gray-100 rounded-xl transition-colors"
              >
                <div className="flex items-center justify-between gap-2 mb-1">
                  <span className="font-semibold text-gray-900 text-sm">{inc.title || `Incident #${inc.id}`}</span>
                  <span className="text-xs text-gray-400">{timeAgo(inc.created_at)}</span>
                </div>
                <p className="text-sm text-gray-600 line-clamp-2">{inc.ai_summary || inc.description || inc.summary}</p>
              </button>
            ))}
          </div>
        </div>
      )}

      <Modal isOpen={!!selectedIncident} onClose={() => setSelectedIncident(null)} title="Incident Summary" size="lg"
        footer={<button onClick={() => setSelectedIncident(null)} className="btn-secondary">Close</button>}
      >
        {selectedIncident && (
          <div className="space-y-4">
            <h3 className="font-semibold text-gray-900">{selectedIncident.title || `Incident #${selectedIncident.id}`}</h3>
            {selectedIncident.ai_summary && (
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">AI Summary</p>
                <p className="text-gray-700 text-sm leading-relaxed">{selectedIncident.ai_summary}</p>
              </div>
            )}
            {selectedIncident.description && (
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Description</p>
                <p className="text-gray-700 text-sm leading-relaxed">{selectedIncident.description}</p>
              </div>
            )}
            {selectedIncident.affected_services && (
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Affected Services</p>
                <p className="text-gray-700 text-sm">{selectedIncident.affected_services?.join(', ')}</p>
              </div>
            )}
            {selectedIncident.resolution && (
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Resolution</p>
                <p className="text-gray-700 text-sm leading-relaxed">{selectedIncident.resolution}</p>
              </div>
            )}
          </div>
        )}
      </Modal>
    </AppLayout>
  );
}
