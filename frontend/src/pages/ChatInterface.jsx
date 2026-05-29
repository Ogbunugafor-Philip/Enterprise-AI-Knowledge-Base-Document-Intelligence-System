import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { MessageSquarePlus, Send, ThumbsUp, ThumbsDown, AlertTriangle, Loader2, ChevronDown, ChevronUp } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import AppLayout from '../components/Layout/AppLayout.jsx';
import { chatApi } from '../services/chatApi.js';
import { formatDistanceToNow } from 'date-fns';

const mdComponents = {
  p:      ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
  strong: ({ children }) => <strong className="font-semibold text-gray-900">{children}</strong>,
  em:     ({ children }) => <em className="italic">{children}</em>,
  ul:     ({ children }) => <ul className="list-disc pl-4 mb-2 space-y-0.5">{children}</ul>,
  ol:     ({ children }) => <ol className="list-decimal pl-4 mb-2 space-y-0.5">{children}</ol>,
  li:     ({ children }) => <li className="leading-relaxed">{children}</li>,
  h1:     ({ children }) => <h1 className="text-base font-bold mb-1 mt-2">{children}</h1>,
  h2:     ({ children }) => <h2 className="text-sm font-bold mb-1 mt-2">{children}</h2>,
  h3:     ({ children }) => <h3 className="text-sm font-semibold mb-1 mt-1">{children}</h3>,
  code:   ({ children }) => <code className="bg-gray-100 rounded px-1 py-0.5 text-xs font-mono">{children}</code>,
};

function ConfidenceBar({ score }) {
  const pct = Math.round((score || 0) * 100);
  const color = pct > 75 ? 'bg-green-500' : pct > 50 ? 'bg-yellow-500' : 'bg-red-500';
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-200 rounded-full h-1.5">
        <div className={`h-1.5 rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-medium text-gray-600">{pct}%</span>
    </div>
  );
}

function ChatMessage({ msg, onFeedback }) {
  const [showSources, setShowSources] = useState(false);
  const isUser = msg.role === 'user';
  if (isUser) return (
    <div className="flex justify-end mb-4">
      <div className="max-w-2xl bg-blue-600 text-white rounded-2xl rounded-tr-sm px-5 py-3.5 shadow-sm">
        <p className="text-sm leading-relaxed">{msg.content}</p>
      </div>
    </div>
  );
  return (
    <div className="flex justify-start mb-4">
      <div className="max-w-3xl w-full">
        <div className="card px-5 py-4">
          {msg.response_rejected && (
            <div className="flex items-start gap-2 mb-3 p-3 bg-amber-50 border border-amber-200 rounded-xl">
              <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
              <p className="text-sm text-amber-800">Source evidence was not strong enough to provide a confident answer.</p>
            </div>
          )}
          <div className="text-sm text-gray-800 mb-3">
            <ReactMarkdown components={mdComponents}>{msg.content || msg.answer}</ReactMarkdown>
          </div>

          {msg.confidence_score !== undefined && (
            <div className="mb-3 space-y-1.5">
              <div className="flex items-center justify-between text-xs text-gray-500 font-medium">
                <span>Confidence</span>
                <span className={`badge ${msg.confidence_score > 0.75 ? 'badge-green' : msg.confidence_score > 0.5 ? 'badge-yellow' : 'badge-red'}`}>
                  {msg.hallucination_risk_score > 0.6 ? 'High Risk' : msg.hallucination_risk_score > 0.3 ? 'Medium Risk' : 'Low Risk'}
                </span>
              </div>
              <ConfidenceBar score={msg.confidence_score} />
            </div>
          )}

          {msg.source_documents?.length > 0 && (
            <div className="mb-3">
              <button onClick={() => setShowSources(v => !v)} className="flex items-center gap-1.5 text-xs font-medium text-blue-600 hover:text-blue-700">
                {showSources ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                {msg.source_documents.length} source{msg.source_documents.length !== 1 ? 's' : ''}
              </button>
              {showSources && (
                <div className="mt-2 space-y-1.5">
                  {msg.source_documents.map((src, i) => (
                    <div key={i} className="text-xs bg-gray-50 rounded-lg px-3 py-2 border border-gray-100">
                      <span className="font-medium text-gray-700">{src.document_title}</span>
                      {src.page_number && <span className="text-gray-400 ml-1.5">· p.{src.page_number}</span>}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          <div className="flex items-center gap-1 pt-2 border-t border-gray-50">
            {[['correct', <ThumbsUp key="u" className="w-3.5 h-3.5" />, 'Helpful'],
              ['incorrect', <ThumbsDown key="d" className="w-3.5 h-3.5" />, 'Not Helpful'],
              ['hallucination', <AlertTriangle key="a" className="w-3.5 h-3.5" />, 'Report']
            ].map(([type, icon, label]) => (
              <button key={type} onClick={() => onFeedback?.(msg.id, type)}
                className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 px-2 py-1 rounded hover:bg-gray-100 transition-colors">
                {icon}{label}
              </button>
            ))}
            {msg.created_at && (
              <span className="ml-auto text-xs text-gray-300">
                {formatDistanceToNow(new Date(msg.created_at), { addSuffix: true })}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex justify-start mb-4">
      <div className="card px-5 py-4">
        <div className="flex items-center gap-1.5">
          {[0,1,2].map(i => (
            <div key={i} className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
          ))}
          <span className="text-xs text-gray-400 ml-1.5">DocIntel is thinking…</span>
        </div>
      </div>
    </div>
  );
}

export default function ChatInterface() {
  const navigate = useNavigate();
  const { sessionId } = useParams();
  const [messages, setMessages] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessLoading, setSessLoading] = useState(true);
  const bottomRef = useRef(null);

  useEffect(() => {
    chatApi.getSessions({ limit: 30, offset: 0 }).then(r => {
      if (r.ok) setSessions(r.data.sessions || []);
      setSessLoading(false);
    });
  }, []);

  useEffect(() => {
    if (sessionId) chatApi.getSession(sessionId).then(r => r.ok && setMessages(r.data.messages || []));
    else setMessages([]);
  }, [sessionId]);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, loading]);

  const send = useCallback(async () => {
    if (!input.trim() || loading) return;
    const q = input.trim();
    setInput('');
    setLoading(true);
    const localId = `local-${Date.now()}`;
    setMessages(prev => [...prev, { id: localId, role: 'user', content: q }]);
    const res = await chatApi.askQuestion({ session_id: sessionId || null, question: q });
    if (res.ok) setMessages(prev => [...prev, { id: res.data.message_id, role: 'assistant', ...res.data }]);
    setLoading(false);
  }, [input, loading, sessionId]);

  async function handleFeedback(messageId, type) {
    await chatApi.submitFeedback({ message_id: messageId, feedback: type });
  }

  async function newChat() {
    const res = await chatApi.createSession({ title: 'New conversation' });
    if (res.ok) { navigate(`/chat/${res.data.id}`); setSessions(p => [res.data, ...p]); }
  }

  const sampleQs = ['What is our leave policy?', 'How do I submit an expense report?', 'What are IT security guidelines?'];

  return (
    <div className="flex h-screen bg-slate-100 overflow-hidden">
      {/* Sessions Sidebar */}
      <aside className="w-72 bg-white border-r border-gray-200 flex flex-col shadow-sm">
        <div className="p-4 border-b border-gray-100">
          <button onClick={newChat} className="w-full btn-primary justify-center">
            <MessageSquarePlus className="w-4 h-4" />New Chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          {sessLoading ? [1,2,3,4].map(i => <div key={i} className="h-10 bg-gray-100 rounded-lg animate-pulse" />) :
            sessions.map(s => (
              <button key={s.id} onClick={() => navigate(`/chat/${s.id}`)}
                className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition-colors truncate ${sessionId === s.id ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-600 hover:bg-gray-50'}`}>
                {s.title || 'Untitled conversation'}
              </button>
            ))
          }
        </div>
      </aside>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-14 bg-white border-b border-gray-200 flex items-center px-6">
          <h1 className="font-semibold text-gray-900">Knowledge Chat</h1>
        </header>

        <div className="flex-1 overflow-y-auto px-6 py-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center">
              <div className="w-16 h-16 rounded-2xl bg-blue-50 flex items-center justify-center mb-4">
                <MessageSquarePlus className="w-8 h-8 text-blue-500" />
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-1">Start a conversation</h3>
              <p className="text-gray-400 text-sm mb-6">Ask any question about your organization's documents</p>
              <div className="flex flex-wrap gap-2 justify-center max-w-lg">
                {sampleQs.map(q => (
                  <button key={q} onClick={() => setInput(q)}
                    className="text-sm px-3 py-1.5 rounded-full border border-blue-200 text-blue-600 hover:bg-blue-50 transition-colors">
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map(msg => <ChatMessage key={msg.id} msg={msg} onFeedback={handleFeedback} />)}
              {loading && <TypingIndicator />}
              <div ref={bottomRef} />
            </>
          )}
        </div>

        <div className="bg-white border-t border-gray-200 p-4">
          <div className="flex items-end gap-3 max-w-4xl mx-auto">
            <textarea
              className="input flex-1 resize-none max-h-32 py-3"
              rows={1}
              placeholder="Ask a question grounded in your documents…"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }}
            />
            <button onClick={send} disabled={!input.trim() || loading}
              className="btn-primary px-4 py-3 rounded-xl self-end">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </button>
          </div>
          <p className="text-center text-xs text-gray-400 mt-2">Enter to send · Shift+Enter for new line</p>
        </div>
      </div>
    </div>
  );
}
