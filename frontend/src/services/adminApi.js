const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

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
    const data = await response.json().catch(() => ({}));
    if (!response.ok) return { ok: false, status: response.status, error: data.detail || "Request failed", data: null };
    return { ok: true, status: response.status, error: null, data };
  } catch (error) {
    return { ok: false, status: 0, error: error.message, data: null };
  }
}

export const adminApi = {
  uploadDocument: (formData) => request("/api/v1/admin/documents/upload", { method: "POST", headers: headers(false), body: formData }),
  getDocuments: (params = {}) => request(`/api/v1/admin/documents?${new URLSearchParams(params)}`, { headers: headers() }),
  getDocument: (id) => request(`/api/v1/admin/documents/${id}`, { headers: headers() }),
  getDocumentStatus: (id) => request(`/api/v1/admin/documents/${id}/status`, { headers: headers() }),
  getFailedUploads: () => request("/api/v1/admin/documents/failed", { headers: headers() }),
  reprocessDocument: (id) => request(`/api/v1/admin/documents/${id}/reprocess`, { method: "POST", headers: headers() }),
  deleteDocument: (id) => request(`/api/v1/admin/documents/${id}`, { method: "DELETE", headers: headers() }),
  getDashboardStats: () => request("/api/v1/admin/dashboard/stats", { headers: headers() })
};
