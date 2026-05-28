import React, { useState, useEffect, useCallback } from 'react';
import { Building2, Plus, Edit, Trash2 } from 'lucide-react';
import AppLayout from '../components/Layout/AppLayout.jsx';
import DataTable from '../components/UI/DataTable.jsx';
import Modal from '../components/UI/Modal.jsx';
import StatsCard from '../components/UI/StatsCard.jsx';
import { superAdminApi } from '../services/superAdminApi.js';

const PLANS = ['free', 'starter', 'enterprise'];
const PLAN_BADGE = { free: 'badge-gray', starter: 'badge-blue', enterprise: 'badge-purple' };

function slugify(str) {
  return str.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
}

function formatDate(ts) {
  if (!ts) return '—';
  return new Date(ts).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
}

export default function OrganizationManagement() {
  const [orgs, setOrgs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [formError, setFormError] = useState('');
  const [form, setForm] = useState({ name: '', slug: '', description: '', plan: 'free' });

  const load = useCallback(async () => {
    setLoading(true);
    const res = await superAdminApi.getOrganizations();
    if (res.ok) setOrgs(res.data?.organizations || res.data || []);
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  function handleNameChange(name) {
    setForm(f => ({ ...f, name, slug: slugify(name) }));
  }

  async function handleCreate(e) {
    e.preventDefault();
    setFormError('');
    if (!form.name || !form.slug) { setFormError('Name and slug are required.'); return; }
    setCreating(true);
    const res = await superAdminApi.createOrganization(form);
    setCreating(false);
    if (res.ok) { setShowCreate(false); setForm({ name: '', slug: '', description: '', plan: 'free' }); load(); }
    else setFormError(res.error);
  }

  async function handleDelete(org) {
    if (!window.confirm(`Delete organization "${org.name}"? This cannot be undone.`)) return;
    const res = await superAdminApi.deleteOrganization(org.id);
    if (res.ok) load();
    else alert(res.error);
  }

  const total = orgs.length;
  const active = orgs.filter(o => o.is_active !== false).length;
  const inactive = total - active;

  const columns = [
    { key: 'name', header: 'Name', sortable: true, render: r => <span className="font-semibold text-gray-900">{r.name}</span> },
    { key: 'slug', header: 'Slug', render: r => <code className="text-xs bg-gray-100 px-1.5 py-0.5 rounded">{r.slug}</code> },
    { key: 'plan', header: 'Plan', render: r => <span className={PLAN_BADGE[r.plan] || 'badge-gray'}>{r.plan || 'free'}</span> },
    { key: 'status', header: 'Status', render: r => <span className={r.is_active !== false ? 'badge-green' : 'badge-gray'}>{r.is_active !== false ? 'Active' : 'Inactive'}</span> },
    { key: 'created_at', header: 'Created', sortable: true, accessor: r => formatDate(r.created_at) },
    {
      key: 'actions', header: 'Actions',
      render: r => (
        <div className="flex items-center gap-1">
          <button className="p-1.5 text-blue-600 hover:bg-blue-50 rounded" title="Edit" onClick={() => alert('Edit coming soon')}>
            <Edit className="w-4 h-4" />
          </button>
          <button className="p-1.5 text-red-600 hover:bg-red-50 rounded" title="Delete" onClick={() => handleDelete(r)}>
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      ),
    },
  ];

  return (
    <AppLayout title="Organizations" subtitle="Manage tenant organizations">
      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <StatsCard title="Total Organizations" value={loading ? '…' : total} icon={Building2} color="blue" />
        <StatsCard title="Active" value={loading ? '…' : active} icon={Building2} color="green" />
        <StatsCard title="Inactive" value={loading ? '…' : inactive} icon={Building2} color="gray" />
      </div>

      <DataTable
        columns={columns}
        data={orgs}
        loading={loading}
        emptyMessage="No organizations found"
        rowKey="id"
        searchable
        actions={
          <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" /> Create Organization
          </button>
        }
      />

      {/* Create Modal */}
      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title="Create Organization" size="md"
        footer={
          <>
            <button onClick={() => setShowCreate(false)} className="btn-secondary">Cancel</button>
            <button onClick={handleCreate} disabled={creating} className="btn-primary">
              {creating ? 'Creating…' : 'Create'}
            </button>
          </>
        }
      >
        <form onSubmit={handleCreate} className="space-y-4">
          {formError && <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm">{formError}</div>}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Organization Name</label>
            <input className="input" value={form.name} onChange={e => handleNameChange(e.target.value)} placeholder="Acme Corp" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Slug</label>
            <input className="input font-mono" value={form.slug} onChange={e => setForm(f => ({ ...f, slug: e.target.value }))} placeholder="acme-corp" />
            <p className="text-xs text-gray-400 mt-1">Auto-generated from name. Used in URLs.</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea className="input resize-none" rows={3} value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} placeholder="Optional description…" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Plan</label>
            <select className="input" value={form.plan} onChange={e => setForm(f => ({ ...f, plan: e.target.value }))}>
              {PLANS.map(p => <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>)}
            </select>
          </div>
        </form>
      </Modal>
    </AppLayout>
  );
}
