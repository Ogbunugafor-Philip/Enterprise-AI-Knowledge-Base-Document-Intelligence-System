import React, { useEffect, useState } from "react";
import { complianceApi } from "../services/complianceApi.js";

export default function DataRetentionSettings() {
  const [settings, setSettings] = useState({
    chat_retention_days: 365,
    document_retention_days: 2555,
    monitoring_log_retention_days: 90,
    audit_log_retention_days: 2555,
  });
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState("");

  useEffect(() => {
    complianceApi.getRetentionSettings().then((res) => res.ok && setSettings(res.data));
  }, []);

  const save = async () => {
    setSaving(true);
    const payload = Object.fromEntries(Object.entries(settings).map(([key, value]) => [key, Number(value)]));
    const res = await complianceApi.updateRetentionSettings(payload);
    if (res.ok) {
      setSettings(res.data);
      setToast("Retention settings saved.");
      setTimeout(() => setToast(""), 3000);
    }
    setSaving(false);
  };

  const field = (key, label) => (
    <label className="block">
      <span className="text-sm font-medium text-slate-700">{label}</span>
      <input
        type="number"
        min="1"
        className="mt-1 w-full rounded border px-3 py-2 text-sm"
        value={settings[key]}
        onChange={(e) => setSettings({ ...settings, [key]: e.target.value })}
      />
    </label>
  );

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-6">
      <div className="mx-auto max-w-3xl">
        <header className="mb-6 border-b pb-5">
          <h1 className="text-2xl font-semibold">Data Retention Settings</h1>
          <p className="text-sm text-slate-500">Configure compliance retention windows.</p>
        </header>

        <section className="rounded border border-orange-200 bg-orange-50 p-4 text-sm text-orange-800">
          Data older than the configured retention period may be permanently deleted by scheduled cleanup jobs. Documents are archived by default unless explicit deletion is configured server-side.
        </section>

        <section className="mt-5 grid gap-4 rounded border bg-white p-5 md:grid-cols-2">
          {field("chat_retention_days", "Chat history retention days")}
          {field("document_retention_days", "Document retention days")}
          {field("monitoring_log_retention_days", "Monitoring log retention days")}
          {field("audit_log_retention_days", "Audit log retention days")}
        </section>

        <div className="mt-5 flex items-center gap-3">
          <button onClick={save} disabled={saving} className="rounded bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-50">
            {saving ? "Saving..." : "Save Settings"}
          </button>
          {toast && <span className="text-sm text-emerald-700">{toast}</span>}
        </div>
      </div>
    </main>
  );
}
