import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { adminApi } from "../services/adminApi.js";

export default function AdminDashboard() {
  const [stats, setStats] = useState({ total_documents: 0, pending_approval: 0, approved_documents: 0, failed_uploads: 0, documents_by_status: {}, documents_by_type: {}, recent_uploads: [] });
  useEffect(() => { adminApi.getDashboardStats().then((res) => res.ok && setStats(res.data)); }, []);
  return (
    <main className="min-h-screen bg-slate-50 px-4 py-6">
      <div className="mx-auto max-w-6xl">
        <header className="flex flex-col gap-3 border-b pb-5 md:flex-row md:items-center md:justify-between">
          <div><h1 className="text-2xl font-semibold">Admin dashboard</h1><p className="text-sm text-slate-600">Document ingestion, approvals, and operational overview.</p></div>
          <nav className="flex flex-wrap gap-2 text-sm">
            <Link className="rounded border px-3 py-2" to="/admin/documents">Documents</Link>
            <Link className="rounded border px-3 py-2" to="/admin/documents?status=reviewed">Approvals</Link>
            <Link className="rounded border px-3 py-2" to="/super-admin">Users</Link>
            <Link className="rounded border px-3 py-2" to="/admin/dashboard">Monitoring</Link>
          </nav>
        </header>
        <section className="mt-6 grid gap-4 md:grid-cols-4">
          {[["Total documents", stats.total_documents], ["Pending approval", stats.pending_approval], ["Approved", stats.approved_documents], ["Failed uploads", stats.failed_uploads]].map(([label, value]) => (
            <div key={label} className="rounded border bg-white p-4"><div className="text-sm text-slate-500">{label}</div><div className="mt-2 text-2xl font-semibold">{value}</div></div>
          ))}
        </section>
        <section className="mt-6 grid gap-4 lg:grid-cols-2">
          <div className="rounded border bg-white p-4"><h2 className="font-semibold">Documents by status</h2>{Object.entries(stats.documents_by_status || {}).map(([k, v]) => <div key={k} className="mt-2 flex justify-between text-sm"><span>{k}</span><span>{v}</span></div>)}</div>
          <div className="rounded border bg-white p-4"><h2 className="font-semibold">Documents by file type</h2>{Object.entries(stats.documents_by_type || {}).map(([k, v]) => <div key={k} className="mt-2 flex justify-between text-sm"><span>{k}</span><span>{v}</span></div>)}</div>
        </section>
        <section className="mt-6 rounded border bg-white p-4">
          <div className="mb-3 flex items-center justify-between"><h2 className="font-semibold">Recent uploads</h2><span className="rounded bg-emerald-100 px-2 py-1 text-xs text-emerald-800">System healthy</span></div>
          <table className="w-full text-left text-sm"><thead><tr className="border-b"><th className="py-2">File</th><th>Type</th><th>Status</th><th>Uploaded by</th><th>Date</th></tr></thead><tbody>{(stats.recent_uploads || []).map((doc) => <tr key={doc.id} className="border-b"><td className="py-2">{doc.file_name}</td><td>{doc.file_type}</td><td>{doc.status}</td><td>{doc.uploaded_by}</td><td>{new Date(doc.created_at).toLocaleString()}</td></tr>)}</tbody></table>
        </section>
        <div className="mt-6 flex gap-2"><Link className="rounded bg-slate-900 px-3 py-2 text-sm text-white" to="/admin/documents">Upload Document</Link><Link className="rounded border px-3 py-2 text-sm" to="/admin/documents">View All Documents</Link><Link className="rounded border px-3 py-2 text-sm" to="/admin/documents?status=failed">View Failed Uploads</Link></div>
      </div>
    </main>
  );
}
