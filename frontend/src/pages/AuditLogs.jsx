import React, { useState, useEffect, useCallback } from 'react';
import { ScrollText, Download, Filter } from 'lucide-react';
import AppLayout from '../components/Layout/AppLayout.jsx';
import DataTable from '../components/UI/DataTable.jsx';
import Modal from '../components/UI/Modal.jsx';
import { complianceApi } from '../services/complianceApi.js';

const ACTION_BADGE = {
  LOGIN: 'badge-gray', LOGOUT: 'badge-gray',
  CREATE: 'badge-green', UPDATE: 'badge-blue', DELETE: 'badge-red',
  SECURITY: 'badge-red', DOCUMENT: 'badge-purple',
};

function actionBadgeClass(action) {
  if (!action) return 'badge-gray';
  const key = Object.keys(ACTION_BADGE).find(k => action.toUpperCase().includes(k));
  return ACTION_BADGE[key] || 'badge-gray';
}

function formatDate(ts) {
  if (!ts) return '—';
  return new Date(ts).toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

const ACTION_TYPES = ['LOGIN', 'LOGOUT', 'CREATE', 'UPDATE', 'DELETE', 'SECURITY', 'DOCUMENT'];

export default function AuditLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [exporting, setExporting] = useState(false);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [actionType, setActionType] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    const params = {};
    if (dateFrom) params.date_from = dateFrom;
    if (dateTo) params.date_to = dateTo;
    if (actionType) params.action_type = actionType;
    const res = await complianceApi.getAuditLogs(params);
    if (res.ok) setLogs(res.data?.logs || res.data || []);
    setLoading(false);
  }, [dateFrom, dateTo, actionType]);

  useEffect(() => { load(); }, [load]);

  async function handleExport() {
    setExporting(true);
    const params = {};
    if (dateFrom) params.date_from = dateFrom;
    if (dateTo) params.date_to = dateTo;
    if (actionType) params.action_type = actionType;
    const res = await complianceApi.exportAuditLogs(params);
    if (res.ok) {
      const url = URL.createObjectURL(res.blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit_logs_${new Date().toISOString().split('T')[0]}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    }
    setExporting(false);
  }

  const columns = [
    { key: 'timestamp', header: 'Timestamp', sortable: true, accessor: r => formatDate(r.timestamp || r.created_at) },
    { key: 'user', header: 'User', accessor: r => r.user_email || r.username || r.user || '—' },
    {
      key: 'action', header: 'Action',
      render: r => <span className={actionBadgeClass(r.action_type || r.action)}>{r.action_type || r.action || '—'}</span>,
    },
    { key: 'resource_type', header: 'Resource Type', accessor: r => r.resource_type || '—' },
    { key: 'ip_address', header: 'IP Address', accessor: r => r.ip_address || '—' },
    {
      key: 'status', header: 'Status',
      render: r => <span className={r.success !== false ? 'badge-green' : 'badge-red'}>{r.success !== false ? 'Success' : 'Failed'}</span>,
    },
    {
      key: 'detail', header: '',
      render: r => (
        <button onClick={() => setSelected(r)} className="text-xs text-blue-600 hover:underline font-medium">View</button>
      ),
    },
  ];

  return (
    <AppLayout title="Audit Logs" subtitle="Complete system activity trail">
      <div className="card p-4 mb-4 flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-1 text-gray-500">
          <Filter className="w-4 h-4" />
          <span className="text-sm font-medium">Filters:</span>
        </div>
        <input type="date" className="input w-40" value={dateFrom} onChange={e => setDateFrom(e.target.value)} />
        <input type="date" className="input w-40" value={dateTo} onChange={e => setDateTo(e.target.value)} />
        <select className="input w-40" value={actionType} onChange={e => setActionType(e.target.value)}>
          <option value="">All Actions</option>
          {ACTION_TYPES.map(a => <option key={a} value={a}>{a}</option>)}
        </select>
        <div className="ml-auto">
          <button onClick={handleExport} disabled={exporting} className="btn-secondary flex items-center gap-2">
            <Download className="w-4 h-4" />
            {exporting ? 'Exporting…' : 'Export CSV'}
          </button>
        </div>
      </div>

      <DataTable
        columns={columns}
        data={logs}
        loading={loading}
        emptyMessage="No audit logs found"
        rowKey="id"
        searchable
        pageSize={20}
      />

      <Modal isOpen={!!selected} onClose={() => setSelected(null)} title="Audit Log Detail" size="xl"
        footer={<button onClick={() => setSelected(null)} className="btn-secondary">Close</button>}
      >
        {selected && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div><p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Timestamp</p><p className="text-gray-900">{formatDate(selected.timestamp || selected.created_at)}</p></div>
              <div><p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">User</p><p className="text-gray-900">{selected.user_email || selected.username || selected.user || '—'}</p></div>
              <div><p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Action</p><span className={actionBadgeClass(selected.action_type || selected.action)}>{selected.action_type || selected.action}</span></div>
              <div><p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Resource Type</p><p className="text-gray-900">{selected.resource_type || '—'}</p></div>
              <div><p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Resource ID</p><p className="text-gray-900 font-mono text-xs">{selected.resource_id || '—'}</p></div>
              <div><p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">IP Address</p><p className="text-gray-900 font-mono text-xs">{selected.ip_address || '—'}</p></div>
            </div>
            {selected.old_value !== undefined && (
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Previous Value</p>
                <pre className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-xs text-gray-700 overflow-x-auto whitespace-pre-wrap">
                  {typeof selected.old_value === 'string' ? selected.old_value : JSON.stringify(selected.old_value, null, 2)}
                </pre>
              </div>
            )}
            {selected.new_value !== undefined && (
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">New Value</p>
                <pre className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-xs text-gray-700 overflow-x-auto whitespace-pre-wrap">
                  {typeof selected.new_value === 'string' ? selected.new_value : JSON.stringify(selected.new_value, null, 2)}
                </pre>
              </div>
            )}
            {selected.details && (
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Details</p>
                <pre className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-xs text-gray-700 overflow-x-auto whitespace-pre-wrap">
                  {typeof selected.details === 'string' ? selected.details : JSON.stringify(selected.details, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </Modal>
    </AppLayout>
  );
}
