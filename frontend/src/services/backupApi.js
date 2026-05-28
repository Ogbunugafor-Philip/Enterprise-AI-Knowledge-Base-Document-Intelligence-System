const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function headers() {
  const token = localStorage.getItem("access_token");
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function request(path, options = {}) {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers: { ...headers(), ...(options.headers || {}) } });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) return { ok: false, status: response.status, error: data.detail || "Request failed", data: null };
    return { ok: true, status: response.status, error: null, data };
  } catch (error) {
    return { ok: false, status: 0, error: error.message, data: null };
  }
}

export const backupApi = {
  runBackup: () => request("/api/v1/backup/run", { method: "POST" }),
  getBackupHistory: () => request("/api/v1/backup/history"),
  checkIntegrity: (id) => request(`/api/v1/backup/${id}/integrity`),
  runDryRun: (backupId) => request("/api/v1/backup/restore/dry-run", { method: "POST", body: JSON.stringify({ backup_id: backupId }) }),
  restorePostgresql: (body) => request("/api/v1/backup/restore/postgresql", { method: "POST", body: JSON.stringify(body) }),
  restoreQdrant: (body) => request("/api/v1/backup/restore/qdrant", { method: "POST", body: JSON.stringify(body) }),
  restoreDocuments: (body) => request("/api/v1/backup/restore/documents", { method: "POST", body: JSON.stringify(body) }),
};
