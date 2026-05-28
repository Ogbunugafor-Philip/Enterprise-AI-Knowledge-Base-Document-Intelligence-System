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
    if (response.status === 204) return { ok: true, status: 204, error: null, data: null };
    const data = await response.json().catch(() => ({}));
    if (!response.ok) return { ok: false, status: response.status, error: data.detail || "Request failed", data: null };
    return { ok: true, status: response.status, error: null, data };
  } catch (error) {
    return { ok: false, status: 0, error: error.message, data: null };
  }
}

export const monitoringApi = {
  getDashboard: () =>
    request("/api/v1/monitoring/dashboard", { headers: headers() }),

  getMetrics: (timePeriod = "24h") =>
    request(`/api/v1/monitoring/metrics?time_period=${timePeriod}`, { headers: headers() }),

  getAlerts: (severity) =>
    request(`/api/v1/monitoring/alerts${severity ? `?severity=${severity}` : ""}`, { headers: headers() }),

  getAlert: (id) =>
    request(`/api/v1/monitoring/alerts/${id}`, { headers: headers() }),

  updateAlertStatus: (id, body) =>
    request(`/api/v1/monitoring/alerts/${id}/status`, {
      method: "PUT",
      headers: headers(),
      body: JSON.stringify(body),
    }),

  getIncidents: (status) =>
    request(`/api/v1/monitoring/incidents${status ? `?status=${status}` : ""}`, { headers: headers() }),

  getIncident: (id) =>
    request(`/api/v1/monitoring/incidents/${id}`, { headers: headers() }),

  getHealthSummary: () =>
    request("/api/v1/monitoring/health-summary", { headers: headers() }),

  getRiskAnalysis: () =>
    request("/api/v1/monitoring/risk-analysis", { headers: headers() }),

  getAITrustReport: () =>
    request("/api/v1/monitoring/ai-trust-report", { headers: headers() }),

  getDebuggingHistory: (params = {}) =>
    request(`/api/v1/monitoring/debugging/history?${new URLSearchParams(params)}`, { headers: headers() }),

  getAIQuality: (days = 30) =>
    request(`/api/v1/monitoring/ai-quality?days=${days}`, { headers: headers() }),
};
