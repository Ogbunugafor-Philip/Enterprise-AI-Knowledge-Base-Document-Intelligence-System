import React, { useRef, useState } from "react";
import { X, Upload, Download, FileSpreadsheet, AlertCircle, CheckCircle } from "lucide-react";
import { superAdminApi } from "../services/superAdminApi.js";

export default function BulkUploadModal({ onClose, onComplete }) {
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [fileError, setFileError] = useState("");

  const ACCEPTED = [".xlsx", ".xls"];

  const validateFile = (f) => {
    if (!f) return false;
    const ext = f.name.toLowerCase().slice(f.name.lastIndexOf("."));
    if (!ACCEPTED.includes(ext)) { setFileError("Only .xlsx and .xls files are accepted."); return false; }
    setFileError("");
    return true;
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f && validateFile(f)) setFile(f);
  };

  const handleFileInput = (e) => {
    const f = e.target.files[0];
    if (f && validateFile(f)) setFile(f);
  };

  const handleDownloadTemplate = async () => {
    const res = await superAdminApi.downloadBulkTemplate();
    if (res.ok && res.blob) {
      const url = URL.createObjectURL(res.blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "bulk_user_template.xlsx";
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    const res = await superAdminApi.bulkUploadUsers(formData);
    if (res.ok) {
      setResult(res.data);
      if (onComplete) onComplete(res.data);
    } else {
      setFileError(res.error || "Upload failed");
    }
    setUploading(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-2xl rounded-lg border border-slate-200 bg-white shadow-xl">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <h2 className="flex items-center gap-2 font-semibold text-slate-900">
            <FileSpreadsheet className="h-5 w-5" /> Bulk Upload Users
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700"><X className="h-5 w-5" /></button>
        </div>

        <div className="px-5 py-4 space-y-4">
          {/* Template download */}
          <div className="flex items-center justify-between rounded border border-dashed border-slate-300 bg-slate-50 px-4 py-3">
            <p className="text-sm text-slate-600">Download the Excel template with correct column headers</p>
            <button onClick={handleDownloadTemplate} className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-white">
              <Download className="h-4 w-4" /> Template
            </button>
          </div>

          {!result && (
            <>
              {/* Drop zone */}
              <div
                onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                onDragLeave={() => setDragging(false)}
                onDrop={handleDrop}
                onClick={() => inputRef.current?.click()}
                className={`cursor-pointer rounded border-2 border-dashed p-8 text-center transition ${
                  dragging ? "border-slate-500 bg-slate-100" : "border-slate-300 hover:border-slate-400"
                }`}
              >
                <Upload className="mx-auto mb-2 h-8 w-8 text-slate-400" />
                {file ? (
                  <p className="font-medium text-slate-700">{file.name}</p>
                ) : (
                  <p className="text-sm text-slate-500">Drop an Excel file here, or click to browse</p>
                )}
                <p className="mt-1 text-xs text-slate-400">Accepted: .xlsx, .xls</p>
                <input ref={inputRef} type="file" accept=".xlsx,.xls" onChange={handleFileInput} className="hidden" />
              </div>
              {fileError && (
                <p className="flex items-center gap-1 text-sm text-red-600">
                  <AlertCircle className="h-4 w-4" /> {fileError}
                </p>
              )}

              <div className="flex justify-end gap-2">
                <button onClick={onClose} className="rounded border px-4 py-2 text-sm text-slate-600 hover:bg-slate-50">Cancel</button>
                <button
                  onClick={handleUpload}
                  disabled={!file || uploading}
                  className="rounded bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-60"
                >
                  {uploading ? "Uploading…" : "Upload"}
                </button>
              </div>
            </>
          )}

          {/* Results */}
          {result && (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-3 text-center">
                <div className="rounded border bg-slate-50 p-3">
                  <div className="text-xl font-semibold">{result.total_rows}</div>
                  <div className="text-xs text-slate-500">Total Rows</div>
                </div>
                <div className="rounded border bg-emerald-50 p-3">
                  <div className="text-xl font-semibold text-emerald-700">{result.successfully_created}</div>
                  <div className="text-xs text-emerald-600">Created</div>
                </div>
                <div className="rounded border bg-red-50 p-3">
                  <div className="text-xl font-semibold text-red-700">{result.failed_rows}</div>
                  <div className="text-xs text-red-600">Failed</div>
                </div>
              </div>

              {result.errors.length > 0 && (
                <div>
                  <h3 className="mb-2 text-sm font-semibold text-slate-700">Errors</h3>
                  <div className="max-h-48 overflow-y-auto rounded border bg-red-50">
                    <table className="w-full text-xs">
                      <thead className="border-b bg-red-100">
                        <tr>
                          <th className="px-3 py-2 text-left">Row</th>
                          <th className="px-3 py-2 text-left">Email</th>
                          <th className="px-3 py-2 text-left">Error</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-red-100">
                        {result.errors.map((err, i) => (
                          <tr key={i}>
                            <td className="px-3 py-1.5">{err.row_number}</td>
                            <td className="px-3 py-1.5">{err.email || "—"}</td>
                            <td className="px-3 py-1.5 text-red-700">{err.error_reason}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {result.successfully_created > 0 && (
                <div className="flex items-center gap-2 rounded bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
                  <CheckCircle className="h-4 w-4" />
                  {result.successfully_created} user{result.successfully_created !== 1 ? "s" : ""} created with welcome emails sent.
                </div>
              )}

              <div className="flex justify-end">
                <button onClick={onClose} className="rounded bg-slate-900 px-4 py-2 text-sm text-white">Done</button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
