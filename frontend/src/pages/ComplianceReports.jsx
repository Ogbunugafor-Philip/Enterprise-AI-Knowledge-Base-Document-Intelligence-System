import React, { useEffect, useState } from "react";
import { Download } from "lucide-react";
import { complianceApi } from "../services/complianceApi.js";

export default function ComplianceReports() {
  const [form, setForm] = useState({ report_type: "activity", format: "pdf", date_from: "", date_to: "" });
  const [loading, setLoading] = useState(false);
  const [recent, setRecent] = useState([]);
  const [preview, setPreview] = useState(null);

  const previewReport = async () => {
    const params = {};
    if (form.date_from) params.date_from = form.date_from;
    if (form.date_to) params.date_to = form.date_to;
    const res = form.report_type === "security"
      ? await complianceApi.getSecurityReport(params)
      : await complianceApi.getActivityReport(params);
    if (res.ok) setPreview(res.data);
  };

  useEffect(() => { previewReport(); }, [form.report_type]);

  const generate = async () => {
    setLoading(true);
    const body = Object.fromEntries(Object.entries(form).filter(([, v]) => v !== ""));
    const res = await complianceApi.generateReport(body);
    if (res.ok) {
      const ext = form.format === "csv" ? "csv" : "pdf";
      const name = `${form.report_type}_compliance_report.${ext}`;
      const url = URL.createObjectURL(res.blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = name;
      a.click();
      URL.revokeObjectURL(url);
      setRecent((items) => [{ name, generated_at: new Date().toISOString(), blob: res.blob }, ...items].slice(0, 8));
    }
    setLoading(false);
  };

  const downloadRecent = (item) => {
    const url = URL.createObjectURL(item.blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = item.name;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-6">
      <div className="mx-auto max-w-6xl">
        <header className="mb-6 border-b pb-5">
          <h1 className="text-2xl font-semibold">Compliance Reports</h1>
          <p className="text-sm text-slate-500">Generate activity, access, document, and security reports.</p>
        </header>

        <section className="grid gap-4 rounded border bg-white p-4 md:grid-cols-5">
          <select className="rounded border px-3 py-2 text-sm" value={form.report_type} onChange={(e) => setForm({ ...form, report_type: e.target.value })}>
            <option value="activity">Activity</option>
            <option value="access">Access</option>
            <option value="document">Document</option>
            <option value="security">Security</option>
          </select>
          <input type="date" className="rounded border px-3 py-2 text-sm" value={form.date_from} onChange={(e) => setForm({ ...form, date_from: e.target.value })} />
          <input type="date" className="rounded border px-3 py-2 text-sm" value={form.date_to} onChange={(e) => setForm({ ...form, date_to: e.target.value })} />
          <select className="rounded border px-3 py-2 text-sm" value={form.format} onChange={(e) => setForm({ ...form, format: e.target.value })}>
            <option value="pdf">PDF</option>
            <option value="csv">CSV</option>
          </select>
          <button onClick={generate} disabled={loading} className="rounded bg-slate-900 px-3 py-2 text-sm text-white disabled:opacity-50">
            {loading ? "Generating..." : "Generate Report"}
          </button>
        </section>

        <section className="mt-6 grid gap-6 lg:grid-cols-2">
          <div className="rounded border bg-white p-4">
            <h2 className="mb-3 font-semibold">Recent Reports</h2>
            {recent.length === 0 ? <p className="text-sm text-slate-400">No reports generated in this session.</p> : (
              <ul className="divide-y">
                {recent.map((item) => (
                  <li key={`${item.name}-${item.generated_at}`} className="flex items-center justify-between py-3 text-sm">
                    <div>
                      <p className="font-medium">{item.name}</p>
                      <p className="text-xs text-slate-400">{new Date(item.generated_at).toLocaleString()}</p>
                    </div>
                    <button onClick={() => downloadRecent(item)} className="inline-flex items-center gap-1 rounded border px-2 py-1 text-xs">
                      <Download className="h-3 w-3" /> Download
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
          <div className="rounded border bg-white p-4">
            <h2 className="mb-3 font-semibold">Report Preview</h2>
            <pre className="max-h-96 overflow-auto rounded bg-slate-50 p-3 text-xs">{preview ? JSON.stringify(preview, null, 2) : "No preview available."}</pre>
          </div>
        </section>
      </div>
    </main>
  );
}
