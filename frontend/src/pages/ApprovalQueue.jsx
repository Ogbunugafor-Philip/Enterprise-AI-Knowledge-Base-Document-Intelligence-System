import React, { useEffect, useState } from "react";
import { CheckCircle, XCircle, Filter, RefreshCw } from "lucide-react";
import { adminApi } from "../services/adminApi.js";
import ApprovalModal from "../components/ApprovalModal.jsx";

export default function ApprovalQueue() {
  const [data, setData] = useState({ documents: [], total_pending: 0, total_reviewed: 0, page: 1, page_size: 20 });
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [bulkSelected, setBulkSelected] = useState(new Set());
  const [filterDept, setFilterDept] = useState("");
  const [filterType, setFilterType] = useState("");
  const [toast, setToast] = useState("");

  const loadQueue = async (page = 1) => {
    setLoading(true);
    const [qRes, sRes] = await Promise.all([
      adminApi.getApprovalQueue({ page, page_size: 20 }),
      adminApi.getGovernanceStats(),
    ]);
    if (qRes.ok) setData(qRes.data);
    if (sRes.ok) setStats(sRes.data);
    setLoading(false);
  };

  useEffect(() => { loadQueue(); }, []);

  const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(""), 3000); };

  const handleApprove = async (docId) => {
    const res = await adminApi.approveDocument({ document_id: docId, action: "approve" });
    if (res.ok) { showToast("Document approved."); loadQueue(data.page); setSelected(null); }
    else throw new Error(res.error);
  };

  const handleReject = async (docId, reason) => {
    const res = await adminApi.rejectDocument({ document_id: docId, action: "reject", rejection_reason: reason });
    if (res.ok) { showToast("Document rejected."); loadQueue(data.page); setSelected(null); }
    else throw new Error(res.error);
  };

  const handleBulkApprove = async () => {
    for (const id of bulkSelected) await adminApi.approveDocument({ document_id: id, action: "approve" });
    setBulkSelected(new Set());
    showToast(`${bulkSelected.size} document(s) approved.`);
    loadQueue(data.page);
  };

  const toggleBulk = (id) => {
    setBulkSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const filtered = data.documents.filter((doc) => {
    if (filterDept && doc.department_id !== filterDept) return false;
    if (filterType && doc.file_type !== filterType) return false;
    return true;
  });

  const fileTypes = [...new Set(data.documents.map((d) => d.file_type).filter(Boolean))];

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-6">
      {toast && (
        <div className="fixed top-4 right-4 z-50 rounded bg-slate-900 px-4 py-2 text-sm text-white shadow">
          {toast}
        </div>
      )}
      {selected && (
        <ApprovalModal
          document={selected}
          onApprove={handleApprove}
          onReject={handleReject}
          onClose={() => setSelected(null)}
        />
      )}

      <div className="mx-auto max-w-6xl">
        <header className="mb-6 flex flex-col gap-3 border-b pb-5 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Approval Queue</h1>
            <p className="text-sm text-slate-600">Review and approve documents before they become searchable.</p>
          </div>
          <button onClick={() => loadQueue()} className="flex items-center gap-1 rounded border px-3 py-2 text-sm hover:bg-white">
            <RefreshCw className="h-4 w-4" /> Refresh
          </button>
        </header>

        {/* Stats bar */}
        <div className="mb-5 grid gap-4 md:grid-cols-4">
          {[
            ["Pending", data.total_pending, "bg-yellow-50 border-yellow-200 text-yellow-800"],
            ["Reviewed", data.total_reviewed, "bg-blue-50 border-blue-200 text-blue-800"],
            ["Approved", stats?.total_approved ?? "—", "bg-emerald-50 border-emerald-200 text-emerald-800"],
            ["Rejected", stats?.total_rejected ?? "—", "bg-red-50 border-red-200 text-red-800"],
          ].map(([label, value, cls]) => (
            <div key={label} className={`rounded border p-4 ${cls}`}>
              <div className="text-xs font-medium">{label}</div>
              <div className="mt-1 text-2xl font-semibold">{value}</div>
            </div>
          ))}
        </div>

        {/* Filters */}
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <Filter className="h-4 w-4 text-slate-500" />
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="rounded border border-slate-300 px-3 py-1.5 text-sm"
          >
            <option value="">All file types</option>
            {fileTypes.map((t) => <option key={t} value={t}>{t.toUpperCase()}</option>)}
          </select>
          {bulkSelected.size > 0 && (
            <button
              onClick={handleBulkApprove}
              className="ml-auto flex items-center gap-1 rounded bg-emerald-600 px-3 py-1.5 text-sm text-white hover:bg-emerald-700"
            >
              <CheckCircle className="h-4 w-4" />
              Approve {bulkSelected.size} selected
            </button>
          )}
        </div>

        {/* Table */}
        <div className="overflow-x-auto rounded border bg-white">
          <table className="w-full text-left text-sm">
            <thead className="border-b bg-slate-50">
              <tr>
                <th className="w-8 px-4 py-3">
                  <input
                    type="checkbox"
                    checked={bulkSelected.size === filtered.length && filtered.length > 0}
                    onChange={() => {
                      if (bulkSelected.size === filtered.length) setBulkSelected(new Set());
                      else setBulkSelected(new Set(filtered.map((d) => d.id)));
                    }}
                  />
                </th>
                <th className="px-4 py-3">Title</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Department</th>
                <th className="px-4 py-3">Uploaded by</th>
                <th className="px-4 py-3">Date</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr><td colSpan={8} className="px-4 py-8 text-center text-slate-400">Loading…</td></tr>
              ) : filtered.length === 0 ? (
                <tr><td colSpan={8} className="px-4 py-8 text-center text-slate-400">No documents pending review.</td></tr>
              ) : (
                filtered.map((doc) => (
                  <tr
                    key={doc.id}
                    className="cursor-pointer hover:bg-slate-50"
                    onClick={() => setSelected(doc)}
                  >
                    <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        checked={bulkSelected.has(doc.id)}
                        onChange={() => toggleBulk(doc.id)}
                      />
                    </td>
                    <td className="px-4 py-3 font-medium text-slate-900">{doc.title}</td>
                    <td className="px-4 py-3 text-slate-500">{doc.file_type?.toUpperCase()}</td>
                    <td className="px-4 py-3 text-slate-500">{doc.department_id ?? "—"}</td>
                    <td className="px-4 py-3 text-slate-500">{doc.uploaded_by}</td>
                    <td className="px-4 py-3 text-slate-500">{new Date(doc.created_at).toLocaleDateString()}</td>
                    <td className="px-4 py-3">
                      <span className={`rounded px-2 py-0.5 text-xs font-medium ${
                        doc.status === "reviewed" ? "bg-blue-100 text-blue-700" : "bg-yellow-100 text-yellow-700"
                      }`}>{doc.status}</span>
                    </td>
                    <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                      <div className="flex gap-1">
                        <button
                          onClick={() => handleApprove(doc.id)}
                          className="rounded border border-emerald-300 px-2 py-1 text-xs text-emerald-700 hover:bg-emerald-50"
                        >
                          <CheckCircle className="h-3.5 w-3.5" />
                        </button>
                        <button
                          onClick={() => setSelected(doc)}
                          className="rounded border border-red-300 px-2 py-1 text-xs text-red-600 hover:bg-red-50"
                        >
                          <XCircle className="h-3.5 w-3.5" />
                        </button>
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
          <button disabled={data.page <= 1} onClick={() => loadQueue(data.page - 1)} className="rounded border px-3 py-1.5 disabled:opacity-40 hover:bg-white">
            Previous
          </button>
          <span>Page {data.page}</span>
          <button onClick={() => loadQueue(data.page + 1)} className="rounded border px-3 py-1.5 hover:bg-white">
            Next
          </button>
        </div>
      </div>
    </main>
  );
}
