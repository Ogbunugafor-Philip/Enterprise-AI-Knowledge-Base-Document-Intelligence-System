const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function headers(json = true) {
  const token = localStorage.getItem("access_token");
  return {
    ...(json ? { "Content-Type": "application/json" } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function request(path, options = {}) {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, options);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) return { ok: false, status: response.status, error: data.detail || "Request failed", data: null };
    return { ok: true, status: response.status, error: null, data };
  } catch (error) {
    return { ok: false, status: 0, error: error.message, data: null };
  }
}

export const securityApi = {
  getSecurityChecklist: () =>
    request("/api/v1/security/checklist", { headers: headers() }),
  getRateLimitStatus: () =>
    request("/api/v1/security/rate-limit-status", { headers: headers() }),
  resetRateLimit: (key) =>
    request(`/api/v1/security/rate-limit/reset?key=${encodeURIComponent(key)}`, { method: "POST", headers: headers() }),
  getSecurityEvents: (eventType) =>
    request(`/api/v1/security/events${eventType ? `?event_type=${eventType}` : ""}`, { headers: headers() }),
};
