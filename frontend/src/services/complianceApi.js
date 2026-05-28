import { API_BASE_URL } from "../config/environment.js";

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

async function requestBlob(path, options = {}) {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, options);
    if (!response.ok) return { ok: false, blob: null, error: "Download failed" };
    const blob = await response.blob();
    return { ok: true, blob, error: null };
  } catch (error) {
    return { ok: false, blob: null, error: error.message };
  }
}

export const complianceApi = {
  getAuditLogs: (params = {}) =>
    request(`/api/v1/compliance/audit-logs?${new URLSearchParams(params)}`, { headers: headers() }),
  getAuditLogDetail: (id) =>
    request(`/api/v1/compliance/audit-logs/${id}`, { headers: headers() }),
  exportAuditLogs: (params = {}) =>
    requestBlob(`/api/v1/compliance/audit-logs/export?${new URLSearchParams(params)}`, { headers: headers(false) }),
  generateReport: (body) =>
    requestBlob("/api/v1/compliance/reports/generate", { method: "POST", headers: headers(), body: JSON.stringify(body) }),
  getActivityReport: (params = {}) =>
    request(`/api/v1/compliance/reports/activity?${new URLSearchParams(params)}`, { headers: headers() }),
  getSecurityReport: (params = {}) =>
    request(`/api/v1/compliance/reports/security?${new URLSearchParams(params)}`, { headers: headers() }),
  getUserActivity: (id, params = {}) =>
    request(`/api/v1/compliance/user/${id}/activity?${new URLSearchParams(params)}`, { headers: headers() }),
  getUserDataExport: (id) =>
    request(`/api/v1/compliance/user/${id}/data-export`, { headers: headers() }),
  getRetentionSettings: () =>
    request("/api/v1/compliance/retention-settings", { headers: headers() }),
  updateRetentionSettings: (body) =>
    request("/api/v1/compliance/retention-settings", { method: "PUT", headers: headers(), body: JSON.stringify(body) }),
};
