import React, { useMemo, useState } from "react";
import { RefreshCw } from "lucide-react";

const fallbackQuestions = [
  "What policies apply to my department?",
  "Summarize approved onboarding documents.",
  "Which source explains this workflow?",
  "What are the compliance requirements?",
  "What changed in the latest document version?",
  "Show approved guidance for this process.",
  "Which document should I read first?",
  "What are the key action items?"
];

export default function SampleQuestions({ questions = fallbackQuestions, onSelect }) {
  const [page, setPage] = useState(0);
  const visible = useMemo(() => {
    const start = (page * 5) % questions.length;
    return [...questions, ...questions].slice(start, start + 5);
  }, [questions, page]);

  return (
    <section className="rounded border border-slate-200 bg-white p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-950">Sample questions</h2>
        <button className="rounded p-1 hover:bg-slate-100" onClick={() => setPage(page + 1)} title="Refresh samples">
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>
      <div className="space-y-2">
        {visible.map((question) => (
          <button key={question} className="block w-full rounded border border-slate-200 px-3 py-2 text-left text-sm text-slate-700 hover:border-slate-400" onClick={() => onSelect?.(question)}>
            {question}
          </button>
        ))}
      </div>
    </section>
  );
}
