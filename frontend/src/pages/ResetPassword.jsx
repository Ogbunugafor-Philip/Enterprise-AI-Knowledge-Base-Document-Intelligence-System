import React, { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { ShieldCheck, Lock, Eye, EyeOff, Loader2, CheckCircle, XCircle } from 'lucide-react';
import API_BASE_URL from '../config/api.js';

const STRENGTH_RULES = [
  { label: 'At least 8 characters', test: p => p.length >= 8 },
  { label: 'Uppercase letter',       test: p => /[A-Z]/.test(p) },
  { label: 'Lowercase letter',       test: p => /[a-z]/.test(p) },
  { label: 'Number',                 test: p => /\d/.test(p) },
  { label: 'Special character',      test: p => /[^A-Za-z0-9]/.test(p) },
];

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token') || '';

  const [password, setPassword]   = useState('');
  const [confirm, setConfirm]     = useState('');
  const [showPw, setShowPw]       = useState(false);
  const [showCf, setShowCf]       = useState(false);
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState('');
  const [success, setSuccess]     = useState(false);
  const [tokenBad, setTokenBad]   = useState(!token);

  const allRulesPassed = STRENGTH_RULES.every(r => r.test(password));
  const passwordsMatch = password === confirm && confirm.length > 0;

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');

    if (!allRulesPassed) {
      setError('Password does not meet strength requirements.');
      return;
    }
    if (!passwordsMatch) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/auth/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reset_token: token, new_password: password, confirm_password: confirm }),
      });
      const data = await res.json();
      if (res.ok) {
        setSuccess(true);
        setTimeout(() => navigate('/login', { state: { message: 'Password reset successful. Please log in.' } }), 2500);
      } else if (res.status === 400 && data.detail?.toLowerCase().includes('expired')) {
        setTokenBad(true);
      } else {
        setError(data.detail || 'Something went wrong. Please try again.');
      }
    } catch {
      setError('Cannot reach the server. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  if (tokenBad) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
        <div className="w-full max-w-sm bg-white rounded-2xl border border-slate-200 shadow-sm p-8 text-center">
          <div className="w-14 h-14 rounded-full bg-red-50 border border-red-100 flex items-center justify-center mx-auto mb-4">
            <XCircle className="w-7 h-7 text-red-600" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Link invalid or expired</h2>
          <p className="text-sm text-gray-500 mb-6">
            This reset link is invalid or has expired. Please request a new one.
          </p>
          <Link to="/forgot-password" className="btn-primary inline-flex justify-center px-6 py-2.5 text-sm">
            Request new link
          </Link>
        </div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
        <div className="w-full max-w-sm bg-white rounded-2xl border border-slate-200 shadow-sm p-8 text-center">
          <div className="w-14 h-14 rounded-full bg-green-50 border border-green-100 flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-7 h-7 text-green-600" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Password reset</h2>
          <p className="text-sm text-gray-500">Redirecting you to sign in…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
      <div className="w-full max-w-sm">
        <div className="flex items-center gap-3 mb-8 justify-center">
          <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center shadow-lg">
            <ShieldCheck className="w-6 h-6 text-white" />
          </div>
          <span className="text-xl font-bold text-gray-900">DocIntel</span>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-8">
          <div className="mb-6">
            <h2 className="text-xl font-bold text-gray-900">Set new password</h2>
            <p className="text-sm text-gray-500 mt-1">Choose a strong password for your account.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label" htmlFor="password">New password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  id="password"
                  type={showPw ? 'text' : 'password'}
                  required
                  autoComplete="new-password"
                  className="input pl-10 pr-10"
                  placeholder="••••••••"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                />
                <button type="button" onClick={() => setShowPw(v => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {password.length > 0 && (
              <ul className="space-y-1">
                {STRENGTH_RULES.map(({ label, test }) => (
                  <li key={label} className={`flex items-center gap-2 text-xs ${test(password) ? 'text-green-600' : 'text-gray-400'}`}>
                    {test(password)
                      ? <CheckCircle className="w-3.5 h-3.5 shrink-0" />
                      : <XCircle className="w-3.5 h-3.5 shrink-0" />}
                    {label}
                  </li>
                ))}
              </ul>
            )}

            <div>
              <label className="label" htmlFor="confirm">Confirm password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  id="confirm"
                  type={showCf ? 'text' : 'password'}
                  required
                  autoComplete="new-password"
                  className="input pl-10 pr-10"
                  placeholder="••••••••"
                  value={confirm}
                  onChange={e => setConfirm(e.target.value)}
                />
                <button type="button" onClick={() => setShowCf(v => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                  {showCf ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {confirm.length > 0 && !passwordsMatch && (
                <p className="mt-1 text-xs text-red-600">Passwords do not match</p>
              )}
            </div>

            {error && (
              <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading || !allRulesPassed || !passwordsMatch}
              className="btn-primary w-full justify-center py-2.5 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? <><Loader2 className="w-4 h-4 animate-spin" />Resetting…</> : 'Reset password'}
            </button>
          </form>

          <p className="mt-5 text-center text-sm text-gray-500">
            <Link to="/login" className="text-blue-600 hover:text-blue-700 font-medium">← Back to sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
