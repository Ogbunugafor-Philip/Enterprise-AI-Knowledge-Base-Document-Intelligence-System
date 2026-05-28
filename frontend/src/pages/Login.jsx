import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Loader2, Lock, Mail } from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";
import { API_BASE_URL } from "../config/environment.js";

function roleDefaultRoute(role) {
  if (role === "SUPER_ADMIN") return "/superadmin/dashboard";
  if (role === "ADMIN") return "/admin/dashboard";
  return "/dashboard";
}

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [step, setStep] = useState("login"); // "login" | "otp"
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const from = location.state?.from?.pathname || null;

  async function handleLogin(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (res.ok) {
        login(data.access_token, data.user);
        const dest = from || roleDefaultRoute(data.user?.role);
        navigate(dest, { replace: true });
      } else if (res.status === 403 && data.detail?.toLowerCase().includes("otp")) {
        setStep("otp");
      } else if (res.status === 403 && data.detail?.toLowerCase().includes("locked")) {
        setError("Account is temporarily locked. Please try again later.");
      } else {
        setError(data.detail || "Invalid email or password.");
      }
    } catch {
      setError("Cannot reach the server. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  async function handleOtp(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/auth/verify-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, otp_code: otp }),
      });
      const data = await res.json();
      if (res.ok) {
        // OTP verified — now log in properly
        const loginRes = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        });
        const loginData = await loginRes.json();
        if (loginRes.ok) {
          login(loginData.access_token, loginData.user);
          const dest = from || roleDefaultRoute(loginData.user?.role);
          navigate(dest, { replace: true });
        } else {
          setError(loginData.detail || "Login failed after OTP verification.");
          setStep("login");
        }
      } else {
        setError(data.detail || "Invalid or expired OTP.");
      }
    } catch {
      setError("Cannot reach the server. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-sm">
        {/* Logo / Brand */}
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-slate-900">
            <Lock className="h-6 w-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">DocIntel</h1>
          <p className="mt-1 text-sm text-slate-500">Enterprise AI Knowledge Base</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
          {step === "login" ? (
            <>
              <h2 className="mb-6 text-lg font-semibold text-slate-900">Sign in to your account</h2>
              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-slate-700" htmlFor="email">
                    Email address
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                    <input
                      id="email"
                      type="email"
                      required
                      autoComplete="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full rounded-lg border border-slate-300 py-2.5 pl-10 pr-3 text-sm text-slate-900 placeholder-slate-400 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
                      placeholder="you@company.com"
                    />
                  </div>
                </div>

                <div>
                  <div className="mb-1.5 flex items-center justify-between">
                    <label className="text-sm font-medium text-slate-700" htmlFor="password">
                      Password
                    </label>
                    <a href="/forgot-password" className="text-xs text-slate-500 hover:text-slate-800">
                      Forgot password?
                    </a>
                  </div>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                    <input
                      id="password"
                      type="password"
                      required
                      autoComplete="current-password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full rounded-lg border border-slate-300 py-2.5 pl-10 pr-3 text-sm text-slate-900 placeholder-slate-400 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
                      placeholder="••••••••"
                    />
                  </div>
                </div>

                {error && (
                  <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                    {error}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="flex w-full items-center justify-center gap-2 rounded-lg bg-slate-900 py-2.5 text-sm font-medium text-white transition hover:bg-slate-700 disabled:opacity-60"
                >
                  {loading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Signing in…
                    </>
                  ) : (
                    "Sign in"
                  )}
                </button>
              </form>
            </>
          ) : (
            <>
              <h2 className="mb-2 text-lg font-semibold text-slate-900">Verify your account</h2>
              <p className="mb-6 text-sm text-slate-500">
                A one-time code was sent to <strong>{email}</strong>. Enter it below to continue.
              </p>
              <form onSubmit={handleOtp} className="space-y-4">
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-slate-700" htmlFor="otp">
                    One-time code
                  </label>
                  <input
                    id="otp"
                    type="text"
                    inputMode="numeric"
                    maxLength={6}
                    required
                    value={otp}
                    onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
                    className="w-full rounded-lg border border-slate-300 py-2.5 px-3 text-center text-xl tracking-[0.5em] text-slate-900 focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
                    placeholder="______"
                  />
                </div>

                {error && (
                  <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                    {error}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading || otp.length < 6}
                  className="flex w-full items-center justify-center gap-2 rounded-lg bg-slate-900 py-2.5 text-sm font-medium text-white transition hover:bg-slate-700 disabled:opacity-60"
                >
                  {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Verify & Sign in"}
                </button>

                <button
                  type="button"
                  onClick={() => { setStep("login"); setError(""); setOtp(""); }}
                  className="w-full text-sm text-slate-500 hover:text-slate-800"
                >
                  ← Back to sign in
                </button>
              </form>
            </>
          )}
        </div>

        <p className="mt-6 text-center text-xs text-slate-400">
          DocIntel — Enterprise AI Knowledge Base &amp; Document Intelligence
        </p>
      </div>
    </div>
  );
}
