import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Loader2, MessageSquarePlus } from "lucide-react";
import SampleQuestions from "../components/SampleQuestions.jsx";
import { chatApi } from "../services/chatApi.js";

function confidenceClass(score) {
  if (score > 0.8) return "bg-emerald-100 text-emerald-800";
  if (score >= 0.5) return "bg-yellow-100 text-yellow-800";
  return "bg-red-100 text-red-800";
}

export default function ChatInterface() {
  const { sessionId } = useParams();
  const [messages, setMessages] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    chatApi.getSessions({ limit: 20, offset: 0 }).then((res) => res.ok && setSessions(res.data.sessions || []));
  }, []);

  useEffect(() => {
    if (sessionId) {
      chatApi.getSession(sessionId).then((res) => res.ok && setMessages(res.data.messages || []));
    }
  }, [sessionId]);

  const send = async () => {
    if (!input.trim()) return;
    setLoading(true);
    const question = input;
    setInput("");
    setMessages((prev) => [...prev, { id: `local-${Date.now()}`, role: "user", content: question }]);
    const res = await chatApi.askQuestion({ session_id: sessionId || null, question });
    if (res.ok) {
      setMessages((prev) => [...prev, { id: res.data.message_id, role: "assistant", content: res.data.answer, ...res.data }]);
    }
    setLoading(false);
  };

  return (
    <main className="grid min-h-screen bg-slate-50 text-slate-950 lg:grid-cols-[280px_1fr_300px]">
      <aside className="border-r border-slate-200 bg-white p-4">
        <Link to="/chat" className="mb-4 inline-flex items-center gap-2 rounded bg-slate-900 px-3 py-2 text-sm text-white"><MessageSquarePlus className="h-4 w-4" />New Chat</Link>
        <div className="space-y-2">
          {sessions.map((session) => (
            <Link key={session.id} className="block rounded border border-slate-200 px-3 py-2 text-sm hover:border-slate-400" to={`/chat/${session.id}`}>
              {session.title}
            </Link>
          ))}
        </div>
      </aside>
      <section className="flex min-h-screen flex-col">
        <header className="border-b border-slate-200 bg-white px-5 py-4">
          <h1 className="font-semibold">Knowledge chat</h1>
        </header>
        <div className="flex-1 space-y-4 overflow-y-auto p-5">
          {messages.length === 0 && <div className="rounded border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">Ask a question to begin.</div>}
          {messages.map((message) => (
            <article key={message.id} className={`rounded border p-4 ${message.role === "user" ? "ml-auto max-w-2xl bg-slate-900 text-white" : "max-w-3xl bg-white"}`}>
              {message.response_rejected && <div className="mb-3 rounded border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">Safe fallback: source evidence was not strong enough.</div>}
              <p className="text-sm leading-6">{message.content || message.answer}</p>
              {message.role === "assistant" && (
                <div className="mt-4 space-y-3 text-sm">
                  <div className="flex flex-wrap gap-2">
                    <span className={`rounded px-2 py-1 ${confidenceClass(message.confidence_score || 0)}`}>Confidence {Math.round((message.confidence_score || 0) * 100)}%</span>
                    <span className="rounded bg-slate-100 px-2 py-1">Retrieval {Math.round((message.retrieval_score || 0) * 100)}%</span>
                    <span className="rounded bg-slate-100 px-2 py-1">Risk {(message.hallucination_risk_score || 0) > 0.7 ? "high" : (message.hallucination_risk_score || 0) > 0.4 ? "medium" : "low"}</span>
                  </div>
                  {(message.source_documents || []).map((source, index) => (
                    <div key={`${source.document_id}-${index}`} className="rounded border border-slate-200 p-2">
                      {source.document_title} {source.page_number ? `page ${source.page_number}` : ""}
                    </div>
                  ))}
                  <div className="flex flex-wrap gap-2">
                    {["Correct", "Incorrect", "Unclear", "Report Hallucination"].map((label) => <button key={label} className="rounded border px-2 py-1 text-xs">{label}</button>)}
                  </div>
                </div>
              )}
            </article>
          ))}
          {loading && <div className="flex items-center gap-2 text-sm text-slate-500"><Loader2 className="h-4 w-4 animate-spin" />Generating response...</div>}
        </div>
        <footer className="border-t border-slate-200 bg-white p-4">
          <div className="flex gap-2">
            <input className="min-w-0 flex-1 rounded border border-slate-300 px-3 py-2 text-sm" value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask a question..." />
            <button className="rounded bg-slate-900 px-4 py-2 text-sm text-white" onClick={send}>Send</button>
          </div>
        </footer>
      </section>
      <aside className="space-y-4 border-l border-slate-200 bg-white p-4">
        <SampleQuestions onSelect={setInput} />
        <section className="rounded border border-slate-200 p-4">
          <h2 className="text-sm font-semibold">Tips</h2>
          <p className="mt-2 text-sm text-slate-600">Ask specific questions and compare important answers with source references.</p>
        </section>
      </aside>
    </main>
  );
}
