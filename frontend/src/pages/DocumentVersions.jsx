import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { Clock, CheckCircle, Archive, RotateCcw, Upload } from "lucide-react";
import { adminApi } from "../services/adminApi.js";

const STATUS_ICON = {
  approved: <CheckCircle className="h-4 w-4 text-emerald-500" />,
  archived: <Archive className="h-4 w-4 text-slate-400" />,
  rejected: <span className="h-4 w-4 rounded-full bg-red-400 inline-block" />,
};

export default function DocumentVersions() {
  const { documentId } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");
  const [showUpload, setShowUpload] = useState(false);
  const [uploadForm, setUploadForm] = useState({ title: "", description: "", file: null });
  const [uploading, setUploading] = useState(false);

  const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(""), 3000); };

  const load = async () => {
    setLoading(true);
    const res = await adminApi.getDocumentVersions(documentId);
    if (res.ok) setData(res.data);
    else setError("Failed to load versions.");
    setLoading(false);
  };

  useEffect(() => { load(); }, [documentId]);

  const handleRollback = async (versionId) => {
    if (!window.confirm("Roll back to this version? The current approved version will be archived.")) return;
    const res = await adminApi.rollbackVersion(documentId, versionId);
    if (res.ok) { showToast("Rolled back successfully."); load(); }
    else showToast("Rollback failed: " + res.error);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!uploadForm.file || !uploadForm.title.trim()) return;
    setUploading(true);
    const formData = new FormData();
    formData.append("file", uploadForm.file);
    formData.append("title", uploadForm.title);
    if (uploadForm.description) formData.append("description", uploadForm.description);
    const res = await adminApi.uploadDocumentVersion(documentId, formData);
    if (res.ok) { showToast("New version uploaded and queued for processing."); setShowUpload(false); load(); }
    else showToast("Upload failed: " + res.error);
    setUploading(false);
  };

  if (loading) return <main className="p-8 text-slate-500">Loading versions…</main>;
  if (error) return <main className="p-8 text-red-500">{error}</main>;

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-6">
      {toast && (
        <div className="fixed top-4 right-4 z-50 rounded bg-slate-900 px-4 py-2 text-sm text-white shadow">
          {toast}
        </div>
      )}

      <div className="mx-auto max-w-4xl">
        <div className="mb-6 flex items-center justify-between border-b pb-5">
          <div>
            <Link to="/admin/documents" className="text-sm text-slate-500 hover:text-slate-700">
              ← Back to Documents
            </Link>
            <h1 className="mt-1 text-2xl font-semibold">Version History</h1>
            <p className="text-sm text-slate-500">Document ID: {documentId}</p>
          </div>
          <button
            onClick={() => setShowUpload((s) => !s)}
            className="flex items-center gap-1 rounded bg-slate-900 px-3 py-2 text-sm text-white hover:bg-slate-700"
          >
            <Upload className="h-4 w-4" /> Upload New Version
          </button>
        </div>

        {showUpload && (
          <form onSubmit={handleUpload} className="mb-6 rounded border bg-white p-5 space-y-3">
            <h2 className="font-semibold text-slate-800">Upload New Version</h2>
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">Title <span className="text-red-500">*</span></label>
              <input
                type="text"
                value={uploadForm.title}
                onChange={(e) => setUploadForm({ ...uploadForm, title: e.target.value })}
                required
                className="w-full rounded border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">Description</label>
              <input
                type="text"
                value={uploadForm.description}
                onChange={(e) => setUploadForm({ ...uploadForm, description: e.target.value })}
                className="w-full rounded border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">File <span className="text-red-500">*</span></label>
              <input
                type="file"
                required
                onChange={(e) => setUploadForm({ ...uploadForm, file: e.target.files[0] })}
                className="text-sm"
              />
            </div>
            <div className="flex gap-2">
              <button type="button" onClick={() => setShowUpload(false)} className="rounded border px-4 py-2 text-sm text-slate-600">
                Cancel
              </button>
              <button type="submit" disabled={uploading} className="rounded bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-60">
                {uploading ? "Uploading…" : "Upload"}
              </button>
            </div>
          </form>
        )}

        {data?.current_version && (
          <div className="mb-4 rounded border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
            <strong>Current active version:</strong> v{data.current_version.version_number} — {data.current_version.title}
          </div>
        )}

        <div className="relative">
          <div className="absolute left-5 top-0 h-full w-px bg-slate-200" />
          <ul className="space-y-4 pl-12">
            {(data?.versions || []).slice().reverse().map((v) => (
              <li key={v.id} className="relative rounded border bg-white p-4 shadow-sm">
                <div className="absolute -left-8 top-4 flex h-6 w-6 items-center justify-center rounded-full border-2 border-white bg-slate-100">
                  {STATUS_ICON[v.status] || <Clock className="h-3 w-3 text-slate-400" />}
                </div>
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="rounded bg-slate-100 px-2 py-0.5 text-xs font-mono font-semibold text-slate-700">
                        v{v.version_number}
                      </span>
                      {v.id === data?.current_version?.id && (
                        <span className="rounded bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">
                          Current
                        </span>
                      )}
                      <span className={`rounded px-2 py-0.5 text-xs font-medium ${
                        v.status === "approved" ? "bg-emerald-100 text-emerald-700" :
                        v.status === "rejected" ? "bg-red-100 text-red-700" :
                        v.status === "archived" ? "bg-slate-100 text-slate-600" :
                        "bg-yellow-100 text-yellow-700"
                      }`}>{v.status}</span>
                    </div>
                    <p className="mt-1 font-medium text-slate-900">{v.title}</p>
                    <p className="text-xs text-slate-400">{new Date(v.created_at).toLocaleString()}</p>
                  </div>
                  {v.status === "archived" && (
                    <button
                      onClick={() => handleRollback(v.id)}
                      className="flex items-center gap-1 rounded border border-slate-300 px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-50"
                      title="Roll back to this version (Super Admin only)"
                    >
                      <RotateCcw className="h-3.5 w-3.5" /> Rollback
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>

        <p className="mt-6 text-center text-sm text-slate-400">
          {data?.total_versions ?? 0} version{data?.total_versions !== 1 ? "s" : ""} total
        </p>
      </div>
    </main>
  );
}
