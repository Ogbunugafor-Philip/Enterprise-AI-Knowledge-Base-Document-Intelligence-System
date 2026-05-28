// In production the frontend is served from the same origin as the API,
// so we use an empty string (relative paths like /api/v1/...) — no CORS involved.
// In local development we hit the backend container directly on port 8010.
const API_BASE_URL = window.location.hostname === "localhost"
  ? "http://localhost:8010"
  : "";

export default API_BASE_URL;
