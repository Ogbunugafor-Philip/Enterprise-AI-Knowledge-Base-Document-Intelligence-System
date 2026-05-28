import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Building2, Users, UserCheck, UserX, Mail, Lock, Plus, Upload, Shield } from 'lucide-react';
import AppLayout from '../components/Layout/AppLayout.jsx';
import StatsCard from '../components/UI/StatsCard.jsx';
import { superAdminApi } from '../services/superAdminApi.js';

function timeAgo(ts) {
  if (!ts) return '';
  const diff = Math.floor((Date.now() - new Date(ts)) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

export default function SuperAdminDashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [activity, setActivity] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      const [statsRes, activityRes] = await Promise.all([
        superAdminApi.getDashboardStats(),
        superAdminApi.getRecentActivity(),
      ]);
      if (statsRes.ok) setStats(statsRes.data);
      if (activityRes.ok) setActivity((activityRes.data?.activities || activityRes.data || []).slice(0, 5));
      setLoading(false);
    }
    load();
  }, []);

  const s = stats || {};

  return (
    <AppLayout title="Super Admin" subtitle="Platform-wide governance and user management">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <StatsCard title="Organizations" value={loading ? '…' : (s.total_organizations ?? 0)} icon={Building2} color="blue" />
        <StatsCard title="Total Users" value={loading ? '…' : (s.total_users ?? 0)} icon={Users} color="indigo" />
        <StatsCard title="Active Users" value={loading ? '…' : (s.active_users ?? 0)} icon={UserCheck} color="green" />
        <StatsCard title="Inactive Users" value={loading ? '…' : (s.inactive_users ?? 0)} icon={UserX} color="yellow" />
        <StatsCard title="Unverified" value={loading ? '…' : (s.unverified_users ?? 0)} icon={Mail} color="yellow" />
        <StatsCard title="Locked Accounts" value={loading ? '…' : (s.locked_users ?? 0)} icon={Lock} color="red" />
        <StatsCard title="Created Today" value={loading ? '…' : (s.created_today ?? 0)} icon={Plus} color="green" />
        <StatsCard title="Created This Month" value={loading ? '…' : (s.created_this_month ?? 0)} icon={Users} color="purple" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Quick Actions */}
        <div className="card p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="flex flex-col gap-2">
            <button onClick={() => navigate('/superadmin/users')} className="btn-primary flex items-center gap-2">
              <Plus className="w-4 h-4" /> Create User
            </button>
            <button onClick={() => navigate('/superadmin/users')} className="btn-secondary flex items-center gap-2">
              <Upload className="w-4 h-4" /> Bulk Upload
            </button>
            <button onClick={() => navigate('/superadmin/users')} className="btn-secondary flex items-center gap-2">
              <Users className="w-4 h-4" /> View All Users
            </button>
            <button onClick={() => navigate('/superadmin/organizations')} className="btn-secondary flex items-center gap-2">
              <Building2 className="w-4 h-4" /> Organizations
            </button>
            <button onClick={() => navigate('/superadmin/roles')} className="btn-secondary flex items-center gap-2">
              <Shield className="w-4 h-4" /> Roles
            </button>
          </div>
        </div>

        {/* System Governance */}
        <div className="card p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-4">System Governance</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
              <div className="flex items-center gap-2">
                <Lock className="w-4 h-4 text-red-600" />
                <span className="text-sm font-medium text-red-700">Locked Accounts</span>
              </div>
              <span className="text-lg font-bold text-red-700">{loading ? '…' : (s.locked_users ?? 0)}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg">
              <div className="flex items-center gap-2">
                <Mail className="w-4 h-4 text-yellow-600" />
                <span className="text-sm font-medium text-yellow-700">Unverified Users</span>
              </div>
              <span className="text-lg font-bold text-yellow-700">{loading ? '…' : (s.unverified_users ?? 0)}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2">
                <UserX className="w-4 h-4 text-gray-600" />
                <span className="text-sm font-medium text-gray-700">Inactive Users</span>
              </div>
              <span className="text-lg font-bold text-gray-700">{loading ? '…' : (s.inactive_users ?? 0)}</span>
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="card p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-4">Recent Activity</h2>
          {activity.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-6">No recent activity</p>
          ) : (
            <div className="space-y-3">
              {activity.map((item, i) => (
                <div key={i} className="flex items-start gap-3">
                  <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-2 flex-shrink-0" />
                  <div className="min-w-0">
                    <p className="text-sm text-gray-800 truncate">{item.description || item.action || 'Action performed'}</p>
                    <p className="text-xs text-gray-400">{item.user_email || item.user || ''} · {timeAgo(item.timestamp || item.created_at)}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
