import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import DocumentUploadModal from "../components/DocumentUploadModal.jsx";
import DocumentStatusTracker from "../components/DocumentStatusTracker.jsx";
import { debounce } from "../utils/performance.js";
import { adminApi } from "../services/adminApi.js";

const PAGE_SIZE_OPTIONS = [10, 25, 50];

const badge = {
  uploaded: "bg-blue-100 text-blue-800",
  processing: "bg-yellow-100 text-yellow-800",
  reviewed: "bg-purple-100 text-purple-800",
  approved: "bg-emerald-100 text-emerald-800",
  rejected: "bg-red-100 text-red-800",
  failed: "bg-red-100 text-red-800",
};

export default React.memo(function DocumentManagement() {
  const [documents, setDocuments] = useState([]);
  const [filters, setFilters] = useState({ status: "", file_type: "", search_query: "", page: 1, page_size: 10 });
  const [uploadOpen, setUploadOpen] = useState(false);
  const [selected, setSelected] = useState([]);
  const [trackingDoc, setTrackingDoc] = useState(null);
  const [trackingStatus, setTrackingStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback((overrideFilters) => {
    setLoading(true);
    adminApi.getDocuments(overrideFilters ?? filters).then((res) => {
      if (res.ok) setDocuments(res.data?.documents || []);
      setLoading(false);
    });
  }, [filters]);

  useEffect(() => { load(); }, [filters.page, filters.page_size]);

  const debouncedLoad = useMemo(() => debounce(load, 300), [load]);

  const deleteDoc = async (id) => {
    if (!window.confirm("Delete this document?")) return;
    await adminApi.deleteDocument(id);
    load();
  };

  const openTracker = async (doc) => {
    setTrackingDoc(doc);
    const res = await adminApi.getDocumentStatus(doc.id);
    if (res.ok) setTrackingStatus(res.data);
  };

  const handleRetry = async (id) => {
    await adminApi.reprocessDocument(id);
    load();
    if (trackingDoc?.id === id) {
      const res = await adminApi.getDocumentStatus(id);
      if (res.ok) setTrackingStatus(res.data);
    }
  };

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-6">
      <DocumentUploadModal open={uploadOpen} onClose={() => setUploadOpen(false)} onUploaded={load} />

      {trackingDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-md rounded-lg border bg-white p-5 shadow-xl">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="font-semibold text-slate-900">{trackingDoc.title}</h2>
              <button onClick={() => { setTrackingDoc(null); setTrackingStatus(null); }} className="text-slate-400 hover:text-slate-700 text-lg leading-none">&times;</button>
            </div>
            <DocumentStatusTracker
              status={trackingStatus}
              errorMessage={trackingDoc.status === "failed" ? (trackingDoc.malware_scan_result || "Processing failed") : null}
              onRetry={() => handleRetry(trackingDoc.id)}
            />
            <div className="mt-4 flex gap-2">
              <Link
                to={`/admin/documents/${trackingDoc.id}/versions`}
                className="rounded border px-3 py-2 text-sm hover:bg-slate-50"
                onClick={() => { setTrackingDoc(null); setTrackingStatus(null); }}
              >
                View Versions
              </Link>
              <Link
                to="/admin/approvals"
                className="rounded border px-3 py-2 text-sm hover:bg-slate-50"
                onClick={() => { setTrackingDoc(null); setTrackingStatus(null); }}
              >
                Go to Approvals
              </Link>
            </div>
          </div>
        </div>
      )}

      <div className="mx-auto max-w-7xl">
        <header className="flex items-center justify-between gap-3 border-b pb-5">
          <div>
            <h1 className="text-2xl font-semibold">Document Management</h1>
            <p className="text-sm text-slate-500">{documents.length} documents loaded</p>
          </div>
          <div className="flex gap-2">
            <Link to="/admin/approvals" className="rounded border px-3 py-2 text-sm hover:bg-white">
              Approval Queue
            </Link>
            <button className="rounded bg-slate-900 px-3 py-2 text-sm text-white" onClick={() => setUploadOpen(true)}>
              Upload
            </button>
          </div>
        </header>

        <section className="mt-5 grid gap-3 md:grid-cols-5">
          <input
            className="rounded border px-3 py-2 text-sm"
            placeholder="Search title"
            value={filters.search_query}
            onChange={(e) => {
              const updated = { ...filters, search_query: e.target.value, page: 1 };
              setFilters(updated);
              debouncedLoad(updated);
            }}
          />
          <select
            className="rounded border px-3 py-2 text-sm"
            value={filters.status}
            onChange={(e) => {
              const updated = { ...filters, status: e.target.value, page: 1 };
              setFilters(updated);
              debouncedLoad(updated);
            }}
          >
            <option value="">All statuses</option>
            <option>uploaded</option>
            <option>processing</option>
            <option>reviewed</option>
            <option>approved</option>
            <option>rejected</option>
            <option>failed</option>
          </select>
          <select
            className="rounded border px-3 py-2 text-sm"
            value={filters.file_type}
            onChange={(e) => {
              const updated = { ...filters, file_type: e.target.value, page: 1 };
              setFilters(updated);
              debouncedLoad(updated);
            }}
          >
            <option value="">All types</option>
            <option>pdf</option>
            <option>docx</option>
            <option>txt</option>
            <option>xlsx</option>
          </select>
          <select
            className="rounded border px-3 py-2 text-sm"
            value={filters.page_size}
            onChange={(e) => {
              const updated = { ...filters, page_size: Number(e.target.value), page: 1 };
              setFilters(updated);
              load(updated);
            }}
          >
            {PAGE_SIZE_OPTIONS.map((n) => (
              <option key={n} value={n}>{n} per page</option>
            ))}
          </select>
          <button className="rounded border px-3 py-2 text-sm" onClick={() => load()}>
            Apply
          </button>
        </section>

        {selected.length > 0 && (
          <button className="mt-3 rounded border border-red-200 px-3 py-2 text-sm text-red-700">
            Bulk delete ({selected.length})
          </button>
        )}

        <div className="mt-5 overflow-x-auto rounded border bg-white">
          <table className="w-full text-left text-sm">
            <thead className="border-b bg-slate-50">
              <tr>
                <th className="p-3">
                  <input
                    type="checkbox"
                    onChange={(e) =>
                      setSelected(e.target.checked ? documents.map((d) => d.id) : [])
                    }
                  />
                </th>
                <th className="px-3 py-3">Title</th>
                <th className="px-3 py-3">Type</th>
                <th className="px-3 py-3">Size</th>
                <th className="px-3 py-3">Status</th>
                <th className="px-3 py-3">Department</th>
                <th className="px-3 py-3">Uploaded</th>
                <th className="px-3 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={8} className="px-3 py-8 text-center text-slate-400">Loading...</td></tr>
              ) : documents.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-3 py-8 text-center text-slate-400">
                    No documents found.
                  </td>
                </tr>
              ) : (
                documents.map((doc) => (
                  <tr key={doc.id} className="border-b hover:bg-slate-50">
                    <td className="p-3">
                      <input
                        type="checkbox"
                        checked={selected.includes(doc.id)}
                        onChange={(e) =>
                          setSelected(
                            e.target.checked
                              ? [...selected, doc.id]
                              : selected.filter((id) => id !== doc.id)
                          )
                        }
                      />
                    </td>
                    <td className="px-3 py-3 font-medium text-slate-900 max-w-xs truncate">
                      {doc.title}
                    </td>
                    <td className="px-3 py-3 text-slate-500">{doc.file_type?.toUpperCase()}</td>
                    <td className="px-3 py-3 text-slate-500">{doc.file_size_mb} MB</td>
                    <td className="px-3 py-3">
                      <span className={`rounded px-2 py-1 text-xs font-medium ${badge[doc.status] || "bg-slate-100"}`}>
                        {doc.status}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-slate-500">{doc.department_id || "General"}</td>
                    <td className="px-3 py-3 text-slate-400 text-xs">
                      {new Date(doc.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-3 py-3">
                      <div className="flex flex-wrap gap-2 text-xs">
                        <button
                          className="text-blue-600 underline"
                          onClick={() => openTracker(doc)}
                        >
                          Details
                        </button>
                        <Link
                          to={`/admin/documents/${doc.id}/versions`}
                          className="text-slate-600 underline"
                        >
                          Versions
                        </Link>
                        {doc.status === "failed" && (
                          <button
                            className="text-yellow-700 underline"
                            onClick={() => handleRetry(doc.id)}
                          >
                            Reprocess
                          </button>
                        )}
                        <button
                          className="text-red-700 underline"
                          onClick={() => deleteDoc(doc.id)}
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="mt-4 flex items-center justify-between">
          <button
            className="rounded border px-3 py-2 text-sm disabled:opacity-40"
            disabled={filters.page <= 1}
            onClick={() => setFilters({ ...filters, page: Math.max(1, filters.page - 1) })}
          >
            Previous
          </button>
          <span className="text-sm text-slate-500">Page {filters.page}</span>
          <button
            className="rounded border px-3 py-2 text-sm"
            onClick={() => setFilters({ ...filters, page: filters.page + 1 })}
          >
            Next
          </button>
        </div>
      </div>
    </main>
  );
});
