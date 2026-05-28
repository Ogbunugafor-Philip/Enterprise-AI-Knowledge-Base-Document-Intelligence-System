import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, UserPlus, Upload, Lock, Unlock, RefreshCw, Trash2, CheckCircle, XCircle } from 'lucide-react';
import AppLayout from '../components/Layout/AppLayout.jsx';
import DataTable from '../components/UI/DataTable.jsx';
import Modal from '../components/UI/Modal.jsx';
import PageHeader from '../components/UI/PageHeader.jsx';
import { superAdminApi } from '../services/superAdminApi.js';

function RoleBadge({ role }) {
  const map = { SUPER_ADMIN: 'badge-purple', ADMIN: 'badge-blue', USER: 'badge-gray' };
  return <span className={map[role] || 'badge-gray'}>{role?.replace('_', ' ') || '—'}</span>;
}

function StatusBadge({ status }) {
  const map = { active: 'badge-green', inactive: 'badge-gray', locked: 'badge-red' };
  return <span className={map[status] || 'badge-gray'}>{status || '—'}</span>;
}

function formatDate(ts) {
  if (!ts) return 'Never';
  return new Date(ts).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
}

const ROLES = ['USER', 'ADMIN', 'SUPER_ADMIN'];
const DEPARTMENTS = ['Engineering', 'Finance', 'HR', 'Legal', 'Operations', 'Sales', 'IT', 'Management'];
const STATUSES = ['active', 'inactive', 'locked'];

export default function UserManagement() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [showBulk, setShowBulk] = useState(false);
  const [creating, setCreating] = useState(false);
  const [bulkFile, setBulkFile] = useState(null);
  const [bulkUploading, setBulkUploading] = useState(false);
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', role: 'USER', department: '' });
  const [formError, setFormError] = useState('');

  const loadUsers = useCallback(async () => {
    setLoading(true);
    const params = {};
    if (roleFilter) params.role = roleFilter;
    if (statusFilter) params.status = statusFilter;
    const res = await superAdminApi.getUsers(params);
    if (res.ok) setUsers(res.data?.users || res.data || []);
    else setError(res.error);
    setLoading(false);
  }, [roleFilter, statusFilter]);

  useEffect(() => { loadUsers(); }, [loadUsers]);

  async function handleCreate(e) {
    e.preventDefault();
    setFormError('');
    if (!form.first_name || !form.last_name || !form.email) {
      setFormError('First name, last name and email are required.');
      return;
    }
    setCreating(true);
    const res = await superAdminApi.createUser(form);
    setCreating(false);
    if (res.ok) { setShowCreate(false); setForm({ first_name: '', last_name: '', email: '', role: 'USER', department: '' }); loadUsers(); }
    else setFormError(res.error);
  }

  async function handleResetPassword(user) {
    const newPwd = prompt(`Set new password for ${user.email}:`);
    if (!newPwd) return;
    const res = await superAdminApi.resetUserPassword(user.id, { new_password: newPwd });
    if (!res.ok) alert(res.error);
  }

  async function handleToggleActive(user) {
    const res = user.is_active
      ? await superAdminApi.deactivateUser(user.id, { reason: 'Admin action' })
      : await superAdminApi.activateUser(user.id);
    if (res.ok) loadUsers();
    else alert(res.error);
  }

  async function handleUnlock(user) {
    const res = await superAdminApi.unlockUser(user.id);
    if (res.ok) loadUsers();
    else alert(res.error);
  }

  async function handleDelete(user) {
    if (!window.confirm(`Delete user "${user.first_name} ${user.last_name}" (${user.email})?\n\nThis cannot be undone.`)) return;
    const res = await superAdminApi.deleteUser(user.id);
    if (res.ok) setUsers(prev => prev.filter(u => u.id !== user.id));
    else alert(res.error);
  }

  async function handleBulkUpload() {
    if (!bulkFile) return;
    setBulkUploading(true);
    const fd = new FormData();
    fd.append('file', bulkFile);
    const res = await superAdminApi.bulkUploadUsers(fd);
    setBulkUploading(false);
    if (res.ok) { setShowBulk(false); setBulkFile(null); loadUsers(); }
    else alert(res.error);
  }

  const columns = [
    {
      key: 'name', header: 'Name', sortable: true,
      accessor: r => `${r.first_name || ''} ${r.last_name || ''}`.trim(),
      render: r => <span className="font-medium text-gray-900">{r.first_name} {r.last_name}</span>,
    },
    { key: 'email', header: 'Email', sortable: true, accessor: 'email' },
    { key: 'department', header: 'Department', accessor: r => r.department_name || '—' },
    { key: 'role', header: 'Role', render: r => <RoleBadge role={r.role} /> },
    {
      key: 'status', header: 'Status',
      render: r => {
        const status = r.is_locked ? 'locked' : r.is_active ? 'active' : 'inactive';
        return <StatusBadge status={status} />;
      },
    },
    { key: 'last_login', header: 'Last Login', accessor: r => formatDate(r.last_login) },
    {
      key: 'actions', header: 'Actions',
      render: r => {
        const status = r.is_locked ? 'locked' : r.is_active ? 'active' : 'inactive';
        return (
          <div className="flex items-center gap-1">
            <button title="Reset Password" onClick={() => handleResetPassword(r)} className="p-1.5 text-blue-600 hover:bg-blue-50 rounded">
              <RefreshCw className="w-4 h-4" />
            </button>
            <button title={r.is_active ? 'Deactivate' : 'Activate'} onClick={() => handleToggleActive(r)} className="p-1.5 rounded">
              {r.is_active ? <XCircle className="w-4 h-4 text-yellow-600" /> : <CheckCircle className="w-4 h-4 text-green-600" />}
            </button>
            {status === 'locked' && (
              <button title="Unlock" onClick={() => handleUnlock(r)} className="p-1.5 text-orange-600 hover:bg-orange-50 rounded">
                <Unlock className="w-4 h-4" />
              </button>
            )}
            <button title="Delete" onClick={() => handleDelete(r)} className="p-1.5 text-red-600 hover:bg-red-50 rounded">
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        );
      },
    },
  ];

  return (
    <AppLayout title="User Management" subtitle="Manage platform users and access">
      {/* Filters */}
      <div className="card p-4 mb-4 flex flex-wrap items-center gap-3">
        <select className="input w-40" value={roleFilter} onChange={e => setRoleFilter(e.target.value)}>
          <option value="">All Roles</option>
          {ROLES.map(r => <option key={r} value={r}>{r.replace('_', ' ')}</option>)}
        </select>
        <select className="input w-40" value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
          <option value="">All Statuses</option>
          {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <button onClick={loadUsers} className="btn-secondary flex items-center gap-2">
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
        <div className="ml-auto flex items-center gap-2">
          <button onClick={() => setShowBulk(true)} className="btn-secondary flex items-center gap-2">
            <Upload className="w-4 h-4" /> Bulk Upload
          </button>
          <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-2">
            <UserPlus className="w-4 h-4" /> Create User
          </button>
        </div>
      </div>

      {error && <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">{error}</div>}

      <DataTable
        columns={columns}
        data={users}
        loading={loading}
        emptyMessage="No users found"
        rowKey="id"
        searchable
      />

      {/* Create User Modal */}
      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title="Create New User" size="md"
        footer={
          <>
            <button onClick={() => setShowCreate(false)} className="btn-secondary">Cancel</button>
            <button onClick={handleCreate} disabled={creating} className="btn-primary">
              {creating ? 'Creating…' : 'Create User'}
            </button>
          </>
        }
      >
        <form onSubmit={handleCreate} className="space-y-4">
          {formError && <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm">{formError}</div>}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">First Name</label>
              <input className="input" value={form.first_name} onChange={e => setForm(f => ({ ...f, first_name: e.target.value }))} placeholder="John" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
              <input className="input" value={form.last_name} onChange={e => setForm(f => ({ ...f, last_name: e.target.value }))} placeholder="Doe" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input className="input" type="email" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} placeholder="john@example.com" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
            <select className="input" value={form.role} onChange={e => setForm(f => ({ ...f, role: e.target.value }))}>
              {ROLES.map(r => <option key={r} value={r}>{r.replace('_', ' ')}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Department</label>
            <select className="input" value={form.department} onChange={e => setForm(f => ({ ...f, department: e.target.value }))}>
              <option value="">Select department</option>
              {DEPARTMENTS.map(d => <option key={d} value={d}>{d}</option>)}
            </select>
          </div>
        </form>
      </Modal>

      {/* Bulk Upload Modal */}
      <Modal isOpen={showBulk} onClose={() => setShowBulk(false)} title="Bulk Upload Users" size="md"
        footer={
          <>
            <button onClick={() => setShowBulk(false)} className="btn-secondary">Cancel</button>
            <button onClick={handleBulkUpload} disabled={!bulkFile || bulkUploading} className="btn-primary">
              {bulkUploading ? 'Uploading…' : 'Upload'}
            </button>
          </>
        }
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-600">Upload an Excel (.xlsx) file with columns: first_name, last_name, email, role, department.</p>
          <div
            onDragOver={e => e.preventDefault()}
            onDrop={e => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f) setBulkFile(f); }}
            className="border-2 border-dashed border-gray-300 rounded-xl p-10 text-center cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition-colors"
            onClick={() => document.getElementById('bulk-file-input').click()}
          >
            <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
            <p className="text-sm font-medium text-gray-700">{bulkFile ? bulkFile.name : 'Drag & drop or click to select Excel file'}</p>
            <p className="text-xs text-gray-400 mt-1">.xlsx files only</p>
            <input id="bulk-file-input" type="file" accept=".xlsx,.xls" className="hidden" onChange={e => setBulkFile(e.target.files[0])} />
          </div>
          <button
            onClick={async () => {
              const res = await superAdminApi.downloadBulkTemplate();
              if (res.ok) { const url = URL.createObjectURL(res.blob); const a = document.createElement('a'); a.href = url; a.download = 'user_template.xlsx'; a.click(); }
            }}
            className="btn-secondary w-full text-sm"
          >
            Download Template
          </button>
        </div>
      </Modal>
    </AppLayout>
  );
}
