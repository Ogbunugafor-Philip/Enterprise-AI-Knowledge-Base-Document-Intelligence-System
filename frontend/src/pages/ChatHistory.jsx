import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { chatApi } from "../services/chatApi.js";

export default function ChatHistory() {
  const [sessions, setSessions] = useState([]);
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);

  const load = () => chatApi.getSessions({ limit: 10, offset: page * 10 }).then((res) => res.ok && setSessions(res.data.sessions || []));
  useEffect(() => { load(); }, [page]);

  const remove = async (id) => {
    if (!window.confirm("Delete this chat session?")) return;
    await chatApi.deleteSession(id);
    load();
  };

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-6">
      <div className="mx-auto max-w-5xl">
        <h1 className="text-2xl font-semibold">Chat history</h1>
        <input className="mt-5 w-full rounded border border-slate-300 px-3 py-2 text-sm" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search conversations..." />
        <section className="mt-5 space-y-3">
          {sessions.length === 0 && <div className="rounded border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">No chat history yet.</div>}
          {sessions.filter((s) => s.title.toLowerCase().includes(query.toLowerCase())).map((session) => (
            <article key={session.id} className="flex items-center justify-between gap-3 rounded border border-slate-200 bg-white p-4">
              <Link to={`/chat/${session.id}`} className="min-w-0">
                <h2 className="font-medium">{session.title}</h2>
                <p className="text-sm text-slate-500">{new Date(session.updated_at).toLocaleString()} • {session.message_count} messages</p>
              </Link>
              <button className="rounded border border-red-200 px-3 py-2 text-sm text-red-700" onClick={() => remove(session.id)}>Delete</button>
            </article>
          ))}
        </section>
        <div className="mt-5 flex justify-between">
          <button className="rounded border px-3 py-2 text-sm" disabled={page === 0} onClick={() => setPage(Math.max(0, page - 1))}>Previous</button>
          <button className="rounded border px-3 py-2 text-sm" onClick={() => setPage(page + 1)}>Next</button>
        </div>
      </div>
    </main>
  );
}
