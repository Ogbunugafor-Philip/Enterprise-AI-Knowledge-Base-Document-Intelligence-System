import API_BASE_URL from "../config/api.js";

function headers(json = true) {
  const token = localStorage.getItem("access_token");
  return {
    ...(json ? { "Content-Type": "application/json" } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {})
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

export const adminApi = {
  // Documents
  uploadDocument: (formData) => request("/api/v1/admin/documents/upload", { method: "POST", headers: headers(false), body: formData }),
  getDocuments: (params = {}) => request(`/api/v1/admin/documents?${new URLSearchParams(params)}`, { headers: headers() }),
  getDocument: (id) => request(`/api/v1/admin/documents/${id}`, { headers: headers() }),
  getDocumentStatus: (id) => request(`/api/v1/admin/documents/${id}/status`, { headers: headers() }),
  getFailedUploads: () => request("/api/v1/admin/documents/failed", { headers: headers() }),
  reprocessDocument: (id) => request(`/api/v1/admin/documents/${id}/reprocess`, { method: "POST", headers: headers() }),
  deleteDocument: (id) => request(`/api/v1/admin/documents/${id}`, { method: "DELETE", headers: headers() }),
  getDashboardStats: () => request("/api/v1/admin/dashboard/stats", { headers: headers() }),

  // Approvals
  getApprovalQueue: (params = {}) => request(`/api/v1/admin/approvals/queue?${new URLSearchParams(params)}`, { headers: headers() }),
  approveDocument: (body) => request("/api/v1/admin/approvals/approve", { method: "POST", headers: headers(), body: JSON.stringify(body) }),
  rejectDocument: (body) => request("/api/v1/admin/approvals/reject", { method: "POST", headers: headers(), body: JSON.stringify(body) }),
  getApprovalHistory: (id) => request(`/api/v1/admin/approvals/${id}/history`, { headers: headers() }),
  getGovernanceStats: () => request("/api/v1/admin/approvals/stats", { headers: headers() }),

  // Versions
  uploadDocumentVersion: (id, formData) => request(`/api/v1/admin/documents/${id}/versions`, { method: "POST", headers: headers(false), body: formData }),
  getDocumentVersions: (id) => request(`/api/v1/admin/documents/${id}/versions`, { headers: headers() }),
  rollbackVersion: (id, versionId) => request(`/api/v1/admin/documents/${id}/versions/${versionId}/rollback`, { method: "POST", headers: headers() }),

  // Access Rules
  createAccessRule: (docId, body) => request(`/api/v1/admin/documents/${docId}/access-rules`, { method: "POST", headers: headers(), body: JSON.stringify(body) }),
  getAccessRules: (docId) => request(`/api/v1/admin/documents/${docId}/access-rules`, { headers: headers() }),
  deleteAccessRule: (docId, ruleId) => request(`/api/v1/admin/documents/${docId}/access-rules/${ruleId}`, { method: "DELETE", headers: headers() }),
};
