import API_BASE_URL from "../config/api.js";

function authHeaders() {
  const token = localStorage.getItem("access_token");
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {})
  };
}

async function request(path, options = {}) {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: { ...authHeaders(), ...(options.headers || {}) }
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      return { ok: false, status: response.status, error: data.detail || "Request failed", data: null };
    }
    return { ok: true, status: response.status, error: null, data };
  } catch (error) {
    return { ok: false, status: 0, error: error.message, data: null };
  }
}

export const chatApi = {
  createSession: (payload) => request("/api/v1/chat/sessions", { method: "POST", body: JSON.stringify(payload) }),
  getSessions: (params = {}) => request(`/api/v1/chat/sessions?${new URLSearchParams(params)}`),
  getSession: (id) => request(`/api/v1/chat/sessions/${id}`),
  deleteSession: (id) => request(`/api/v1/chat/sessions/${id}`, { method: "DELETE" }),
  askQuestion: (payload) => request("/api/v1/chat/ask", { method: "POST", body: JSON.stringify(payload) }),
  submitFeedback: (payload) => request("/api/v1/chat/feedback", { method: "POST", body: JSON.stringify(payload) }),
  searchConversations: (params) => request(`/api/v1/chat/search?${new URLSearchParams(params)}`),
  getSampleQuestions: () => request("/api/v1/chat/sample-questions"),
  getOnboardingStatus: () => request("/api/v1/chat/onboarding-status"),
  completeOnboardingStep: (payload) => request("/api/v1/chat/onboarding/complete-step", { method: "POST", body: JSON.stringify(payload) }),
  completeOnboarding: () => request("/api/v1/chat/onboarding/complete", { method: "POST" }),
  getUserStats: () => request("/api/v1/users/me/usage-stats")
};
