import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, CheckSquare, XCircle, Upload, BarChart3, Clock } from 'lucide-react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import AppLayout from '../components/Layout/AppLayout.jsx';
import StatsCard from '../components/UI/StatsCard.jsx';
import { adminApi } from '../services/adminApi.js';
import { formatDistanceToNow } from 'date-fns';

const STATUS_COLORS = { approved: '#22c55e', reviewed: '#f59e0b', processing: '#3b82f6', uploaded: '#8b5cf6', failed: '#ef4444', rejected: '#f97316' };
const STATUS_BADGE  = { approved: 'badge-green', reviewed: 'badge-yellow', processing: 'badge-blue', uploaded: 'badge-purple', failed: 'badge-red', rejected: 'badge-red' };

export default function AdminDashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    adminApi.getDashboardStats().then(r => { if (r.ok) setStats(r.data); setLoading(false); });
  }, []);

  const pieData = stats?.documents_by_status
    ? Object.entries(stats.documents_by_status).map(([name, value]) => ({ name, value }))
    : [];

  return (
    <AppLayout title="Admin Dashboard" subtitle="Document management and governance overview">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
        <StatsCard title="Total Documents"  value={loading ? '…' : (stats?.total_documents ?? 0)}  icon={FileText}    color="blue" />
        <StatsCard title="Pending Approval" value={loading ? '…' : (stats?.pending_approval ?? 0)} icon={CheckSquare} color="yellow" />
        <StatsCard title="Approved"         value={loading ? '…' : (stats?.approved_documents ?? 0)} icon={CheckSquare} color="green" />
        <StatsCard title="Failed"           value={loading ? '…' : (stats?.failed_uploads ?? 0)}   icon={XCircle}    color="red" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card p-6">
          <h2 className="section-title flex items-center gap-2"><BarChart3 className="w-5 h-5 text-blue-500" />By Status</h2>
          {loading ? <div className="h-48 bg-gray-100 rounded-xl animate-pulse" /> : pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={85} paddingAngle={3} dataKey="value">
                  {pieData.map(e => <Cell key={e.name} fill={STATUS_COLORS[e.name] || '#94a3b8'} />)}
                </Pie>
                <Tooltip formatter={(v, n) => [v, n.charAt(0).toUpperCase() + n.slice(1)]} />
                <Legend formatter={v => v.charAt(0).toUpperCase() + v.slice(1)} />
              </PieChart>
            </ResponsiveContainer>
          ) : <div className="empty-state text-sm">No documents yet</div>}
        </div>

        <div className="card p-6 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="section-title m-0 flex items-center gap-2"><Clock className="w-5 h-5 text-blue-500" />Recent Uploads</h2>
            <button onClick={() => navigate('/admin/documents')} className="text-sm text-blue-600 font-medium">View all</button>
          </div>
          {loading ? <div className="space-y-3">{[1,2,3,4].map(i => <div key={i} className="h-12 bg-gray-100 rounded-xl animate-pulse" />)}</div>
            : !stats?.recent_uploads?.length ? <div className="empty-state text-sm">No recent uploads</div>
            : (
              <table className="table">
                <thead><tr><th>Document</th><th>Type</th><th>Status</th><th>When</th></tr></thead>
                <tbody>
                  {stats.recent_uploads.map(doc => (
                    <tr key={doc.id}>
                      <td className="font-medium max-w-xs truncate">{doc.title || doc.file_name}</td>
                      <td><span className="badge badge-gray text-xs">{doc.file_type?.split('/').pop() || 'file'}</span></td>
                      <td><span className={`badge ${STATUS_BADGE[doc.status] || 'badge-gray'}`}>{doc.status}</span></td>
                      <td className="text-gray-400 text-xs">{doc.created_at ? formatDistanceToNow(new Date(doc.created_at), { addSuffix: true }) : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
        </div>
      </div>

      <div className="mt-6 card p-6">
        <h2 className="section-title">Quick Actions</h2>
        <div className="flex flex-wrap gap-3">
          <button onClick={() => navigate('/admin/documents')} className="btn-primary"><Upload className="w-4 h-4" />Upload Document</button>
          <button onClick={() => navigate('/admin/approvals')} className="btn-secondary"><CheckSquare className="w-4 h-4" />Review Queue {stats?.pending_approval ? `(${stats.pending_approval})` : ''}</button>
          <button onClick={() => navigate('/admin/documents')} className="btn-secondary"><FileText className="w-4 h-4" />All Documents</button>
        </div>
      </div>
    </AppLayout>
  );
}
