import React, { Suspense } from "react";

/**
 * Wraps React.lazy with a Suspense boundary and a fallback spinner.
 */
export function lazyLoadComponent(importFn, FallbackComponent = null) {
  const LazyComponent = React.lazy(importFn);
  const fallback = FallbackComponent ? <FallbackComponent /> : (
    <div className="flex items-center justify-center p-8">
      <div className="h-6 w-6 animate-spin rounded-full border-2 border-slate-300 border-t-slate-700" />
    </div>
  );
  return function LazyWrapper(props) {
    return (
      <Suspense fallback={fallback}>
        <LazyComponent {...props} />
      </Suspense>
    );
  };
}

/**
 * Returns a debounced version of fn that fires after `delay` ms of inactivity.
 */
export function debounce(fn, delay = 300) {
  let timer;
  return function debounced(...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

/**
 * Returns a throttled version of fn that fires at most once per `limit` ms.
 */
export function throttle(fn, limit = 100) {
  let lastCall = 0;
  return function throttled(...args) {
    const now = Date.now();
    if (now - lastCall >= limit) {
      lastCall = now;
      return fn.apply(this, args);
    }
  };
}

/**
 * In-memory API response cache with a 30-second TTL.
 */
const _memCache = new Map();
const MEM_CACHE_TTL_MS = 30_000;

export function memoizeApiCall(key, apiFn) {
  return async function memoized(...args) {
    const cacheKey = `${key}:${JSON.stringify(args)}`;
    const hit = _memCache.get(cacheKey);
    if (hit && Date.now() - hit.ts < MEM_CACHE_TTL_MS) {
      return hit.value;
    }
    const result = await apiFn(...args);
    _memCache.set(cacheKey, { value: result, ts: Date.now() });
    return result;
  };
}

/**
 * Lightweight relative time formatter (no external dependency).
 */
export function formatRelativeTime(dateInput) {
  const date = dateInput instanceof Date ? dateInput : new Date(dateInput);
  const seconds = Math.round((Date.now() - date.getTime()) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.round(hours / 24);
  if (days < 30) return `${days}d ago`;
  return date.toLocaleDateString();
}
