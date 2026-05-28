import React from "react";

function Pulse({ className }) {
  return <div className={`animate-pulse rounded bg-slate-200 ${className}`} />;
}

export function StatsCardSkeleton() {
  return (
    <div className="rounded border border-slate-200 bg-white p-5 shadow-sm">
      <Pulse className="mb-3 h-4 w-24" />
      <Pulse className="h-8 w-16" />
      <Pulse className="mt-2 h-3 w-32" />
    </div>
  );
}

export function DocumentRowSkeleton() {
  return (
    <div className="flex items-center gap-4 border-b border-slate-100 py-3">
      <Pulse className="h-5 w-5 flex-shrink-0" />
      <div className="flex-1 space-y-2">
        <Pulse className="h-4 w-3/4" />
        <Pulse className="h-3 w-1/2" />
      </div>
      <Pulse className="h-6 w-20 rounded-full" />
      <Pulse className="h-8 w-16 rounded" />
    </div>
  );
}

export function ChatMessageSkeleton() {
  return (
    <div className="flex gap-3 py-3">
      <Pulse className="h-8 w-8 flex-shrink-0 rounded-full" />
      <div className="flex-1 space-y-2">
        <Pulse className="h-4 w-full" />
        <Pulse className="h-4 w-5/6" />
        <Pulse className="h-4 w-2/3" />
      </div>
    </div>
  );
}

export function UserRowSkeleton() {
  return (
    <div className="flex items-center gap-4 border-b border-slate-100 py-3">
      <Pulse className="h-8 w-8 flex-shrink-0 rounded-full" />
      <div className="flex-1 space-y-2">
        <Pulse className="h-4 w-48" />
        <Pulse className="h-3 w-36" />
      </div>
      <Pulse className="h-6 w-16 rounded-full" />
      <Pulse className="h-8 w-20 rounded" />
    </div>
  );
}

export function StatsGridSkeleton({ count = 4 }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {Array.from({ length: count }).map((_, i) => (
        <StatsCardSkeleton key={i} />
      ))}
    </div>
  );
}

export function TableSkeleton({ rows = 5, RowComponent = DocumentRowSkeleton }) {
  return (
    <div className="rounded border border-slate-200 bg-white">
      <div className="border-b border-slate-200 p-4">
        <Pulse className="h-5 w-32" />
      </div>
      <div className="divide-y divide-slate-100 px-4">
        {Array.from({ length: rows }).map((_, i) => (
          <RowComponent key={i} />
        ))}
      </div>
    </div>
  );
}
