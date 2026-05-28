// Base URL for API calls — paths in service files already include /api/v1/...
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "https://docintel.space";

export const APP_URL =
  import.meta.env.VITE_APP_URL || "https://docintel.space";

export const ENVIRONMENT =
  import.meta.env.VITE_ENV || "production";
