import React, { useState } from "react";

const steps = [
  ["Welcome", "Use the AI knowledge base to ask questions grounded in approved company documents."],
  ["Ask questions", "Type focused questions in the input box. Include the policy, workflow, or topic you need."],
  ["Read answers", "Review source references and confidence scores before using an answer for important work."],
  ["Give feedback", "Use feedback buttons to mark correct answers, unclear answers, or possible hallucinations."],
  ["Find help", "Open Help when you need usage guidance or your administrator contact path."]
];

export default function OnboardingTour({ onComplete }) {
  const [index, setIndex] = useState(0);
  const [visible, setVisible] = useState(() => localStorage.getItem("ent_rag_tour_done") !== "true");

  if (!visible) return null;

  const finish = () => {
    localStorage.setItem("ent_rag_tour_done", "true");
    setVisible(false);
    onComplete?.();
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/50 p-4">
      <div className="mx-auto mt-24 max-w-lg rounded bg-white p-6 shadow-xl">
        <div className="mb-3 text-sm text-slate-500">Step {index + 1} of {steps.length}</div>
        <h2 className="text-xl font-semibold text-slate-950">{steps[index][0]}</h2>
        <p className="mt-3 text-sm leading-6 text-slate-600">{steps[index][1]}</p>
        <div className="mt-6 h-2 rounded bg-slate-100">
          <div className="h-2 rounded bg-slate-800" style={{ width: `${((index + 1) / steps.length) * 100}%` }} />
        </div>
        <div className="mt-6 flex justify-between gap-2">
          <button className="rounded border px-3 py-2 text-sm" onClick={() => setIndex(Math.max(0, index - 1))}>Previous</button>
          <div className="flex gap-2">
            <button className="rounded border px-3 py-2 text-sm" onClick={finish}>Skip Tour</button>
            <button className="rounded bg-slate-900 px-3 py-2 text-sm text-white" onClick={() => (index === steps.length - 1 ? finish() : setIndex(index + 1))}>
              {index === steps.length - 1 ? "Finish" : "Next"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
