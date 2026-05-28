import React from "react";
import { Navigate, Route, Routes, Link } from "react-router-dom";

import { AuthProvider, useAuth } from "./context/AuthContext.jsx";
import { ErrorBoundary } from "./utils/errorBoundary.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";

// Pages
import Login from "./pages/Login.jsx";
import UserDashboard from "./pages/UserDashboard.jsx";
import ChatInterface from "./pages/ChatInterface.jsx";
import ChatHistory from "./pages/ChatHistory.jsx";
import AdminDashboard from "./pages/AdminDashboard.jsx";
import DocumentManagement from "./pages/DocumentManagement.jsx";
import DocumentVersions from "./pages/DocumentVersions.jsx";
import ApprovalQueue from "./pages/ApprovalQueue.jsx";
import SuperAdminDashboard from "./pages/SuperAdminDashboard.jsx";
import UserManagement from "./pages/UserManagement.jsx";
import MonitoringDashboard from "./pages/MonitoringDashboard.jsx";
import AlertsPanel from "./pages/AlertsPanel.jsx";
import DebuggingAssistant from "./pages/DebuggingAssistant.jsx";
import AITrustReport from "./pages/AITrustReport.jsx";
import AuditLogs from "./pages/AuditLogs.jsx";
import ComplianceReports from "./pages/ComplianceReports.jsx";
import SecurityDashboard from "./pages/SecurityDashboard.jsx";
import BackupManagement from "./pages/BackupManagement.jsx";

// Components
import DataRetentionSettings from "./components/DataRetentionSettings.jsx";
import HelpSection from "./components/HelpSection.jsx";

// ─── Unauthorized page ───────────────────────────────────────────────────────

function Unauthorized() {
  const { logout, role } = useAuth();
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-slate-50 text-slate-900">
      <h1 className="text-2xl font-semibold">Access Denied</h1>
      <p className="text-slate-500">You don't have permission to view this page (role: {role || "none"}).</p>
      <div className="flex gap-3">
        <button onClick={() => window.history.back()} className="rounded border px-4 py-2 text-sm">Go back</button>
        <button onClick={logout} className="rounded bg-slate-900 px-4 py-2 text-sm text-white">Sign out</button>
      </div>
    </div>
  );
}

// ─── Root redirect based on role ─────────────────────────────────────────────

function RootRedirect() {
  const { isAuthenticated, role } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (role === "SUPER_ADMIN") return <Navigate to="/superadmin/dashboard" replace />;
  if (role === "ADMIN") return <Navigate to="/admin/dashboard" replace />;
  return <Navigate to="/dashboard" replace />;
}

// ─── Routes ──────────────────────────────────────────────────────────────────

function AppRoutes() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/login" element={<Login />} />
      <Route path="/unauthorized" element={<Unauthorized />} />

      {/* Root — redirect based on role */}
      <Route path="/" element={<RootRedirect />} />

      {/* ── User routes ── */}
      <Route path="/dashboard" element={
        <ProtectedRoute><UserDashboard /></ProtectedRoute>
      } />
      <Route path="/chat" element={
        <ProtectedRoute><ChatInterface /></ProtectedRoute>
      } />
      <Route path="/chat/:sessionId" element={
        <ProtectedRoute><ChatInterface /></ProtectedRoute>
      } />
      <Route path="/history" element={
        <ProtectedRoute><ChatHistory /></ProtectedRoute>
      } />
      <Route path="/help" element={
        <ProtectedRoute><HelpSection /></ProtectedRoute>
      } />

      {/* ── Admin routes ── */}
      <Route path="/admin/dashboard" element={
        <ProtectedRoute allowedRoles={["ADMIN", "SUPER_ADMIN"]}><AdminDashboard /></ProtectedRoute>
      } />
      <Route path="/admin/documents" element={
        <ProtectedRoute allowedRoles={["ADMIN", "SUPER_ADMIN"]}><DocumentManagement /></ProtectedRoute>
      } />
      <Route path="/admin/documents/:documentId/versions" element={
        <ProtectedRoute allowedRoles={["ADMIN", "SUPER_ADMIN"]}><DocumentVersions /></ProtectedRoute>
      } />
      <Route path="/admin/approvals" element={
        <ProtectedRoute allowedRoles={["ADMIN", "SUPER_ADMIN"]}><ApprovalQueue /></ProtectedRoute>
      } />

      {/* ── Super Admin routes ── */}
      <Route path="/superadmin/dashboard" element={
        <ProtectedRoute allowedRoles={["SUPER_ADMIN"]}><SuperAdminDashboard /></ProtectedRoute>
      } />
      <Route path="/superadmin/users" element={
        <ProtectedRoute allowedRoles={["SUPER_ADMIN"]}><UserManagement /></ProtectedRoute>
      } />

      {/* ── Monitoring routes ── */}
      <Route path="/monitoring" element={
        <ProtectedRoute allowedRoles={["ADMIN", "SUPER_ADMIN"]}><MonitoringDashboard /></ProtectedRoute>
      } />
      <Route path="/monitoring/alerts" element={
        <ProtectedRoute allowedRoles={["ADMIN", "SUPER_ADMIN"]}><AlertsPanel /></ProtectedRoute>
      } />
      <Route path="/monitoring/debugging" element={
        <ProtectedRoute allowedRoles={["ADMIN", "SUPER_ADMIN"]}><DebuggingAssistant /></ProtectedRoute>
      } />
      <Route path="/monitoring/ai-trust" element={
        <ProtectedRoute allowedRoles={["ADMIN", "SUPER_ADMIN"]}><AITrustReport /></ProtectedRoute>
      } />

      {/* ── Compliance routes ── */}
      <Route path="/compliance/audit-logs" element={
        <ProtectedRoute allowedRoles={["ADMIN", "SUPER_ADMIN"]}><AuditLogs /></ProtectedRoute>
      } />
      <Route path="/compliance/reports" element={
        <ProtectedRoute allowedRoles={["ADMIN", "SUPER_ADMIN"]}><ComplianceReports /></ProtectedRoute>
      } />
      <Route path="/compliance/retention" element={
        <ProtectedRoute allowedRoles={["ADMIN", "SUPER_ADMIN"]}><DataRetentionSettings /></ProtectedRoute>
      } />

      {/* ── Security & Backup ── */}
      <Route path="/security" element={
        <ProtectedRoute allowedRoles={["ADMIN", "SUPER_ADMIN"]}><SecurityDashboard /></ProtectedRoute>
      } />
      <Route path="/backup" element={
        <ProtectedRoute allowedRoles={["ADMIN", "SUPER_ADMIN"]}><BackupManagement /></ProtectedRoute>
      } />

      {/* Catch-all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

// ─── Root export ─────────────────────────────────────────────────────────────

export default function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </ErrorBoundary>
  );
}
