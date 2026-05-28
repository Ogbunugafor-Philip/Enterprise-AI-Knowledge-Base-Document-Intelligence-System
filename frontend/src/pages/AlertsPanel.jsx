import React, { useState, useEffect, useCallback } from 'react';
import { AlertTriangle, CheckCircle, Clock, Eye } from 'lucide-react';
import AppLayout from '../components/Layout/AppLayout.jsx';
import DataTable from '../components/UI/DataTable.jsx';
import Modal from '../components/UI/Modal.jsx';
import { monitoringApi } from '../services/monitoringApi.js';

const SEVERITY_BADGE = { critical: 'badge-red', high: 'badge-red', medium: 'badge-yellow', low: 'badge-blue' };
const STATUS_BADGE = { open: 'badge-red', investigating: 'badge-yellow', resolved: 'badge-green', ignored: 'badge-gray' };

function formatDate(ts) {
  if (!ts) return '—';
  return new Date(ts).toLocaleString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
}

function timeAgo(ts) {
  if (!ts) return '';
  const diff = Math.floor((Date.now() - new Date(ts)) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

export default function AlertsPanel() {
  const [alerts, setAlerts] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [selected, setSelected] = useState(null);
  const [updating, setUpdating] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    const [alertRes, incidentRes] = await Promise.all([
      monitoringApi.getAlerts(severityFilter || undefined),
      monitoringApi.getIncidents(),
    ]);
    if (alertRes.ok) {
      let data = alertRes.data?.alerts || alertRes.data || [];
      if (statusFilter) data = data.filter(a => a.status === statusFilter);
      setAlerts(data);
    }
    if (incidentRes.ok) setIncidents(incidentRes.data?.incidents || incidentRes.data || []);
    setLoading(false);
  }, [severityFilter, statusFilter]);

  useEffect(() => { load(); }, [load]);

  async function updateStatus(alert, status) {
    setUpdating(alert.id);
    const res = await monitoringApi.updateAlertStatus(alert.id, { status });
    setUpdating('');
    if (res.ok) load();
  }

  const columns = [
    { key: 'severity', header: 'Severity', render: r => <span className={SEVERITY_BADGE[r.severity] || 'badge-gray'}>{r.severity}</span> },
    {
      key: 'title', header: 'Title', sortable: true,
      render: r => (
        <button onClick={() => setSelected(r)} className="text-left font-medium text-gray-900 hover:text-blue-600 truncate max-w-xs">
          {r.title || r.message || '—'}
        </button>
      ),
    },
    { key: 'service', header: 'Affected Service', accessor: r => r.affected_service || r.service || '—' },
    { key: 'status', header: 'Status', render: r => <span className={STATUS_BADGE[r.status] || 'badge-gray'}>{r.status}</span> },
    { key: 'created_at', header: 'Created', accessor: r => formatDate(r.created_at), sortable: true },
    {
      key: 'actions', header: 'Actions',
      render: r => (
        <div className="flex items-center gap-1">
          <button onClick={() => setSelected(r)} className="p-1.5 text-blue-600 hover:bg-blue-50 rounded" title="View">
            <Eye className="w-4 h-4" />
          </button>
          {r.status === 'open' && (
            <button onClick={() => updateStatus(r, 'investigating')} disabled={updating === r.id}
              className="text-xs px-2 py-1 bg-yellow-100 text-yellow-800 rounded hover:bg-yellow-200 font-medium">
              Investigate
            </button>
          )}
          {r.status !== 'resolved' && (
            <button onClick={() => updateStatus(r, 'resolved')} disabled={updating === r.id}
              className="text-xs px-2 py-1 bg-green-100 text-green-800 rounded hover:bg-green-200 font-medium">
              Resolve
            </button>
          )}
          {r.status !== 'ignored' && r.status !== 'resolved' && (
            <button onClick={() => updateStatus(r, 'ignored')} disabled={updating === r.id}
              className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 font-medium">
              Ignore
            </button>
          )}
        </div>
      ),
    },
  ];

  return (
    <AppLayout title="Alerts" subtitle="System alerts and incident management">
      <div className="card p-4 mb-4 flex flex-wrap items-center gap-3">
        <select className="input w-36" value={severityFilter} onChange={e => setSeverityFilter(e.target.value)}>
          <option value="">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <select className="input w-36" value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
          <option value="">All Statuses</option>
          <option value="open">Open</option>
          <option value="investigating">Investigating</option>
          <option value="resolved">Resolved</option>
          <option value="ignored">Ignored</option>
        </select>
      </div>

      <DataTable
        columns={columns}
        data={alerts}
        loading={loading}
        emptyMessage="No alerts found"
        rowKey="id"
        searchable
      />

      {incidents.length > 0 && (
        <div className="card p-6 mt-6">
          <h2 className="text-base font-semibold text-gray-900 mb-4">Incidents</h2>
          <div className="space-y-3">
            {incidents.map((inc, i) => (
              <div key={inc.id || i} className="flex items-start gap-4 p-4 bg-gray-50 rounded-xl">
                <AlertTriangle className="w-5 h-5 text-orange-500 flex-shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-semibold text-gray-900 text-sm">{inc.title || `Incident #${inc.id}`}</span>
                    <span className={STATUS_BADGE[inc.status] || 'badge-gray'}>{inc.status}</span>
                  </div>
                  <p className="text-sm text-gray-600 line-clamp-2">{inc.description || inc.summary}</p>
                  <p className="text-xs text-gray-400 mt-1">{timeAgo(inc.created_at)} · {inc.affected_services?.join(', ') || ''}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <Modal isOpen={!!selected} onClose={() => setSelected(null)} title="Alert Details" size="lg"
        footer={<button onClick={() => setSelected(null)} className="btn-secondary">Close</button>}
      >
        {selected && (
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <span className={SEVERITY_BADGE[selected.severity] || 'badge-gray'}>{selected.severity}</span>
              <span className={STATUS_BADGE[selected.status] || 'badge-gray'}>{selected.status}</span>
              <span className="text-xs text-gray-400">{formatDate(selected.created_at)}</span>
            </div>
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Title</p>
              <p className="text-gray-900 font-semibold">{selected.title || selected.message}</p>
            </div>
            {selected.description && (
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Description</p>
                <p className="text-gray-700 text-sm">{selected.description}</p>
              </div>
            )}
            {selected.business_impact && (
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Business Impact</p>
                <p className="text-gray-700 text-sm">{selected.business_impact}</p>
              </div>
            )}
            {selected.recommended_action && (
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Recommended Action</p>
                <p className="text-gray-700 text-sm">{selected.recommended_action}</p>
              </div>
            )}
            {selected.affected_service && (
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Affected Service</p>
                <p className="text-gray-700 text-sm">{selected.affected_service}</p>
              </div>
            )}
          </div>
        )}
      </Modal>
    </AppLayout>
  );
}
