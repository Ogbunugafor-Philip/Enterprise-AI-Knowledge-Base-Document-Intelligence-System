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

async function requestBlob(path) {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, { headers: headers(false) });
    if (!response.ok) return { ok: false, blob: null, error: "Download failed" };
    const blob = await response.blob();
    return { ok: true, blob, error: null };
  } catch (error) {
    return { ok: false, blob: null, error: error.message };
  }
}

export const superAdminApi = {
  getDashboardStats: () =>
    request("/api/v1/superadmin/dashboard/stats", { headers: headers() }),

  getUsers: (params = {}) =>
    request(`/api/v1/superadmin/users?${new URLSearchParams(params)}`, { headers: headers() }),

  getUser: (id) =>
    request(`/api/v1/superadmin/users/${id}`, { headers: headers() }),

  createUser: (body) =>
    request("/api/v1/superadmin/users", { method: "POST", headers: headers(), body: JSON.stringify(body) }),

  updateUser: (id, body) =>
    request(`/api/v1/superadmin/users/${id}`, { method: "PUT", headers: headers(), body: JSON.stringify(body) }),

  activateUser: (id) =>
    request(`/api/v1/superadmin/users/${id}/activate`, { method: "POST", headers: headers() }),

  deactivateUser: (id, body) =>
    request(`/api/v1/superadmin/users/${id}/deactivate`, { method: "POST", headers: headers(), body: JSON.stringify(body) }),

  deleteUser: (id) =>
    request(`/api/v1/superadmin/users/${id}`, { method: "DELETE", headers: headers() }),

  resetUserPassword: (id, body) =>
    request(`/api/v1/superadmin/users/${id}/reset-password`, { method: "POST", headers: headers(), body: JSON.stringify(body) }),

  unlockUser: (id) =>
    request(`/api/v1/superadmin/users/${id}/unlock`, { method: "POST", headers: headers() }),

  bulkUploadUsers: (formData) =>
    request("/api/v1/superadmin/users/bulk-upload", { method: "POST", headers: headers(false), body: formData }),

  downloadBulkTemplate: () =>
    requestBlob("/api/v1/superadmin/users/bulk-upload/template"),
};
