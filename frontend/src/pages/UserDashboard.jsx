import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MessageSquarePlus, TrendingUp, Clock, FileText, Zap } from 'lucide-react';
import AppLayout from '../components/Layout/AppLayout.jsx';
import StatsCard from '../components/UI/StatsCard.jsx';
import { chatApi } from '../services/chatApi.js';
import { useAuth } from '../context/AuthContext.jsx';
import { formatDistanceToNow } from 'date-fns';

function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 17) return 'Good afternoon';
  return 'Good evening';
}

export default function UserDashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [stats, setStats] = useState({ total_questions_asked: 0, total_sessions_created: 0 });
  const [sessions, setSessions] = useState([]);
  const [quickQ, setQuickQ] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([chatApi.getUserStats(), chatApi.getSessions({ limit: 6, offset: 0 })])
      .then(([s, sess]) => {
        if (s.ok) setStats(s.data);
        if (sess.ok) setSessions(sess.data.sessions || []);
      }).finally(() => setLoading(false));
  }, []);

  async function handleQuickAsk(e) {
    e.preventDefault();
    if (!quickQ.trim()) return;
    const res = await chatApi.createSession({ title: quickQ.slice(0, 60) });
    navigate(res.ok ? `/chat/${res.data.id}` : '/chat');
  }

  return (
    <AppLayout title={`${getGreeting()}, ${user?.first_name || 'User'}`} subtitle="Your activity overview">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
        <StatsCard title="Questions Asked"  value={stats.total_questions_asked}  icon={MessageSquarePlus} color="blue" />
        <StatsCard title="Sessions Created" value={stats.total_sessions_created} icon={Clock}            color="green" />
        <StatsCard title="Avg Confidence"   value="88%"                          icon={TrendingUp}       color="purple" subtitle="Last 30 days" />
        <StatsCard title="Docs Available"   value="—"                            icon={FileText}         color="yellow" subtitle="Approved in your org" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="card p-6">
            <h2 className="section-title flex items-center gap-2"><Zap className="w-5 h-5 text-blue-500" />Ask a Question</h2>
            <form onSubmit={handleQuickAsk}>
              <textarea className="input resize-none mb-3" rows={3}
                placeholder="What does our leave policy say about sick days?"
                value={quickQ} onChange={e => setQuickQ(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleQuickAsk(e); }} />
              <div className="flex items-center justify-between">
                <p className="text-xs text-gray-400">Ctrl+Enter to submit</p>
                <button type="submit" className="btn-primary" disabled={!quickQ.trim()}>Ask Question</button>
              </div>
            </form>
          </div>

          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="section-title m-0">Recent Conversations</h2>
              <button onClick={() => navigate('/history')} className="text-sm text-blue-600 font-medium">View all</button>
            </div>
            {loading ? (
              <div className="space-y-3">{[1,2,3].map(i => <div key={i} className="h-12 bg-gray-100 rounded-xl animate-pulse" />)}</div>
            ) : sessions.length === 0 ? (
              <p className="text-sm text-gray-400 py-4 text-center">No conversations yet — start by asking a question</p>
            ) : sessions.map(s => (
              <button key={s.id} onClick={() => navigate(`/chat/${s.id}`)}
                className="w-full text-left py-3 hover:bg-gray-50 px-2 -mx-2 rounded-lg transition-colors">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-medium text-gray-800 truncate">{s.title || 'Untitled'}</span>
                  <span className="text-xs text-gray-400 shrink-0">
                    {s.created_at ? formatDistanceToNow(new Date(s.created_at), { addSuffix: true }) : ''}
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-4">
          <div className="card p-6">
            <h2 className="section-title">Quick Actions</h2>
            <div className="space-y-2">
              <button onClick={() => navigate('/chat')} className="w-full btn-primary justify-center"><MessageSquarePlus className="w-4 h-4" />New Chat</button>
              <button onClick={() => navigate('/history')} className="w-full btn-secondary justify-center"><Clock className="w-4 h-4" />Chat History</button>
            </div>
          </div>
          <div className="card p-6">
            <h2 className="section-title">Try Asking</h2>
            {['What is our leave policy?', 'How do I submit expenses?', 'IT security guidelines?', 'How do I request time off?'].map(q => (
              <button key={q} onClick={() => setQuickQ(q)}
                className="w-full text-left text-xs text-gray-600 hover:text-blue-600 py-2 px-2 rounded hover:bg-blue-50 transition-colors border-b border-gray-50 last:border-0">
                "{q}"
              </button>
            ))}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
