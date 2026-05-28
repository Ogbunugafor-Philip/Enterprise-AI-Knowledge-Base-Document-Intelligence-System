import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { HelpCircle, History, MessageSquarePlus } from "lucide-react";
import OnboardingTour from "../components/OnboardingTour.jsx";
import { chatApi } from "../services/chatApi.js";

export default function UserDashboard() {
  const [stats, setStats] = useState({ total_questions_asked: 0, total_sessions_created: 0, most_active_day: null });
  const [sessions, setSessions] = useState([]);
  const [showTour, setShowTour] = useState(false);
  const firstName = localStorage.getItem("first_name") || "User";

  useEffect(() => {
    chatApi.getUserStats().then((res) => res.ok && setStats(res.data));
    chatApi.getSessions({ limit: 5, offset: 0 }).then((res) => res.ok && setSessions(res.data.sessions || []));
    chatApi.getOnboardingStatus().then((res) => setShowTour(res.ok && !res.data.is_completed));
  }, []);

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-6 text-slate-950">
      {showTour && <OnboardingTour onComplete={() => setShowTour(false)} />}
      <div className="mx-auto max-w-6xl">
        <header className="flex flex-col gap-4 border-b border-slate-200 pb-5 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Welcome, {firstName}</h1>
            <p className="mt-1 text-sm text-slate-600">Ask questions grounded in approved organization documents.</p>
          </div>
          <nav className="flex flex-wrap gap-2">
            <Link className="inline-flex items-center gap-2 rounded bg-slate-900 px-3 py-2 text-sm text-white" to="/chat"><MessageSquarePlus className="h-4 w-4" />New Chat</Link>
            <Link className="inline-flex items-center gap-2 rounded border px-3 py-2 text-sm" to="/history"><History className="h-4 w-4" />Chat History</Link>
            <Link className="inline-flex items-center gap-2 rounded border px-3 py-2 text-sm" to="/help"><HelpCircle className="h-4 w-4" />Help</Link>
          </nav>
        </header>

        {showTour && (
          <section className="mt-5 rounded border border-amber-300 bg-amber-50 p-4">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm text-amber-900">Complete the guided tour to learn how source-backed answers and feedback work.</p>
              <button className="rounded bg-amber-900 px-3 py-2 text-sm text-white" onClick={() => setShowTour(true)}>Start Tour</button>
            </div>
          </section>
        )}

        <section className="mt-6 grid gap-4 md:grid-cols-3">
          <div className="rounded border border-slate-200 bg-white p-4"><div className="text-sm text-slate-500">Questions asked</div><div className="mt-2 text-2xl font-semibold">{stats.total_questions_asked}</div></div>
          <div className="rounded border border-slate-200 bg-white p-4"><div className="text-sm text-slate-500">Sessions created</div><div className="mt-2 text-2xl font-semibold">{stats.total_sessions_created}</div></div>
          <div className="rounded border border-slate-200 bg-white p-4"><div className="text-sm text-slate-500">Last active</div><div className="mt-2 text-2xl font-semibold">{stats.most_active_day || "Today"}</div></div>
        </section>

        <section className="mt-6 grid gap-5 lg:grid-cols-[1fr_360px]">
          <div className="rounded border border-slate-200 bg-white p-4">
            <h2 className="font-semibold">Quick ask</h2>
            <div className="mt-3 flex gap-2">
              <input className="min-w-0 flex-1 rounded border border-slate-300 px-3 py-2 text-sm" placeholder="Ask about approved documents..." />
              <Link className="rounded bg-slate-900 px-4 py-2 text-sm text-white" to="/chat">Ask</Link>
            </div>
          </div>
          <div className="rounded border border-slate-200 bg-white p-4">
            <h2 className="font-semibold">Recent sessions</h2>
            <div className="mt-3 space-y-2">
              {sessions.length === 0 && <p className="text-sm text-slate-500">No recent sessions.</p>}
              {sessions.map((session) => (
                <Link key={session.id} className="block rounded border border-slate-200 px-3 py-2 text-sm hover:border-slate-400" to={`/chat/${session.id}`}>
                  <div className="font-medium">{session.title}</div>
                  <div className="text-xs text-slate-500">{new Date(session.updated_at).toLocaleString()}</div>
                </Link>
              ))}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
