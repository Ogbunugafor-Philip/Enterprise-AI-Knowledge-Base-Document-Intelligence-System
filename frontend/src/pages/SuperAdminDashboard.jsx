import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Users, Building2, ShieldCheck, UserCheck, UserX,
  AlertTriangle, MailWarning, PlusCircle, Upload,
  ClipboardList, BarChart3, RefreshCw
} from "lucide-react";
import { superAdminApi } from "../services/superAdminApi.js";

function StatCard({ icon: Icon, label, value, color = "slate" }) {
  const colors = {
    slate: "bg-white border-slate-200 text-slate-900",
    green: "bg-emerald-50 border-emerald-200 text-emerald-800",
    red: "bg-red-50 border-red-200 text-red-800",
    yellow: "bg-yellow-50 border-yellow-200 text-yellow-800",
    blue: "bg-blue-50 border-blue-200 text-blue-800",
  };
  return (
    <div className={`rounded border p-4 shadow-sm ${colors[color]}`}>
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium opacity-75">{label}</span>
        <Icon className="h-5 w-5 opacity-60" />
      </div>
      <div className="mt-2 text-2xl font-semibold">{value ?? "—"}</div>
    </div>
  );
}

export default function SuperAdminDashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    const res = await superAdminApi.getDashboardStats();
    if (res.ok) setStats(res.data);
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-6">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <header className="mb-6 flex flex-col gap-3 border-b pb-5 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">Super Admin</h1>
            <p className="text-sm text-slate-500">Platform-wide governance and user management.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <nav className="flex flex-wrap gap-2 text-sm">
              {[
                { label: "Users", to: "/superadmin/users" },
                { label: "Organizations", to: "/super-admin" },
                { label: "Roles", to: "/super-admin" },
                { label: "Audit Logs", to: "/super-admin" },
                { label: "Monitoring", to: "/super-admin" },
              ].map(({ label, to }) => (
                <Link key={label} to={to} className="rounded border px-3 py-1.5 text-slate-600 hover:bg-white">
                  {label}
                </Link>
              ))}
            </nav>
            <button onClick={load} className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-white">
              <RefreshCw className="h-4 w-4" />
            </button>
          </div>
        </header>

        {/* Stats grid */}
        {loading ? (
          <p className="text-sm text-slate-400">Loading stats…</p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
            <StatCard icon={Building2} label="Organizations" value={stats?.total_organizations} />
            <StatCard icon={Users} label="Total Users" value={stats?.total_users} />
            <StatCard icon={UserCheck} label="Active Users" value={stats?.active_users} color="green" />
            <StatCard icon={UserX} label="Inactive Users" value={stats?.inactive_users} color="red" />
            <StatCard icon={MailWarning} label="Unverified" value={stats?.unverified_users} color="yellow" />
            <StatCard icon={AlertTriangle} label="Locked Accounts" value={stats?.locked_accounts} color="red" />
            <StatCard icon={PlusCircle} label="Created Today" value={stats?.users_created_today} color="blue" />
            <StatCard icon={BarChart3} label="Created This Month" value={stats?.users_created_this_month} color="blue" />
          </div>
        )}

        {/* Quick actions */}
        <section className="mt-8">
          <h2 className="mb-4 font-semibold text-slate-700">Quick Actions</h2>
          <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-4">
            <Link
              to="/superadmin/users"
              className="flex items-center gap-3 rounded border bg-white p-4 shadow-sm hover:border-slate-400"
            >
              <PlusCircle className="h-6 w-6 text-slate-600" />
              <div>
                <p className="font-medium text-slate-900">Create User</p>
                <p className="text-xs text-slate-500">Add a new platform user</p>
              </div>
            </Link>
            <Link
              to="/superadmin/users"
              className="flex items-center gap-3 rounded border bg-white p-4 shadow-sm hover:border-slate-400"
            >
              <Upload className="h-6 w-6 text-slate-600" />
              <div>
                <p className="font-medium text-slate-900">Bulk Upload</p>
                <p className="text-xs text-slate-500">Import users from Excel</p>
              </div>
            </Link>
            <Link
              to="/superadmin/users"
              className="flex items-center gap-3 rounded border bg-white p-4 shadow-sm hover:border-slate-400"
            >
              <Users className="h-6 w-6 text-slate-600" />
              <div>
                <p className="font-medium text-slate-900">View All Users</p>
                <p className="text-xs text-slate-500">Browse and manage users</p>
              </div>
            </Link>
            <Link
              to="/super-admin"
              className="flex items-center gap-3 rounded border bg-white p-4 shadow-sm hover:border-slate-400"
            >
              <Building2 className="h-6 w-6 text-slate-600" />
              <div>
                <p className="font-medium text-slate-900">Organizations</p>
                <p className="text-xs text-slate-500">Tenant management</p>
              </div>
            </Link>
          </div>
        </section>

        {/* System governance */}
        <section className="mt-8">
          <h2 className="mb-4 font-semibold text-slate-700">System Governance</h2>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded border bg-white p-5 shadow-sm">
              <div className="mb-3 flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-emerald-500" />
                <h3 className="font-semibold text-slate-800">Security Status</h3>
              </div>
              <ul className="space-y-2 text-sm text-slate-600">
                <li className="flex justify-between"><span>Locked accounts</span><span className="font-medium text-red-600">{stats?.locked_accounts ?? "—"}</span></li>
                <li className="flex justify-between"><span>Unverified users</span><span className="font-medium text-yellow-600">{stats?.unverified_users ?? "—"}</span></li>
                <li className="flex justify-between"><span>Inactive users</span><span className="font-medium text-slate-500">{stats?.inactive_users ?? "—"}</span></li>
              </ul>
            </div>
            <div className="rounded border bg-white p-5 shadow-sm">
              <div className="mb-3 flex items-center gap-2">
                <ClipboardList className="h-5 w-5 text-blue-500" />
                <h3 className="font-semibold text-slate-800">Recent Activity</h3>
              </div>
              {(stats?.recent_user_activity || []).length === 0 ? (
                <p className="text-sm text-slate-400">No recent activity.</p>
              ) : (
                <ul className="divide-y divide-slate-100">
                  {(stats?.recent_user_activity || []).slice(0, 5).map((entry) => (
                    <li key={entry.id} className="flex items-center justify-between py-1.5 text-xs text-slate-600">
                      <span className="font-mono">{entry.action}</span>
                      <span className="text-slate-400">{new Date(entry.created_at).toLocaleString()}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
