import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { ShieldCheck, Mail, Lock, Eye, EyeOff, Loader2, FileText, Brain, Users, BarChart3 } from 'lucide-react';
import { useAuth } from '../context/AuthContext.jsx';
import API_BASE_URL from '../config/api.js';

function roleDefaultRoute(role) {
  if (role === 'SUPER_ADMIN') return '/superadmin/dashboard';
  if (role === 'ADMIN') return '/admin/dashboard';
  return '/dashboard';
}

const features = [
  { icon: FileText, label: 'Document Intelligence', desc: 'AI-powered analysis of enterprise documents' },
  { icon: Brain, label: 'RAG Pipeline', desc: 'Retrieval-augmented generation with confidence scoring' },
  { icon: Users, label: 'Multi-Tenant RBAC', desc: 'Enterprise-grade role-based access control' },
  { icon: BarChart3, label: 'Compliance Ready', desc: 'Full audit logs, GDPR export, data retention' },
];

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from?.pathname;

  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw]     = useState(false);
  const [remember, setRemember] = useState(false);
  const [otp, setOtp]           = useState('');
  const [step, setStep]         = useState('login');
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState('');

  async function handleLogin(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (res.ok) {
        const userData = { ...data.user, must_change_password: data.must_change_password };
        login(data.access_token, userData);
        if (data.must_change_password) {
          navigate('/change-password', { replace: true });
        } else {
          navigate(from || roleDefaultRoute(data.user?.role), { replace: true });
        }
      } else if (res.status === 403 && data.detail?.toLowerCase().includes('otp')) {
        setStep('otp');
      } else {
        setError(data.detail || 'Invalid email or password.');
      }
    } catch {
      setError('Cannot reach the server. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  async function handleOtp(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/auth/verify-otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, otp_code: otp }),
      });
      if (res.ok) {
        const loginRes = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password }),
        });
        const loginData = await loginRes.json();
        if (loginRes.ok) {
          const userData = { ...loginData.user, must_change_password: loginData.must_change_password };
          login(loginData.access_token, userData);
          if (loginData.must_change_password) {
            navigate('/change-password', { replace: true });
          } else {
            navigate(from || roleDefaultRoute(loginData.user?.role), { replace: true });
          }
        } else {
          setError(loginData.detail || 'Login failed after OTP verification.');
          setStep('login');
        }
      } else {
        const d = await res.json();
        setError(d.detail || 'Invalid or expired OTP.');
      }
    } catch {
      setError('Cannot reach the server. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex">
      {/* Left Panel */}
      <div className="hidden lg:flex flex-col justify-between w-[60%] bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 p-12 relative overflow-hidden">
        {/* Background decoration */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 -right-40 w-96 h-96 rounded-full bg-blue-600/10 blur-3xl" />
          <div className="absolute -bottom-40 -left-40 w-96 h-96 rounded-full bg-indigo-600/10 blur-3xl" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 rounded-full bg-blue-500/5 blur-2xl" />
        </div>

        <div className="relative">
          <div className="flex items-center gap-3 mb-16">
            <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center shadow-lg">
              <ShieldCheck className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="text-white font-bold text-xl">DocIntel</div>
              <div className="text-blue-300 text-xs">Enterprise AI Knowledge Base</div>
            </div>
          </div>

          <h1 className="text-4xl font-bold text-white leading-tight mb-4">
            Intelligent Document<br />
            <span className="text-blue-400">Knowledge Platform</span>
          </h1>
          <p className="text-slate-300 text-lg leading-relaxed max-w-md">
            Transform your enterprise documents into a searchable, AI-powered knowledge base with enterprise-grade security and compliance.
          </p>
        </div>

        <div className="relative grid grid-cols-2 gap-4">
          {features.map(({ icon: Icon, label, desc }) => (
            <div key={label} className="bg-white/5 backdrop-blur-sm rounded-xl p-4 border border-white/10">
              <div className="w-8 h-8 rounded-lg bg-blue-600/20 flex items-center justify-center mb-3">
                <Icon className="w-4 h-4 text-blue-400" />
              </div>
              <div className="text-white text-sm font-semibold mb-1">{label}</div>
              <div className="text-slate-400 text-xs leading-relaxed">{desc}</div>
            </div>
          ))}
        </div>

        <div className="relative text-slate-500 text-xs">
          © 2025 DocIntel Enterprise AI · All rights reserved
        </div>
      </div>

      {/* Right Panel */}
      <div className="flex-1 flex flex-col items-center justify-center bg-white p-8 lg:p-12">
        {/* Mobile logo */}
        <div className="lg:hidden flex items-center gap-3 mb-10">
          <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center">
            <ShieldCheck className="w-6 h-6 text-white" />
          </div>
          <span className="text-xl font-bold text-gray-900">DocIntel</span>
        </div>

        <div className="w-full max-w-sm">
          {step === 'login' ? (
            <>
              <div className="mb-8">
                <h2 className="text-2xl font-bold text-gray-900">Welcome back</h2>
                <p className="text-gray-500 mt-1 text-sm">Sign in to your enterprise knowledge base</p>
              </div>

              <form onSubmit={handleLogin} className="space-y-5">
                <div>
                  <label className="label" htmlFor="email">Email address</label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input id="email" type="email" required autoComplete="email" className="input pl-10"
                      placeholder="you@company.com" value={email} onChange={e => setEmail(e.target.value)} />
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="label m-0" htmlFor="password">Password</label>
                    <a href="/forgot-password" className="text-xs text-blue-600 hover:text-blue-700 font-medium">Forgot password?</a>
                  </div>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input id="password" type={showPw ? 'text' : 'password'} required autoComplete="current-password"
                      className="input pl-10 pr-10" placeholder="••••••••"
                      value={password} onChange={e => setPassword(e.target.value)} />
                    <button type="button" onClick={() => setShowPw(v => !v)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                      {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <label className="flex items-center gap-2.5 cursor-pointer">
                  <input type="checkbox" className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    checked={remember} onChange={e => setRemember(e.target.checked)} />
                  <span className="text-sm text-gray-600">Remember me for 30 days</span>
                </label>

                {error && (
                  <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
                )}

                <button type="submit" disabled={loading} className="btn-primary w-full justify-center py-2.5 text-base">
                  {loading ? <><Loader2 className="w-4 h-4 animate-spin" />Signing in…</> : 'Sign in'}
                </button>
              </form>
            </>
          ) : (
            <>
              <div className="mb-8">
                <h2 className="text-2xl font-bold text-gray-900">Verify your account</h2>
                <p className="text-gray-500 mt-1 text-sm">
                  A verification code was sent to <strong className="text-gray-700">{email}</strong>
                </p>
              </div>
              <form onSubmit={handleOtp} className="space-y-5">
                <div>
                  <label className="label">One-time code</label>
                  <input type="text" inputMode="numeric" maxLength={6} required
                    className="input text-center text-2xl tracking-[0.5em] font-mono"
                    placeholder="_ _ _ _ _ _"
                    value={otp} onChange={e => setOtp(e.target.value.replace(/\D/g, ''))} />
                </div>
                {error && <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
                <button type="submit" disabled={loading || otp.length < 6} className="btn-primary w-full justify-center py-2.5">
                  {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Verify & Sign in'}
                </button>
                <button type="button" onClick={() => { setStep('login'); setError(''); setOtp(''); }}
                  className="w-full text-sm text-gray-500 hover:text-gray-700 text-center">
                  ← Back to sign in
                </button>
              </form>
            </>
          )}

          <p className="mt-8 text-center text-xs text-gray-400">
            DocIntel Enterprise AI Knowledge Base · Secure Sign In
          </p>
        </div>
      </div>
    </div>
  );
}
