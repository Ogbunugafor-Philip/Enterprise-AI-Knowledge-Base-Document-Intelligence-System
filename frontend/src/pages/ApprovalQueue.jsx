import React, { useEffect, useState } from 'react';
import { CheckCircle, XCircle, Clock, FileText } from 'lucide-react';
import AppLayout from '../components/Layout/AppLayout.jsx';
import StatsCard from '../components/UI/StatsCard.jsx';
import Modal from '../components/UI/Modal.jsx';
import { adminApi } from '../services/adminApi.js';
import { formatDistanceToNow } from 'date-fns';

export default function ApprovalQueue() {
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [rejectModal, setRejectModal] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const [approvedToday, setApprovedToday] = useState(0);
  const [rejectedToday, setRejectedToday] = useState(0);
  const [processing, setProcessing] = useState(false);

  const load = () => {
    setLoading(true);
    adminApi.getApprovalQueue({ page: 1, page_size: 50 })
      .then(r => { if (r.ok) setQueue(r.data?.documents || []); })
      .finally(() => setLoading(false));
    adminApi.getGovernanceStats().then(r => {
      if (r.ok) { setApprovedToday(r.data?.approved_today ?? 0); setRejectedToday(r.data?.rejected_today ?? 0); }
    });
  };

  useEffect(load, []);

  async function approve(doc) {
    setProcessing(true);
    await adminApi.approveDocument({ document_id: doc.id, notes: 'Approved' });
    setSelected(null);
    setProcessing(false);
    load();
  }

  async function reject() {
    if (!selected || !rejectReason.trim()) return;
    setProcessing(true);
    await adminApi.rejectDocument({ document_id: selected.id, reason: rejectReason });
    setRejectModal(false); setRejectReason(''); setSelected(null); setProcessing(false);
    load();
  }

  return (
    <AppLayout title="Approval Queue" subtitle="Review and approve submitted documents">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 mb-8">
        <StatsCard title="Pending Review" value={queue.length}   icon={Clock}        color="yellow" />
        <StatsCard title="Approved Today" value={approvedToday}  icon={CheckCircle}  color="green" />
        <StatsCard title="Rejected Today" value={rejectedToday}  icon={XCircle}      color="red" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        <div className="lg:col-span-2 card overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-100">
            <h2 className="font-semibold text-gray-900">Pending ({queue.length})</h2>
          </div>
          <div className="overflow-y-auto" style={{ maxHeight: 'calc(100vh - 340px)' }}>
            {loading ? (
              <div className="p-4 space-y-3">{[1,2,3].map(i => <div key={i} className="h-16 bg-gray-100 rounded-xl animate-pulse" />)}</div>
            ) : queue.length === 0 ? (
              <p className="text-center text-gray-400 text-sm py-10">No documents awaiting approval</p>
            ) : queue.map(doc => (
              <button key={doc.id} onClick={() => setSelected(doc)}
                className={`w-full text-left px-5 py-4 border-b border-gray-50 hover:bg-gray-50 transition-colors ${selected?.id === doc.id ? 'bg-blue-50' : ''}`}>
                <div className="flex items-start gap-3">
                  <FileText className="w-5 h-5 text-gray-400 shrink-0 mt-0.5" />
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-gray-800 truncate">{doc.title || doc.file_name}</p>
                    <p className="text-xs text-gray-400 mt-0.5">{doc.file_type?.split('/').pop()?.toUpperCase()} · {doc.created_at ? formatDistanceToNow(new Date(doc.created_at), { addSuffix: true }) : ''}</p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="lg:col-span-3 card p-6">
          {!selected ? (
            <div className="h-full flex flex-col items-center justify-center text-center py-16">
              <FileText className="w-12 h-12 text-gray-200 mb-3" />
              <p className="font-medium text-gray-500">Select a document to review</p>
              <p className="text-sm text-gray-400 mt-1">Click any document from the list to view details</p>
            </div>
          ) : (
            <>
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h3 className="text-lg font-bold text-gray-900">{selected.title || selected.file_name}</h3>
                  <p className="text-sm text-gray-400 mt-1">{selected.file_name}</p>
                </div>
                <span className="badge badge-yellow">Pending</span>
              </div>
              <div className="grid grid-cols-2 gap-4 mb-6">
                {[['File Size', selected.file_size_mb ? `${selected.file_size_mb} MB` : '—'],
                  ['Submitted', selected.created_at ? formatDistanceToNow(new Date(selected.created_at), { addSuffix: true }) : '—'],
                  ['Chunks', selected.chunk_count ?? '—'],
                  ['Department', selected.department_id ? 'Assigned' : 'General']].map(([l, v]) => (
                  <div key={l} className="bg-gray-50 rounded-xl p-3">
                    <p className="text-xs text-gray-500 font-medium">{l}</p>
                    <p className="text-sm font-semibold text-gray-800 mt-0.5">{v}</p>
                  </div>
                ))}
              </div>
              <div className="flex gap-3">
                <button onClick={() => approve(selected)} disabled={processing} className="flex-1 btn-success justify-center py-3">
                  <CheckCircle className="w-4 h-4" />{processing ? 'Processing…' : 'Approve'}
                </button>
                <button onClick={() => setRejectModal(true)} disabled={processing} className="flex-1 btn-danger justify-center py-3">
                  <XCircle className="w-4 h-4" />Reject
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      <Modal isOpen={rejectModal} onClose={() => setRejectModal(false)} title="Reject Document" size="sm"
        footer={<><button className="btn-secondary" onClick={() => setRejectModal(false)}>Cancel</button>
          <button className="btn-danger" onClick={reject} disabled={!rejectReason.trim() || processing}>Reject</button></>}>
        <div className="space-y-3">
          <p className="text-sm text-gray-600">Reason for rejecting <strong>"{selected?.title || selected?.file_name}"</strong></p>
          <textarea className="input resize-none" rows={4} placeholder="Enter rejection reason…"
            value={rejectReason} onChange={e => setRejectReason(e.target.value)} />
        </div>
      </Modal>
    </AppLayout>
  );
}
