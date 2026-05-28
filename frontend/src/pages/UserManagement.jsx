import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Search, Filter, PlusCircle, Upload,
  CheckCircle, XCircle, Lock, MailWarning, RefreshCw, Eye
} from "lucide-react";
import { superAdminApi } from "../services/superAdminApi.js";
import CreateUserModal from "../components/CreateUserModal.jsx";
import BulkUploadModal from "../components/BulkUploadModal.jsx";
import UserDetailPanel from "../components/UserDetailPanel.jsx";

function StatusBadge({ user }) {
  const now = new Date();
  const isLocked = user.locked_until && new Date(user.locked_until) > now;
  if (isLocked) return <span className="rounded px-2 py-0.5 text-xs font-medium bg-red-100 text-red-700">Locked</span>;
  if (!user.is_active) return <span className="rounded px-2 py-0.5 text-xs font-medium bg-slate-100 text-slate-600">Inactive</span>;
  if (!user.is_verified) return <span className="rounded px-2 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-700">Unverified</span>;
  return <span className="rounded px-2 py-0.5 text-xs font-medium bg-emerald-100 text-emerald-700">Active</span>;
}

export default function UserManagement() {
  const [data, setData] = useState({ users: [], total_count: 0, page: 1, page_size: 20 });
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ search_query: "", is_active: "", is_verified: "", organization_id: "", role: "" });
  const [showCreate, setShowCreate] = useState(false);
  const [showBulk, setShowBulk] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [toast, setToast] = useState("");
  const [page, setPage] = useState(1);

  const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(""), 3000); };

  const load = async (p = 1) => {
    setLoading(true);
    const params = { page: p, page_size: 20 };
    if (filters.search_query) params.search_query = filters.search_query;
    if (filters.is_active !== "") params.is_active = filters.is_active === "true";
    if (filters.is_verified !== "") params.is_verified = filters.is_verified === "true";
    if (filters.organization_id) params.organization_id = filters.organization_id;
    if (filters.role) params.role = filters.role;
    const res = await superAdminApi.getUsers(params);
    if (res.ok) setData(res.data);
    setLoading(false);
  };

  useEffect(() => { load(page); }, [page]);

  const handleAction = async (action, userId) => {
    let res;
    if (action === "activate") res = await superAdminApi.activateUser(userId);
    else if (action === "deactivate") res = await superAdminApi.deactivateUser(userId, { user_id: userId, is_active: false });
    else if (action === "unlock") res = await superAdminApi.unlockUser(userId);
    else if (action === "reset") res = await superAdminApi.resetUserPassword(userId, { user_id: userId, force_change_on_login: true });
    if (res?.ok) { showToast(`${action} successful.`); load(page); }
    else showToast(res?.error || "Action failed");
  };

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-6">
      {toast && (
        <div className="fixed top-4 right-4 z-50 rounded bg-slate-900 px-4 py-2 text-sm text-white shadow">
          {toast}
        </div>
      )}
      {showCreate && <CreateUserModal onClose={() => setShowCreate(false)} onCreated={() => { setShowCreate(false); load(1); showToast("User created."); }} />}
      {showBulk && <BulkUploadModal onClose={() => setShowBulk(false)} onComplete={() => { setShowBulk(false); load(1); }} />}
      {selectedUser && <UserDetailPanel user={selectedUser} onClose={() => setSelectedUser(null)} onRefresh={() => load(page)} />}

      <div className="mx-auto max-w-7xl">
        <header className="mb-6 flex flex-col gap-3 border-b pb-5 md:flex-row md:items-center md:justify-between">
          <div>
            <Link to="/superadmin/dashboard" className="text-sm text-slate-500 hover:text-slate-700">← Super Admin</Link>
            <h1 className="mt-1 text-2xl font-semibold">User Management</h1>
            <p className="text-sm text-slate-500">{data.total_count} users total</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button onClick={() => setShowBulk(true)} className="flex items-center gap-1 rounded border px-3 py-2 text-sm hover:bg-white">
              <Upload className="h-4 w-4" /> Bulk Upload
            </button>
            <button onClick={() => setShowCreate(true)} className="flex items-center gap-1 rounded bg-slate-900 px-3 py-2 text-sm text-white hover:bg-slate-700">
              <PlusCircle className="h-4 w-4" /> Create User
            </button>
          </div>
        </header>

        {/* Filters */}
        <div className="mb-4 flex flex-wrap items-center gap-3 rounded border bg-white px-4 py-3">
          <Filter className="h-4 w-4 text-slate-400" />
          <div className="relative">
            <Search className="absolute left-2.5 top-2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search name or email…"
              value={filters.search_query}
              onChange={(e) => setFilters({ ...filters, search_query: e.target.value })}
              className="rounded border border-slate-300 py-1.5 pl-8 pr-3 text-sm focus:outline-none"
            />
          </div>
          <select
            value={filters.is_active}
            onChange={(e) => setFilters({ ...filters, is_active: e.target.value })}
            className="rounded border border-slate-300 px-3 py-1.5 text-sm"
          >
            <option value="">All status</option>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </select>
          <select
            value={filters.is_verified}
            onChange={(e) => setFilters({ ...filters, is_verified: e.target.value })}
            className="rounded border border-slate-300 px-3 py-1.5 text-sm"
          >
            <option value="">All verified</option>
            <option value="true">Verified</option>
            <option value="false">Unverified</option>
          </select>
          <button onClick={() => load(1)} className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-slate-50">
            <RefreshCw className="h-4 w-4" /> Apply
          </button>
        </div>

        {/* Table */}
        <div className="overflow-x-auto rounded border bg-white">
          <table className="w-full text-left text-sm">
            <thead className="border-b bg-slate-50">
              <tr>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">Role</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Verified</th>
                <th className="px-4 py-3">Last Login</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-slate-400">Loading…</td></tr>
              ) : data.users.length === 0 ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-slate-400">No users found.</td></tr>
              ) : (
                data.users.map((user) => (
                  <tr key={user.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3 font-medium text-slate-900">
                      {user.first_name} {user.last_name}
                    </td>
                    <td className="px-4 py-3 text-slate-600">{user.email}</td>
                    <td className="px-4 py-3 text-slate-500">{user.role ?? "—"}</td>
                    <td className="px-4 py-3"><StatusBadge user={user} /></td>
                    <td className="px-4 py-3">
                      {user.is_verified
                        ? <CheckCircle className="h-4 w-4 text-emerald-500" />
                        : <MailWarning className="h-4 w-4 text-yellow-500" />}
                    </td>
                    <td className="px-4 py-3 text-slate-400 text-xs">
                      {user.last_login ? new Date(user.last_login).toLocaleDateString() : "Never"}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        <button onClick={() => setSelectedUser(user)} className="rounded border px-2 py-1 text-xs hover:bg-slate-100" title="View">
                          <Eye className="h-3.5 w-3.5" />
                        </button>
                        {user.is_active ? (
                          <button onClick={() => handleAction("deactivate", user.id)} className="rounded border border-slate-300 px-2 py-1 text-xs text-slate-600 hover:bg-slate-50" title="Deactivate">
                            <XCircle className="h-3.5 w-3.5" />
                          </button>
                        ) : (
                          <button onClick={() => handleAction("activate", user.id)} className="rounded border border-emerald-300 px-2 py-1 text-xs text-emerald-600 hover:bg-emerald-50" title="Activate">
                            <CheckCircle className="h-3.5 w-3.5" />
                          </button>
                        )}
                        {user.locked_until && new Date(user.locked_until) > new Date() && (
                          <button onClick={() => handleAction("unlock", user.id)} className="rounded border border-yellow-300 px-2 py-1 text-xs text-yellow-600 hover:bg-yellow-50" title="Unlock">
                            <Lock className="h-3.5 w-3.5" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="mt-4 flex items-center gap-3 text-sm text-slate-500">
          <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="rounded border px-3 py-1.5 disabled:opacity-40 hover:bg-white">Previous</button>
          <span>Page {page} · {data.total_count} total</span>
          <button onClick={() => setPage(page + 1)} disabled={page * data.page_size >= data.total_count} className="rounded border px-3 py-1.5 disabled:opacity-40 hover:bg-white">Next</button>
        </div>
      </div>
    </main>
  );
}
