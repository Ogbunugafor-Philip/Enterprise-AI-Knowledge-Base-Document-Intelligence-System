import React, { useState, useEffect } from "react";
import { X, UserPlus, Loader2 } from "lucide-react";
import { superAdminApi } from "../services/superAdminApi.js";

function extractError(err) {
  if (!err) return "";
  if (typeof err === "string") return err;
  if (Array.isArray(err)) return err.map((e) => (e.msg ? e.msg : String(e))).join(", ");
  if (err && typeof err === "object") {
    if (err.detail) return extractError(err.detail);
    return JSON.stringify(err);
  }
  return "Request failed. Please try again.";
}

function getStoredUser() {
  try {
    return JSON.parse(localStorage.getItem("ent_rag_user") || "{}");
  } catch {
    return {};
  }
}

export default function CreateUserModal({ onClose, onCreated }) {
  const storedUser = getStoredUser();

  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    organization_id: storedUser.organization_id || "",
    department_id: "",
    role_id: "",
    send_welcome_email: true,
  });
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(null);
  const [roles, setRoles] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      const [rolesRes, deptsRes] = await Promise.all([
        superAdminApi.getRoles(),
        superAdminApi.getDepartments(),
      ]);
      if (cancelled) return;
      if (rolesRes.ok) setRoles(Array.isArray(rolesRes.data) ? rolesRes.data : []);
      if (deptsRes.ok) setDepartments(Array.isArray(deptsRes.data) ? deptsRes.data : []);
      setLoading(false);
    }
    load();
    return () => { cancelled = true; };
  }, []);

  const validate = () => {
    const e = {};
    if (!form.first_name.trim()) e.first_name = "Required";
    if (!form.last_name.trim()) e.last_name = "Required";
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(form.email.trim())) e.email = "Valid email required";
    if (!form.organization_id) e.organization_id = "Organization not found — please re-login";
    if (!form.role_id) e.role_id = "Required";
    return e;
  };

  const handleSubmit = async (ev) => {
    ev.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }
    setErrors({});
    setSubmitting(true);
    const body = {
      first_name: form.first_name.trim(),
      last_name: form.last_name.trim(),
      email: form.email.trim(),
      organization_id: form.organization_id,
      role_id: form.role_id,
      send_welcome_email: form.send_welcome_email,
    };
    if (form.department_id) body.department_id = form.department_id;
    const res = await superAdminApi.createUser(body);
    if (res.ok) {
      setSuccess(res.data);
      if (onCreated) onCreated(res.data);
    } else {
      setErrors({ submit: extractError(res.error) });
    }
    setSubmitting(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-lg rounded-lg border border-slate-200 bg-white shadow-xl">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <h2 className="flex items-center gap-2 font-semibold text-slate-900">
            <UserPlus className="h-5 w-5" /> Create User
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700">
            <X className="h-5 w-5" />
          </button>
        </div>

        {success ? (
          <div className="px-5 py-6 text-center space-y-3">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100">
              <UserPlus className="h-6 w-6 text-emerald-600" />
            </div>
            <p className="font-semibold text-slate-900">User created successfully</p>
            <p className="text-sm text-slate-500">{success.email}</p>
            {form.send_welcome_email && (
              <p className="text-xs text-slate-400">Verification email and temporary password sent.</p>
            )}
            <button onClick={onClose} className="rounded bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-700">
              Done
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="px-5 py-4 space-y-3">
            {loading && (
              <div className="flex items-center gap-2 text-sm text-slate-500 pb-1">
                <Loader2 className="h-4 w-4 animate-spin" /> Loading options…
              </div>
            )}

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">
                  First Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={form.first_name}
                  onChange={(e) => setForm({ ...form, first_name: e.target.value })}
                  className={`w-full rounded border px-3 py-2 text-sm ${errors.first_name ? "border-red-400" : "border-slate-300"} focus:outline-none`}
                />
                {errors.first_name && <p className="mt-0.5 text-xs text-red-600">{errors.first_name}</p>}
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">
                  Last Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={form.last_name}
                  onChange={(e) => setForm({ ...form, last_name: e.target.value })}
                  className={`w-full rounded border px-3 py-2 text-sm ${errors.last_name ? "border-red-400" : "border-slate-300"} focus:outline-none`}
                />
                {errors.last_name && <p className="mt-0.5 text-xs text-red-600">{errors.last_name}</p>}
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">
                Email <span className="text-red-500">*</span>
              </label>
              <input
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className={`w-full rounded border px-3 py-2 text-sm ${errors.email ? "border-red-400" : "border-slate-300"} focus:outline-none`}
              />
              {errors.email && <p className="mt-0.5 text-xs text-red-600">{errors.email}</p>}
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">
                Role <span className="text-red-500">*</span>
              </label>
              <select
                value={form.role_id}
                onChange={(e) => setForm({ ...form, role_id: e.target.value })}
                disabled={loading}
                className={`w-full rounded border px-3 py-2 text-sm bg-white ${errors.role_id ? "border-red-400" : "border-slate-300"} focus:outline-none disabled:opacity-60`}
              >
                <option value="">— Select role —</option>
                {roles.map((r) => (
                  <option key={r.id} value={r.id}>{r.name}</option>
                ))}
              </select>
              {errors.role_id && <p className="mt-0.5 text-xs text-red-600">{errors.role_id}</p>}
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">Department</label>
              <select
                value={form.department_id}
                onChange={(e) => setForm({ ...form, department_id: e.target.value })}
                disabled={loading}
                className="w-full rounded border border-slate-300 px-3 py-2 text-sm bg-white focus:outline-none disabled:opacity-60"
              >
                <option value="">— None —</option>
                {departments.map((d) => (
                  <option key={d.id} value={d.id}>{d.name}</option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-2">
              <input
                id="welcome-email"
                type="checkbox"
                checked={form.send_welcome_email}
                onChange={(e) => setForm({ ...form, send_welcome_email: e.target.checked })}
                className="h-4 w-4"
              />
              <label htmlFor="welcome-email" className="text-sm text-slate-600">
                Send welcome email with OTP and temporary password
              </label>
            </div>

            {errors.organization_id && (
              <p className="rounded bg-yellow-50 px-3 py-2 text-sm text-yellow-700">{errors.organization_id}</p>
            )}
            {errors.submit && (
              <p className="rounded bg-red-50 px-3 py-2 text-sm text-red-700">{errors.submit}</p>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="rounded border px-4 py-2 text-sm text-slate-600 hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting || loading}
                className="rounded bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-60"
              >
                {submitting ? "Creating…" : "Create User"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
