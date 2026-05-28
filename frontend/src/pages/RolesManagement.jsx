import React, { useState, useEffect, useCallback } from 'react';
import { Shield, Plus, Eye } from 'lucide-react';
import AppLayout from '../components/Layout/AppLayout.jsx';
import DataTable from '../components/UI/DataTable.jsx';
import Modal from '../components/UI/Modal.jsx';
import { superAdminApi } from '../services/superAdminApi.js';

export default function RolesManagement() {
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [formError, setFormError] = useState('');
  const [form, setForm] = useState({ name: '', description: '' });
  const [selectedRole, setSelectedRole] = useState(null);
  const [permissions, setPermissions] = useState([]);
  const [loadingPerms, setLoadingPerms] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    const res = await superAdminApi.getRoles();
    if (res.ok) setRoles(res.data?.roles || res.data || []);
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  async function viewPermissions(role) {
    setSelectedRole(role);
    setPermissions([]);
    setLoadingPerms(true);
    const res = await superAdminApi.getRolePermissions(role.id);
    if (res.ok) setPermissions(res.data?.permissions || res.data || []);
    setLoadingPerms(false);
  }

  async function handleCreate(e) {
    e.preventDefault();
    setFormError('');
    if (!form.name) { setFormError('Role name is required.'); return; }
    setCreating(true);
    const res = await superAdminApi.createRole(form);
    setCreating(false);
    if (res.ok) { setShowCreate(false); setForm({ name: '', description: '' }); load(); }
    else setFormError(res.error);
  }

  const columns = [
    { key: 'name', header: 'Role Name', sortable: true, render: r => <span className="font-semibold text-gray-900">{r.name}</span> },
    { key: 'description', header: 'Description', accessor: r => r.description || '—' },
    {
      key: 'system_role', header: 'Type',
      render: r => r.is_system_role || r.is_default
        ? <span className="badge-purple">System Role</span>
        : <span className="badge-gray">Custom</span>,
    },
    {
      key: 'permissions_count', header: 'Permissions',
      render: r => (
        <span className="font-medium text-gray-700">
          {r.permissions_count ?? r.permissions?.length ?? '—'}
        </span>
      ),
    },
    {
      key: 'actions', header: 'Actions',
      render: r => (
        <button onClick={() => viewPermissions(r)} className="flex items-center gap-1.5 text-xs px-3 py-1.5 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 font-medium">
          <Eye className="w-3.5 h-3.5" /> View Permissions
        </button>
      ),
    },
  ];

  return (
    <AppLayout title="Roles Management" subtitle="Manage roles and permissions">
      <DataTable
        columns={columns}
        data={roles}
        loading={loading}
        emptyMessage="No roles found"
        rowKey="id"
        searchable
        actions={
          <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" /> Create Role
          </button>
        }
      />

      {/* Permissions Modal */}
      <Modal isOpen={!!selectedRole} onClose={() => setSelectedRole(null)} title={`Permissions — ${selectedRole?.name}`} size="lg"
        footer={<button onClick={() => setSelectedRole(null)} className="btn-secondary">Close</button>}
      >
        {loadingPerms ? (
          <div className="text-center text-gray-400 py-8">Loading permissions…</div>
        ) : permissions.length === 0 ? (
          <div className="text-center text-gray-400 py-8">No permissions defined for this role.</div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {permissions.map((perm, i) => (
              <div key={i} className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg">
                <Shield className="w-4 h-4 text-blue-500 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-gray-800">{perm.name || perm.permission || perm}</p>
                  {perm.description && <p className="text-xs text-gray-500">{perm.description}</p>}
                </div>
              </div>
            ))}
          </div>
        )}
      </Modal>

      {/* Create Role Modal */}
      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title="Create Role" size="md"
        footer={
          <>
            <button onClick={() => setShowCreate(false)} className="btn-secondary">Cancel</button>
            <button onClick={handleCreate} disabled={creating} className="btn-primary">
              {creating ? 'Creating…' : 'Create Role'}
            </button>
          </>
        }
      >
        <form onSubmit={handleCreate} className="space-y-4">
          {formError && <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm">{formError}</div>}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Role Name</label>
            <input className="input" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} placeholder="e.g. EDITOR" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea className="input resize-none" rows={3} value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} placeholder="What can this role do?" />
          </div>
        </form>
      </Modal>
    </AppLayout>
  );
}
