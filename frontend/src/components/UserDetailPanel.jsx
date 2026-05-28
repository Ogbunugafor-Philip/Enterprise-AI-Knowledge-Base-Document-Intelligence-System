import React, { useState } from "react";
import {
  X, User, Shield, Lock, MailWarning, KeyRound,
  CheckCircle, XCircle, Edit2, Trash2, RotateCcw, Unlock
} from "lucide-react";
import { superAdminApi } from "../services/superAdminApi.js";

function Badge({ label, color }) {
  const colors = {
    green: "bg-emerald-100 text-emerald-700",
    red: "bg-red-100 text-red-700",
    yellow: "bg-yellow-100 text-yellow-700",
    gray: "bg-slate-100 text-slate-600",
  };
  return <span className={`rounded px-2 py-0.5 text-xs font-medium ${colors[color] || colors.gray}`}>{label}</span>;
}

function InfoRow({ label, value }) {
  return (
    <div className="flex items-start justify-between py-1.5 text-sm">
      <span className="text-slate-500 w-40 shrink-0">{label}</span>
      <span className="text-slate-900 text-right">{value ?? "—"}</span>
    </div>
  );
}

export default function UserDetailPanel({ user, onClose, onRefresh }) {
  const [loading, setLoading] = useState("");
  const [toast, setToast] = useState("");

  const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(""), 3000); };

  const act = async (action, label) => {
    setLoading(label);
    let res;
    switch (action) {
      case "activate": res = await superAdminApi.activateUser(user.id); break;
      case "deactivate": res = await superAdminApi.deactivateUser(user.id, { user_id: user.id, is_active: false, reason: "Deactivated by super admin" }); break;
      case "reset": res = await superAdminApi.resetUserPassword(user.id, { user_id: user.id, force_change_on_login: true }); break;
      case "unlock": res = await superAdminApi.unlockUser(user.id); break;
      case "delete":
        if (!window.confirm("Permanently soft-delete this user?")) { setLoading(""); return; }
        res = await superAdminApi.deleteUser(user.id);
        break;
      default: setLoading(""); return;
    }
    if (res.ok) { showToast(`${label} successful.`); if (onRefresh) onRefresh(); }
    else showToast(`${label} failed: ${res.error}`);
    setLoading("");
  };

  const now = new Date();
  const pwChangedAt = user.password_changed_at ? new Date(user.password_changed_at) : null;
  const daysSincePwChange = pwChangedAt ? Math.floor((now - pwChangedAt) / 86400000) : null;
  const isLocked = user.locked_until && new Date(user.locked_until) > now;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-end bg-black/30">
      {toast && (
        <div className="fixed top-4 right-4 z-60 rounded bg-slate-900 px-4 py-2 text-sm text-white shadow">
          {toast}
        </div>
      )}
      <div className="h-full w-full max-w-md overflow-y-auto border-l border-slate-200 bg-white shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b px-5 py-4">
          <h2 className="flex items-center gap-2 font-semibold text-slate-900">
            <User className="h-5 w-5" /> User Details
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700"><X className="h-5 w-5" /></button>
        </div>

        <div className="px-5 py-4 space-y-5">
          {/* Identity */}
          <div>
            <p className="text-lg font-semibold text-slate-900">{user.first_name} {user.last_name}</p>
            <p className="text-sm text-slate-500">{user.email}</p>
            <div className="mt-2 flex flex-wrap gap-1">
              {user.is_active ? <Badge label="Active" color="green" /> : <Badge label="Inactive" color="gray" />}
              {user.is_verified ? <Badge label="Verified" color="green" /> : <Badge label="Unverified" color="yellow" />}
              {isLocked && <Badge label="Locked" color="red" />}
              {user.must_change_password && <Badge label="Must Change Password" color="yellow" />}
              {user.role && <Badge label={user.role} color="gray" />}
            </div>
          </div>

          {/* Account info */}
          <div className="divide-y divide-slate-100 rounded border bg-slate-50 px-4 py-1">
            <InfoRow label="Organization" value={user.organization_id} />
            <InfoRow label="Department" value={user.department_id} />
            <InfoRow label="Last Login" value={user.last_login ? new Date(user.last_login).toLocaleString() : "Never"} />
            <InfoRow label="Failed Attempts" value={user.failed_login_attempts} />
            <InfoRow label="Locked Until" value={user.locked_until ? new Date(user.locked_until).toLocaleString() : "—"} />
            <InfoRow label="Created" value={new Date(user.created_at).toLocaleDateString()} />
          </div>

          {/* Password status */}
          <div className="rounded border bg-yellow-50 px-4 py-3 space-y-1 text-sm">
            <div className="flex items-center gap-2 font-medium text-yellow-800">
              <KeyRound className="h-4 w-4" /> Password Status
            </div>
            <InfoRow
              label="Last changed"
              value={pwChangedAt ? `${daysSincePwChange} day(s) ago` : "Never"}
            />
            {daysSincePwChange !== null && daysSincePwChange >= 25 && (
              <p className="text-xs text-yellow-700">Warning: password expires in {30 - daysSincePwChange} day(s)</p>
            )}
            <InfoRow label="Must change on login" value={user.must_change_password ? "Yes" : "No"} />
          </div>

          {/* Actions */}
          <div className="grid grid-cols-2 gap-2">
            {user.is_active ? (
              <button onClick={() => act("deactivate", "Deactivate")} disabled={!!loading} className="flex items-center justify-center gap-1 rounded border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-60">
                <XCircle className="h-4 w-4" /> Deactivate
              </button>
            ) : (
              <button onClick={() => act("activate", "Activate")} disabled={!!loading} className="flex items-center justify-center gap-1 rounded border border-emerald-300 px-3 py-2 text-sm text-emerald-700 hover:bg-emerald-50 disabled:opacity-60">
                <CheckCircle className="h-4 w-4" /> Activate
              </button>
            )}
            <button onClick={() => act("reset", "Reset Password")} disabled={!!loading} className="flex items-center justify-center gap-1 rounded border border-blue-300 px-3 py-2 text-sm text-blue-700 hover:bg-blue-50 disabled:opacity-60">
              <RotateCcw className="h-4 w-4" /> Reset Password
            </button>
            {isLocked && (
              <button onClick={() => act("unlock", "Unlock")} disabled={!!loading} className="flex items-center justify-center gap-1 rounded border border-yellow-300 px-3 py-2 text-sm text-yellow-700 hover:bg-yellow-50 disabled:opacity-60">
                <Unlock className="h-4 w-4" /> Unlock
              </button>
            )}
            <button onClick={() => act("delete", "Delete")} disabled={!!loading} className="flex items-center justify-center gap-1 rounded border border-red-300 px-3 py-2 text-sm text-red-600 hover:bg-red-50 disabled:opacity-60">
              <Trash2 className="h-4 w-4" /> Delete
            </button>
          </div>

          {loading && (
            <p className="text-center text-sm text-slate-500">{loading}…</p>
          )}
        </div>
      </div>
    </div>
  );
}
