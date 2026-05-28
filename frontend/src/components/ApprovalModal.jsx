import React, { useState } from "react";
import { CheckCircle, XCircle, FileText, X } from "lucide-react";

export default function ApprovalModal({ document, onApprove, onReject, onClose }) {
  const [rejecting, setRejecting] = useState(false);
  const [reason, setReason] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState("");

  const handleApprove = async () => {
    setLoading(true);
    setError("");
    try {
      await onApprove(document.id);
      setSuccess("Document approved successfully.");
    } catch {
      setError("Failed to approve document.");
    }
    setLoading(false);
  };

  const handleReject = async () => {
    if (reason.trim().length < 20) {
      setError("Rejection reason must be at least 20 characters.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await onReject(document.id, reason.trim());
      setSuccess("Document rejected.");
    } catch {
      setError("Failed to reject document.");
    }
    setLoading(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-lg rounded-lg border border-slate-200 bg-white shadow-xl">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <h2 className="font-semibold text-slate-900">Review Document</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="px-5 py-4 space-y-3">
          <div className="flex items-start gap-3 rounded border border-slate-100 bg-slate-50 p-3">
            <FileText className="mt-0.5 h-5 w-5 shrink-0 text-slate-500" />
            <div className="space-y-1 text-sm">
              <p className="font-medium text-slate-900">{document.title}</p>
              <p className="text-slate-500">
                {document.file_name} &middot; {document.file_type?.toUpperCase()} &middot;{" "}
                {document.file_size_mb} MB
              </p>
              {document.department_id && (
                <p className="text-slate-500">Department: {document.department_id}</p>
              )}
              <p className="text-slate-500">Uploaded by: {document.uploaded_by}</p>
              <p className="text-slate-500">
                Uploaded: {new Date(document.created_at).toLocaleString()}
              </p>
              <span
                className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${
                  document.status === "approved"
                    ? "bg-emerald-100 text-emerald-700"
                    : document.status === "rejected"
                    ? "bg-red-100 text-red-700"
                    : "bg-yellow-100 text-yellow-700"
                }`}
              >
                {document.status}
              </span>
            </div>
          </div>

          {success && (
            <p className="rounded bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{success}</p>
          )}
          {error && (
            <p className="rounded bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
          )}

          {rejecting ? (
            <div className="space-y-2">
              <label className="block text-sm font-medium text-slate-700">
                Rejection reason <span className="text-red-500">*</span>
              </label>
              <textarea
                rows={3}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Explain why this document is being rejected (min 20 characters)"
                className="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
              />
              <p className="text-xs text-slate-400">{reason.length} / 20 characters minimum</p>
            </div>
          ) : null}
        </div>

        {!success && (
          <div className="flex justify-end gap-2 border-t px-5 py-4">
            {rejecting ? (
              <>
                <button
                  onClick={() => { setRejecting(false); setError(""); setReason(""); }}
                  className="rounded border px-4 py-2 text-sm text-slate-600 hover:bg-slate-50"
                  disabled={loading}
                >
                  Cancel
                </button>
                <button
                  onClick={handleReject}
                  disabled={loading}
                  className="flex items-center gap-1 rounded bg-red-600 px-4 py-2 text-sm text-white hover:bg-red-700 disabled:opacity-60"
                >
                  <XCircle className="h-4 w-4" />
                  Confirm Rejection
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => setRejecting(true)}
                  className="flex items-center gap-1 rounded border border-red-300 px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                >
                  <XCircle className="h-4 w-4" />
                  Reject
                </button>
                <button
                  onClick={handleApprove}
                  disabled={loading}
                  className="flex items-center gap-1 rounded bg-emerald-600 px-4 py-2 text-sm text-white hover:bg-emerald-700 disabled:opacity-60"
                >
                  <CheckCircle className="h-4 w-4" />
                  {loading ? "Approving…" : "Approve"}
                </button>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
