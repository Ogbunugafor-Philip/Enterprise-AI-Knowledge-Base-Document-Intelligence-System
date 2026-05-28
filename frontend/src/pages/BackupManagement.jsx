import React, { useState, useEffect } from 'react';
import { Database, Clock, CheckCircle, AlertTriangle, Play, RotateCcw } from 'lucide-react';
import AppLayout from '../components/Layout/AppLayout.jsx';
import StatsCard from '../components/UI/StatsCard.jsx';
import Modal from '../components/UI/Modal.jsx';
import { backupApi } from '../services/backupApi.js';

function formatDate(ts) {
  if (!ts) return 'Never';
  return new Date(ts).toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function timeAgo(ts) {
  if (!ts) return 'Never';
  const diff = Math.floor((Date.now() - new Date(ts)) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)} days ago`;
}

const RESTORE_TYPES = [
  { key: 'postgresql', label: 'PostgreSQL Database', icon: Database },
  { key: 'qdrant', label: 'Qdrant Vector Store', icon: Database },
  { key: 'documents', label: 'Documents Storage', icon: Database },
];

export default function BackupManagement() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [checkingId, setCheckingId] = useState('');
  const [showRestore, setShowRestore] = useState(false);
  const [restoreType, setRestoreType] = useState('postgresql');
  const [restoreBackupId, setRestoreBackupId] = useState('');
  const [confirmText, setConfirmText] = useState('');
  const [restoring, setRestoring] = useState(false);
  const [restoreError, setRestoreError] = useState('');
  const [restoreSuccess, setRestoreSuccess] = useState('');

  async function loadHistory() {
    setLoading(true);
    const res = await backupApi.getBackupHistory();
    if (res.ok) setHistory(res.data?.backups || res.data || []);
    setLoading(false);
  }

  useEffect(() => { loadHistory(); }, []);

  async function handleRunBackup() {
    setRunning(true);
    const res = await backupApi.runBackup();
    if (!res.ok) alert(res.error || 'Backup failed');
    else await loadHistory();
    setRunning(false);
  }

  async function handleIntegrity(id) {
    setCheckingId(id);
    const res = await backupApi.checkIntegrity(id);
    if (!res.ok) alert(res.error || 'Integrity check failed');
    else await loadHistory();
    setCheckingId('');
  }

  async function handleRestore() {
    if (confirmText !== 'CONFIRM_RESTORE') {
      setRestoreError('You must type CONFIRM_RESTORE exactly to proceed.');
      return;
    }
    setRestoring(true);
    setRestoreError(''); setRestoreSuccess('');
    const body = { backup_id: restoreBackupId };
    let res;
    if (restoreType === 'postgresql') res = await backupApi.restorePostgresql(body);
    else if (restoreType === 'qdrant') res = await backupApi.restoreQdrant(body);
    else res = await backupApi.restoreDocuments(body);
    setRestoring(false);
    if (res.ok) { setRestoreSuccess('Restore initiated successfully.'); setConfirmText(''); }
    else setRestoreError(res.error || 'Restore failed.');
  }

  const lastBackup = history[0];

  return (
    <AppLayout title="Backup Management" subtitle="System backups and disaster recovery">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <StatsCard
          title="Last Backup"
          value={loading ? '…' : timeAgo(lastBackup?.created_at)}
          icon={Clock}
          color={lastBackup ? 'green' : 'red'}
          subtitle={lastBackup ? formatDate(lastBackup.created_at) : 'No backups found'}
        />
        <StatsCard
          title="Backup Size"
          value={loading ? '…' : (lastBackup?.size_mb ? `${lastBackup.size_mb} MB` : '—')}
          icon={Database}
          color="blue"
        />
        <StatsCard
          title="Integrity Status"
          value={loading ? '…' : (lastBackup?.integrity_status || '—')}
          icon={lastBackup?.integrity_status === 'VERIFIED' ? CheckCircle : AlertTriangle}
          color={lastBackup?.integrity_status === 'VERIFIED' ? 'green' : 'yellow'}
        />
      </div>

      <div className="flex items-center gap-3 mb-6">
        <button onClick={handleRunBackup} disabled={running} className="btn-primary flex items-center gap-2">
          <Play className="w-4 h-4" />
          {running ? 'Running Backup…' : 'Run Backup Now'}
        </button>
        <button onClick={() => setShowRestore(true)} className="btn-danger flex items-center gap-2">
          <RotateCcw className="w-4 h-4" />
          Restore
        </button>
      </div>

      <div className="card overflow-hidden mb-6">
        <div className="px-6 py-4 border-b border-gray-100">
          <h2 className="text-base font-semibold text-gray-900">Backup History</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="table">
            <thead><tr><th>Date</th><th>Size</th><th>Components</th><th>Integrity</th><th>Actions</th></tr></thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={5} className="text-center text-gray-400 py-8 text-sm">Loading…</td></tr>
              ) : history.length === 0 ? (
                <tr><td colSpan={5} className="empty-state">No backups found</td></tr>
              ) : history.map((b, i) => (
                <tr key={b.id || i}>
                  <td className="text-sm">{formatDate(b.created_at)}</td>
                  <td className="text-sm">{b.size_mb ? `${b.size_mb} MB` : '—'}</td>
                  <td className="text-sm">{b.components?.join(', ') || b.backup_type || '—'}</td>
                  <td>
                    <span className={b.integrity_status === 'VERIFIED' ? 'badge-green' : b.integrity_status === 'FAILED' ? 'badge-red' : 'badge-gray'}>
                      {b.integrity_status || 'Unknown'}
                    </span>
                  </td>
                  <td>
                    <button
                      onClick={() => handleIntegrity(b.id)}
                      disabled={checkingId === b.id}
                      className="text-xs px-3 py-1 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 font-medium"
                    >
                      {checkingId === b.id ? 'Checking…' : 'Check Integrity'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <Modal
        isOpen={showRestore}
        onClose={() => { setShowRestore(false); setRestoreError(''); setRestoreSuccess(''); setConfirmText(''); }}
        title="Restore System"
        size="md"
        footer={
          <>
            <button onClick={() => setShowRestore(false)} className="btn-secondary">Cancel</button>
            <button onClick={handleRestore} disabled={restoring || confirmText !== 'CONFIRM_RESTORE'} className="btn-danger">
              {restoring ? 'Restoring…' : 'Restore'}
            </button>
          </>
        }
      >
        <div className="space-y-4">
          <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-red-700 font-medium">
              Warning: Restoring will overwrite current data. This action cannot be undone.
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Restore Type</label>
            <div className="space-y-2">
              {RESTORE_TYPES.map(rt => (
                <label key={rt.key} className={`flex items-center gap-3 p-3 rounded-lg border-2 cursor-pointer ${restoreType === rt.key ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'}`}>
                  <input type="radio" name="restoreType" value={rt.key} checked={restoreType === rt.key} onChange={() => setRestoreType(rt.key)} className="w-4 h-4 text-blue-600" />
                  <rt.icon className="w-4 h-4 text-gray-600" />
                  <span className="text-sm font-medium text-gray-800">{rt.label}</span>
                </label>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Backup ID</label>
            <select className="input" value={restoreBackupId} onChange={e => setRestoreBackupId(e.target.value)}>
              <option value="">Select backup…</option>
              {history.map((b, i) => <option key={b.id || i} value={b.id}>{formatDate(b.created_at)} — {b.size_mb ? `${b.size_mb} MB` : ''}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Type <span className="font-bold">CONFIRM_RESTORE</span> to proceed
            </label>
            <input className="input" value={confirmText} onChange={e => setConfirmText(e.target.value)} placeholder="CONFIRM_RESTORE" />
          </div>
          {restoreError && <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm">{restoreError}</div>}
          {restoreSuccess && <div className="p-3 bg-green-50 text-green-700 rounded-lg text-sm">{restoreSuccess}</div>}
        </div>
      </Modal>
    </AppLayout>
  );
}
