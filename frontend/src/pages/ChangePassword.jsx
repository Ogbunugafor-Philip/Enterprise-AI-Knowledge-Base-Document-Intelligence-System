import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, Eye, EyeOff, Loader2, ShieldCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext.jsx';
import API_BASE_URL from '../config/api.js';

function roleDefaultRoute(role) {
  if (role === 'SUPER_ADMIN') return '/superadmin/dashboard';
  if (role === 'ADMIN') return '/admin/dashboard';
  return '/dashboard';
}

export default function ChangePassword() {
  const { user, token, updateUser } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({ current_password: '', new_password: '', confirm_password: '' });
  const [show, setShow] = useState({ current: false, new_pw: false, confirm: false });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  if (!token) {
    navigate('/login', { replace: true });
    return null;
  }

  const fields = [
    { key: 'current_password',  label: 'Current password',      showKey: 'current' },
    { key: 'new_password',      label: 'New password',          showKey: 'new_pw'  },
    { key: 'confirm_password',  label: 'Confirm new password',  showKey: 'confirm' },
  ];

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    if (form.new_password !== form.confirm_password) {
      setError('New passwords do not match.');
      return;
    }
    if (form.new_password.length < 8) {
      setError('New password must be at least 8 characters.');
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/auth/change-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(form),
      });
      const data = await res.json();
      if (res.ok) {
        updateUser({ must_change_password: false, is_first_login: false });
        setSuccess(true);
        setTimeout(() => navigate(roleDefaultRoute(user?.role), { replace: true }), 1500);
      } else {
        const detail = data.detail;
        if (Array.isArray(detail)) {
          setError(detail.map(d => d.msg || String(d)).join(', '));
        } else {
          setError(detail || 'Failed to change password.');
        }
      }
    } catch {
      setError('Cannot reach the server. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-xl border border-slate-100 p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center shadow-md">
              <ShieldCheck className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900">Set a New Password</h1>
              <p className="text-sm text-slate-500">You must change your password before continuing</p>
            </div>
          </div>

          {success ? (
            <div className="rounded-lg bg-emerald-50 border border-emerald-200 px-4 py-3 text-emerald-700 text-sm text-center">
              Password changed successfully! Redirecting to your dashboard…
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              {fields.map(({ key, label, showKey }) => (
                <div key={key}>
                  <label className="block text-sm font-medium text-slate-700 mb-1">{label}</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input
                      type={show[showKey] ? 'text' : 'password'}
                      required
                      className="input pl-10 pr-10 w-full"
                      value={form[key]}
                      onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
                      placeholder="••••••••"
                    />
                    <button
                      type="button"
                      onClick={() => setShow(s => ({ ...s, [showKey]: !s[showKey] }))}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                    >
                      {show[showKey] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
              ))}

              {error && (
                <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="btn-primary w-full justify-center py-2.5 text-base"
              >
                {loading
                  ? <><Loader2 className="w-4 h-4 animate-spin mr-2 inline" />Changing…</>
                  : 'Set New Password'
                }
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
