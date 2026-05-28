import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import API_BASE_URL from "../config/api.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const raw = localStorage.getItem("ent_rag_user");
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  });

  const [token, setToken] = useState(() => localStorage.getItem("ent_rag_token") || null);

  const isAuthenticated = Boolean(token && user);
  const role = user?.role || null;

  const login = useCallback((accessToken, userData) => {
    localStorage.setItem("ent_rag_token", accessToken);
    localStorage.setItem("ent_rag_user", JSON.stringify(userData));
    // Legacy keys used by existing pages
    localStorage.setItem("access_token", accessToken);
    localStorage.setItem("first_name", userData.first_name || "");
    localStorage.setItem("user_role", userData.role || "");
    localStorage.setItem("user_email", userData.email || "");
    setToken(accessToken);
    setUser(userData);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("ent_rag_token");
    localStorage.removeItem("ent_rag_user");
    localStorage.removeItem("access_token");
    localStorage.removeItem("first_name");
    localStorage.removeItem("user_role");
    localStorage.removeItem("user_email");
    setToken(null);
    setUser(null);
    window.location.href = "/login";
  }, []);

  const getAuthHeader = useCallback(() => {
    return token ? { Authorization: `Bearer ${token}` } : {};
  }, [token]);

  const updateUser = useCallback((updates) => {
    setUser(prev => {
      if (!prev) return prev;
      const updated = { ...prev, ...updates };
      localStorage.setItem("ent_rag_user", JSON.stringify(updated));
      return updated;
    });
  }, []);

  // Keep legacy access_token in sync in case other pages read it
  useEffect(() => {
    if (token) localStorage.setItem("access_token", token);
  }, [token]);

  return (
    <AuthContext.Provider value={{ user, token, isAuthenticated, role, login, logout, getAuthHeader, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
