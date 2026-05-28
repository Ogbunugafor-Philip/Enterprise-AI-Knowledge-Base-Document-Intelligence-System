import React, { useEffect, useState } from "react";
import { Plus, Trash2, Shield } from "lucide-react";
import { adminApi } from "../services/adminApi.js";

const ACCESS_TYPE_LABELS = {
  organization: "Organization-wide",
  department: "Department",
  role: "Role",
  user: "Specific User",
};

export default function AccessRuleManager({ documentId }) {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    access_type: "organization",
    department_id: "",
    role_id: "",
    user_id: "",
  });
  const [formError, setFormError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const fetchRules = async () => {
    setLoading(true);
    const res = await adminApi.getAccessRules(documentId);
    if (res.ok) setRules(res.data);
    else setError("Failed to load access rules.");
    setLoading(false);
  };

  useEffect(() => { fetchRules(); }, [documentId]);

  const handleAdd = async () => {
    setFormError("");
    const payload = { document_id: documentId, access_type: form.access_type };
    if (form.access_type === "department") {
      if (!form.department_id.trim()) { setFormError("Department ID is required."); return; }
      payload.department_id = form.department_id.trim();
    }
    if (form.access_type === "role") {
      if (!form.role_id.trim()) { setFormError("Role ID is required."); return; }
      payload.role_id = form.role_id.trim();
    }
    if (form.access_type === "user") {
      if (!form.user_id.trim()) { setFormError("User ID is required."); return; }
      payload.user_id = form.user_id.trim();
    }
    setSubmitting(true);
    const res = await adminApi.createAccessRule(documentId, payload);
    if (res.ok) {
      setRules((prev) => [...prev, res.data]);
      setShowForm(false);
      setForm({ access_type: "organization", department_id: "", role_id: "", user_id: "" });
    } else {
      setFormError(res.error || "Failed to create rule.");
    }
    setSubmitting(false);
  };

  const handleDelete = async (ruleId) => {
    const res = await adminApi.deleteAccessRule(documentId, ruleId);
    if (res.ok || res.status === 204) {
      setRules((prev) => prev.filter((r) => r.id !== ruleId));
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="flex items-center gap-2 font-semibold text-slate-800">
          <Shield className="h-4 w-4 text-slate-500" />
          Access Rules
        </h3>
        <button
          onClick={() => setShowForm((s) => !s)}
          className="flex items-center gap-1 rounded border px-3 py-1.5 text-sm hover:bg-slate-50"
        >
          <Plus className="h-4 w-4" />
          Add Rule
        </button>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {showForm && (
        <div className="rounded border border-slate-200 bg-slate-50 p-4 space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Access Type</label>
            <select
              value={form.access_type}
              onChange={(e) => setForm({ ...form, access_type: e.target.value })}
              className="w-full rounded border border-slate-300 px-3 py-2 text-sm"
            >
              {Object.entries(ACCESS_TYPE_LABELS).map(([val, label]) => (
                <option key={val} value={val}>{label}</option>
              ))}
            </select>
          </div>
          {form.access_type === "department" && (
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">Department ID</label>
              <input
                type="text"
                value={form.department_id}
                onChange={(e) => setForm({ ...form, department_id: e.target.value })}
                placeholder="UUID"
                className="w-full rounded border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
          )}
          {form.access_type === "role" && (
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">Role ID</label>
              <input
                type="text"
                value={form.role_id}
                onChange={(e) => setForm({ ...form, role_id: e.target.value })}
                placeholder="UUID"
                className="w-full rounded border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
          )}
          {form.access_type === "user" && (
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">User ID</label>
              <input
                type="text"
                value={form.user_id}
                onChange={(e) => setForm({ ...form, user_id: e.target.value })}
                placeholder="UUID"
                className="w-full rounded border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
          )}
          {formError && <p className="text-xs text-red-600">{formError}</p>}
          <div className="flex gap-2">
            <button
              onClick={() => { setShowForm(false); setFormError(""); }}
              className="rounded border px-3 py-1.5 text-sm text-slate-600 hover:bg-white"
            >
              Cancel
            </button>
            <button
              onClick={handleAdd}
              disabled={submitting}
              className="rounded bg-slate-900 px-3 py-1.5 text-sm text-white hover:bg-slate-700 disabled:opacity-60"
            >
              {submitting ? "Saving…" : "Add Rule"}
            </button>
          </div>
        </div>
      )}

      {loading ? (
        <p className="text-sm text-slate-500">Loading rules…</p>
      ) : rules.length === 0 ? (
        <p className="rounded border border-dashed border-slate-300 p-4 text-center text-sm text-slate-400">
          No access rules configured. Default: all users in the organization can access approved documents.
        </p>
      ) : (
        <ul className="divide-y divide-slate-100 rounded border border-slate-200 bg-white">
          {rules.map((rule) => (
            <li key={rule.id} className="flex items-center justify-between px-4 py-3 text-sm">
              <div>
                <span className="font-medium text-slate-800">
                  {ACCESS_TYPE_LABELS[rule.access_type] || rule.access_type}
                </span>
                {rule.department_id && (
                  <span className="ml-2 text-slate-500">Dept: {rule.department_id}</span>
                )}
                {rule.role_id && (
                  <span className="ml-2 text-slate-500">Role: {rule.role_id}</span>
                )}
                {rule.user_id && (
                  <span className="ml-2 text-slate-500">User: {rule.user_id}</span>
                )}
                <span className="ml-2 text-xs text-slate-400">
                  granted {new Date(rule.granted_at).toLocaleDateString()}
                </span>
              </div>
              <button
                onClick={() => handleDelete(rule.id)}
                className="text-slate-400 hover:text-red-500"
                title="Remove rule"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
