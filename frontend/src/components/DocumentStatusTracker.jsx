import React from "react";

const stages = ["Uploaded", "Malware Scan", "Text Extraction", "Chunking", "Embedding", "Complete"];

export default function DocumentStatusTracker({ status, errorMessage, onRetry }) {
  const current = status?.progress_percent ? Math.floor((status.progress_percent / 100) * (stages.length - 1)) : 0;
  return (
    <section className="rounded border border-slate-200 bg-white p-4">
      <h2 className="font-semibold">Processing status</h2>
      <div className="mt-4 grid gap-2">
        {stages.map((stage, index) => (
          <div key={stage} className={`rounded px-3 py-2 text-sm ${index === current ? "bg-yellow-100 text-yellow-900" : index < current ? "bg-emerald-100 text-emerald-800" : "bg-slate-100 text-slate-600"}`}>
            {stage}
          </div>
        ))}
      </div>
      <p className="mt-3 text-sm text-slate-600">Estimated completion: {status?.progress_percent >= 90 ? "soon" : "processing"}</p>
      {errorMessage && <div className="mt-3 rounded bg-red-50 p-3 text-sm text-red-700">{errorMessage}<button className="ml-3 underline" onClick={onRetry}>Retry</button></div>}
    </section>
  );
}
