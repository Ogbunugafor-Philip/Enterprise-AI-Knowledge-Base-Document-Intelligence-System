import React, { useState } from "react";
import { UploadCloud } from "lucide-react";
import { adminApi } from "../services/adminApi.js";

export default function DocumentUploadModal({ open, onClose, onUploaded }) {
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState(null);

  if (!open) return null;

  const upload = async () => {
    if (!file) return setError("Select a file first.");
    setStatus("uploading");
    setError(null);
    const form = new FormData();
    form.append("file", file);
    form.append("title", title || file.name);
    form.append("description", description);
    if (departmentId) form.append("department_id", departmentId);
    const res = await adminApi.uploadDocument(form);
    if (!res.ok) {
      setStatus("error");
      setError(Array.isArray(res.error) ? res.error.join(", ") : res.error);
      return;
    }
    setStatus("success");
    onUploaded?.(res.data);
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/50 p-4">
      <div className="mx-auto mt-16 max-w-xl rounded bg-white p-6 shadow-xl">
        <h2 className="text-lg font-semibold">Upload document</h2>
        <div className="mt-4 rounded border border-dashed border-slate-300 p-6 text-center" onDrop={(e) => { e.preventDefault(); setFile(e.dataTransfer.files[0]); }} onDragOver={(e) => e.preventDefault()}>
          <UploadCloud className="mx-auto h-8 w-8 text-slate-500" />
          <p className="mt-2 text-sm text-slate-600">Drag and drop a file or choose one below.</p>
          <p className="mt-1 text-xs text-slate-500">PDF, DOCX, TXT, Excel, Images. 50MB maximum.</p>
          <input className="mt-4 text-sm" type="file" onChange={(e) => setFile(e.target.files?.[0])} />
          {file && <p className="mt-2 text-sm font-medium">{file.name}</p>}
        </div>
        <div className="mt-4 grid gap-3">
          <input className="rounded border px-3 py-2 text-sm" placeholder="Document title" value={title} onChange={(e) => setTitle(e.target.value)} />
          <textarea className="rounded border px-3 py-2 text-sm" placeholder="Description" value={description} onChange={(e) => setDescription(e.target.value)} />
          <select className="rounded border px-3 py-2 text-sm" value={departmentId} onChange={(e) => setDepartmentId(e.target.value)}>
            <option value="">General department</option>
          </select>
        </div>
        {status === "uploading" && <div className="mt-4 h-2 rounded bg-slate-100"><div className="h-2 w-2/3 rounded bg-blue-600" /></div>}
        {status === "success" && <p className="mt-3 text-sm text-emerald-700">Upload queued for processing.</p>}
        {error && <p className="mt-3 rounded bg-red-50 p-3 text-sm text-red-700">{error}</p>}
        <div className="mt-5 flex justify-end gap-2">
          <button className="rounded border px-3 py-2 text-sm" onClick={onClose}>Close</button>
          <button className="rounded bg-slate-900 px-3 py-2 text-sm text-white" onClick={upload}>Upload</button>
        </div>
      </div>
    </div>
  );
}
