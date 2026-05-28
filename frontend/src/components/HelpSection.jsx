import React from "react";

export default function HelpSection() {
  return (
    <div className="mx-auto max-w-4xl px-6 py-8">
      <h1 className="text-2xl font-semibold text-slate-950">Help</h1>
      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <section className="rounded border border-slate-200 bg-white p-4">
          <h2 className="font-semibold">What the AI can answer</h2>
          <p className="mt-2 text-sm text-slate-600">Questions about approved company documents, policies, procedures, and knowledge base content.</p>
        </section>
        <section className="rounded border border-slate-200 bg-white p-4">
          <h2 className="font-semibold">What the AI cannot answer</h2>
          <p className="mt-2 text-sm text-slate-600">Questions outside uploaded documents, general knowledge, personal opinions, or unsupported claims.</p>
        </section>
        <section className="rounded border border-slate-200 bg-white p-4">
          <h2 className="font-semibold">Use it safely</h2>
          <p className="mt-2 text-sm text-slate-600">Verify important answers with source documents and report incorrect or unsupported responses.</p>
        </section>
        <section className="rounded border border-slate-200 bg-white p-4">
          <h2 className="font-semibold">Confidence scores</h2>
          <p className="mt-2 text-sm text-slate-600">Green means high confidence, yellow means review carefully, and red means low confidence.</p>
        </section>
        <section className="rounded border border-slate-200 bg-white p-4 md:col-span-2">
          <h2 className="font-semibold">Report a problem</h2>
          <p className="mt-2 text-sm text-slate-600">Use the Report Hallucination button on an answer, or contact your organization administrator.</p>
        </section>
      </div>
    </div>
  );
}
