import React, { useEffect, useState } from "react";
import DocumentUploadModal from "../components/DocumentUploadModal.jsx";
import { adminApi } from "../services/adminApi.js";

const badge = { uploaded: "bg-blue-100 text-blue-800", processing: "bg-yellow-100 text-yellow-800", reviewed: "bg-purple-100 text-purple-800", approved: "bg-emerald-100 text-emerald-800", rejected: "bg-red-100 text-red-800", failed: "bg-red-100 text-red-800" };

export default function DocumentManagement() {
  const [documents, setDocuments] = useState([]);
  const [filters, setFilters] = useState({ status: "", file_type: "", search_query: "", page: 1, page_size: 20 });
  const [uploadOpen, setUploadOpen] = useState(false);
  const [selected, setSelected] = useState([]);
  const load = () => adminApi.getDocuments(filters).then((res) => res.ok && setDocuments(res.data.documents || []));
  useEffect(() => { load(); }, [filters.page]);
  const deleteDoc = async (id) => { await adminApi.deleteDocument(id); load(); };
  return (
    <main className="min-h-screen bg-slate-50 px-4 py-6">
      <DocumentUploadModal open={uploadOpen} onClose={() => setUploadOpen(false)} onUploaded={load} />
      <div className="mx-auto max-w-7xl">
        <header className="flex justify-between gap-3"><h1 className="text-2xl font-semibold">Document management</h1><button className="rounded bg-slate-900 px-3 py-2 text-sm text-white" onClick={() => setUploadOpen(true)}>Upload</button></header>
        <section className="mt-5 grid gap-3 md:grid-cols-5">
          <input className="rounded border px-3 py-2 text-sm" placeholder="Search title" value={filters.search_query} onChange={(e) => setFilters({ ...filters, search_query: e.target.value })} />
          <select className="rounded border px-3 py-2 text-sm" value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}><option value="">All statuses</option><option>uploaded</option><option>processing</option><option>reviewed</option><option>approved</option><option>failed</option></select>
          <select className="rounded border px-3 py-2 text-sm" value={filters.file_type} onChange={(e) => setFilters({ ...filters, file_type: e.target.value })}><option value="">All types</option><option>pdf</option><option>docx</option><option>txt</option><option>xlsx</option></select>
          <input className="rounded border px-3 py-2 text-sm" type="date" />
          <button className="rounded border px-3 py-2 text-sm" onClick={load}>Apply</button>
        </section>
        {selected.length > 0 && <button className="mt-3 rounded border border-red-200 px-3 py-2 text-sm text-red-700">Bulk delete</button>}
        <table className="mt-5 w-full rounded border bg-white text-left text-sm">
          <thead><tr className="border-b"><th className="p-3"><input type="checkbox" /></th><th>Title</th><th>File type</th><th>Size</th><th>Status</th><th>Department</th><th>Uploaded by</th><th>Date</th><th>Actions</th></tr></thead>
          <tbody>{documents.map((doc) => <tr key={doc.id} className="border-b"><td className="p-3"><input type="checkbox" onChange={(e) => setSelected(e.target.checked ? [...selected, doc.id] : selected.filter((id) => id !== doc.id))} /></td><td>{doc.title}</td><td>{doc.file_type}</td><td>{doc.file_size_mb} MB</td><td><span className={`rounded px-2 py-1 text-xs ${badge[doc.status] || "bg-slate-100"}`}>{doc.status}</span></td><td>{doc.department_id || "General"}</td><td>{doc.uploaded_by}</td><td>{new Date(doc.created_at).toLocaleDateString()}</td><td className="space-x-2"><button className="underline">View Details</button>{doc.status === "failed" && <button className="underline" onClick={() => adminApi.reprocessDocument(doc.id)}>Reprocess</button>}<button className="text-red-700 underline" onClick={() => deleteDoc(doc.id)}>Delete</button></td></tr>)}</tbody>
        </table>
        <div className="mt-4 flex justify-between"><button className="rounded border px-3 py-2 text-sm" onClick={() => setFilters({ ...filters, page: Math.max(1, filters.page - 1) })}>Previous</button><button className="rounded border px-3 py-2 text-sm" onClick={() => setFilters({ ...filters, page: filters.page + 1 })}>Next</button></div>
      </div>
    </main>
  );
}
