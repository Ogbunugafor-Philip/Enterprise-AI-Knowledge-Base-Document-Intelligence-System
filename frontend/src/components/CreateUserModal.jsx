import React, { useState } from "react";
import { X, UserPlus } from "lucide-react";
import { superAdminApi } from "../services/superAdminApi.js";

const ROLE_OPTIONS = ["USER", "ADMIN", "SUPER_ADMIN"];

export default function CreateUserModal({ onClose, onCreated }) {
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    organization_id: "",
    department_id: "",
    role_id: "",
    send_welcome_email: true,
  });
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(null);

  const validate = () => {
    const e = {};
    if (!form.first_name.trim()) e.first_name = "Required";
    if (!form.last_name.trim()) e.last_name = "Required";
    if (!form.email.trim() || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(form.email)) e.email = "Valid email required";
    if (!form.organization_id.trim()) e.organization_id = "Required";
    return e;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }
    setErrors({});
    setSubmitting(true);
    const body = {
      first_name: form.first_name.trim(),
      last_name: form.last_name.trim(),
      email: form.email.trim(),
      organization_id: form.organization_id.trim(),
      send_welcome_email: form.send_welcome_email,
    };
    if (form.department_id.trim()) body.department_id = form.department_id.trim();
    if (form.role_id.trim()) body.role_id = form.role_id.trim();
    const res = await superAdminApi.createUser(body);
    if (res.ok) {
      setSuccess(res.data);
      if (onCreated) onCreated(res.data);
    } else {
      setErrors({ submit: res.error || "Failed to create user" });
    }
    setSubmitting(false);
  };

  const field = (key, label, type = "text", required = false) => (
    <div>
      <label className="block text-xs font-medium text-slate-600 mb-1">
        {label} {required && <span className="text-red-500">*</span>}
      </label>
      <input
        type={type}
        value={form[key]}
        onChange={(e) => setForm({ ...form, [key]: e.target.value })}
        className={`w-full rounded border px-3 py-2 text-sm ${errors[key] ? "border-red-400" : "border-slate-300"} focus:outline-none`}
      />
      {errors[key] && <p className="mt-0.5 text-xs text-red-600">{errors[key]}</p>}
    </div>
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-lg rounded-lg border border-slate-200 bg-white shadow-xl">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <h2 className="flex items-center gap-2 font-semibold text-slate-900">
            <UserPlus className="h-5 w-5" /> Create User
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700"><X className="h-5 w-5" /></button>
        </div>

        {success ? (
          <div className="px-5 py-6 text-center space-y-3">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100">
              <UserPlus className="h-6 w-6 text-emerald-600" />
            </div>
            <p className="font-semibold text-slate-900">User created successfully</p>
            <p className="text-sm text-slate-500">{success.email}</p>
            <p className="text-xs text-slate-400">Verification email and temporary password sent.</p>
            <button onClick={onClose} className="rounded bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-700">
              Done
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="px-5 py-4 space-y-3">
            <div className="grid grid-cols-2 gap-3">
              {field("first_name", "First Name", "text", true)}
              {field("last_name", "Last Name", "text", true)}
            </div>
            {field("email", "Email", "email", true)}
            {field("organization_id", "Organization ID (UUID)", "text", true)}
            {field("department_id", "Department ID (UUID, optional)")}
            {field("role_id", "Role ID (UUID, optional)")}

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

            {errors.submit && <p className="rounded bg-red-50 px-3 py-2 text-sm text-red-700">{errors.submit}</p>}

            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={onClose} className="rounded border px-4 py-2 text-sm text-slate-600 hover:bg-slate-50">
                Cancel
              </button>
              <button type="submit" disabled={submitting} className="rounded bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-60">
                {submitting ? "Creating…" : "Create User"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
