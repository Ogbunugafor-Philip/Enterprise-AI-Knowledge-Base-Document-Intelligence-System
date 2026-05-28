import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, RefreshCw, Trash2, Eye, GitBranch } from 'lucide-react';
import AppLayout from '../components/Layout/AppLayout.jsx';
import DataTable from '../components/UI/DataTable.jsx';
import Modal from '../components/UI/Modal.jsx';
import { adminApi } from '../services/adminApi.js';
import { formatDistanceToNow } from 'date-fns';

const STATUS_BADGE = { approved: 'badge-green', reviewed: 'badge-yellow', processing: 'badge-blue', uploaded: 'badge-purple', failed: 'badge-red', rejected: 'badge-red' };

export default function DocumentManagement() {
  const navigate = useNavigate();
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ status: '', file_type: '', search_query: '' });
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploading, setUploading] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    adminApi.getDocuments({ ...filters, page: 1, page_size: 100 })
      .then(r => r.ok && setDocs(r.data?.documents || []))
      .finally(() => setLoading(false));
  }, [filters]);

  useEffect(() => { load(); }, [load]);

  async function doDelete() {
    if (!deleteTarget) return;
    await adminApi.deleteDocument(deleteTarget.id);
    setDeleteTarget(null);
    load();
  }

  async function doUpload() {
    if (!uploadFile) return;
    setUploading(true);
    const fd = new FormData();
    fd.append('file', uploadFile);
    fd.append('title', uploadFile.name.replace(/\.[^.]+$/, ''));
    await adminApi.uploadDocument(fd);
    setUploadOpen(false);
    setUploadFile(null);
    setUploading(false);
    load();
  }

  const columns = [
    { key: 'title', header: 'Document', sortable: true, accessor: r => r.title || r.file_name,
      render: r => <div><p className="font-medium text-gray-800 truncate max-w-xs">{r.title || r.file_name}</p><p className="text-xs text-gray-400">{r.file_name}</p></div> },
    { key: 'file_type', header: 'Type', accessor: r => r.file_type?.split('/').pop() || 'file',
      render: r => <span className="badge badge-gray uppercase text-xs">{r.file_type?.split('/').pop() || 'file'}</span> },
    { key: 'status', header: 'Status', sortable: true, accessor: 'status',
      render: r => <span className={`badge ${STATUS_BADGE[r.status] || 'badge-gray'}`}>{r.status}</span> },
    { key: 'created_at', header: 'Uploaded', sortable: true, accessor: 'created_at',
      render: r => <span className="text-xs text-gray-400">{r.created_at ? formatDistanceToNow(new Date(r.created_at), { addSuffix: true }) : '—'}</span> },
    { key: 'actions', header: 'Actions', render: r => (
      <div className="flex items-center gap-1">
        <button title="Versions" onClick={() => navigate(`/admin/documents/${r.id}/versions`)} className="p-1.5 rounded hover:bg-gray-100 text-gray-500 hover:text-blue-600 transition-colors"><GitBranch className="w-4 h-4" /></button>
        <button title="Reprocess" onClick={() => adminApi.reprocessDocument(r.id).then(load)} className="p-1.5 rounded hover:bg-gray-100 text-gray-500 hover:text-green-600 transition-colors"><RefreshCw className="w-4 h-4" /></button>
        <button title="Delete" onClick={() => setDeleteTarget(r)} className="p-1.5 rounded hover:bg-red-50 text-gray-500 hover:text-red-600 transition-colors"><Trash2 className="w-4 h-4" /></button>
      </div>
    )},
  ];

  return (
    <AppLayout title="Document Management" subtitle="Upload and manage organization documents">
      {/* Filters */}
      <div className="card p-4 mb-6 flex flex-wrap items-center gap-3">
        <select className="input w-40" value={filters.status} onChange={e => setFilters(f => ({ ...f, status: e.target.value }))}>
          <option value="">All statuses</option>
          {['uploaded','processing','reviewed','approved','rejected','failed'].map(s => <option key={s} value={s}>{s.charAt(0).toUpperCase()+s.slice(1)}</option>)}
        </select>
        <select className="input w-36" value={filters.file_type} onChange={e => setFilters(f => ({ ...f, file_type: e.target.value }))}>
          <option value="">All types</option>
          {['pdf','docx','txt','xlsx'].map(t => <option key={t} value={t}>{t.toUpperCase()}</option>)}
        </select>
        <div className="flex-1" />
        <button onClick={() => setUploadOpen(true)} className="btn-primary"><Upload className="w-4 h-4" />Upload Document</button>
      </div>

      <DataTable
        columns={columns}
        data={docs}
        loading={loading}
        emptyMessage="No documents found"
        pageSize={15}
        rowKey="id"
      />

      {/* Delete confirmation */}
      <Modal isOpen={!!deleteTarget} onClose={() => setDeleteTarget(null)} title="Delete Document" size="sm"
        footer={<><button className="btn-secondary" onClick={() => setDeleteTarget(null)}>Cancel</button><button className="btn-danger" onClick={doDelete}>Delete</button></>}>
        <p className="text-sm text-gray-600">Are you sure you want to delete <strong className="text-gray-900">"{deleteTarget?.title || deleteTarget?.file_name}"</strong>? This action cannot be undone.</p>
      </Modal>

      {/* Upload modal */}
      <Modal isOpen={uploadOpen} onClose={() => setUploadOpen(false)} title="Upload Document" size="md"
        footer={<><button className="btn-secondary" onClick={() => setUploadOpen(false)}>Cancel</button><button className="btn-primary" onClick={doUpload} disabled={!uploadFile || uploading}>{uploading ? 'Uploading…' : 'Upload'}</button></>}>
        <div className="space-y-4">
          <p className="text-sm text-gray-500">Supported formats: PDF, DOCX, TXT, XLSX · Max size: 50 MB</p>
          <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-gray-300 rounded-xl cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition-colors">
            <Upload className="w-8 h-8 text-gray-400 mb-2" />
            <span className="text-sm text-gray-500">{uploadFile ? uploadFile.name : 'Click to choose file'}</span>
            <input type="file" className="hidden" accept=".pdf,.docx,.txt,.xlsx"
              onChange={e => setUploadFile(e.target.files?.[0] || null)} />
          </label>
        </div>
      </Modal>
    </AppLayout>
  );
}
