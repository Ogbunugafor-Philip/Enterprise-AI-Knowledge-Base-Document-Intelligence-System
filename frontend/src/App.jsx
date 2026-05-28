import React from "react";
import { Link, Navigate, Route, Routes } from "react-router-dom";
import { ErrorBoundary } from "./utils/errorBoundary.jsx";
import { Building2, ShieldCheck, UserRoundCog } from "lucide-react";
import DataRetentionSettings from "./components/DataRetentionSettings.jsx";
import HelpSection from "./components/HelpSection.jsx";
import AdminDashboard from "./pages/AdminDashboard.jsx";
import AITrustReport from "./pages/AITrustReport.jsx";
import AuditLogs from "./pages/AuditLogs.jsx";
import BackupManagement from "./pages/BackupManagement.jsx";
import AlertsPanel from "./pages/AlertsPanel.jsx";
import ApprovalQueue from "./pages/ApprovalQueue.jsx";
import DebuggingAssistant from "./pages/DebuggingAssistant.jsx";
import MonitoringDashboard from "./pages/MonitoringDashboard.jsx";
import SecurityDashboard from "./pages/SecurityDashboard.jsx";
import ChatHistory from "./pages/ChatHistory.jsx";
import ChatInterface from "./pages/ChatInterface.jsx";
import ComplianceReports from "./pages/ComplianceReports.jsx";
import DocumentManagement from "./pages/DocumentManagement.jsx";
import DocumentVersions from "./pages/DocumentVersions.jsx";
import SuperAdminDashboard from "./pages/SuperAdminDashboard.jsx";
import UserDashboard from "./pages/UserDashboard.jsx";
import UserManagement from "./pages/UserManagement.jsx";

function WorkspaceCard({ icon: Icon, title, description, to }) {
  return (
    <Link
      to={to}
      className="rounded border border-slate-200 bg-white p-5 shadow-sm transition hover:border-slate-400"
    >
      <Icon className="mb-4 h-6 w-6 text-slate-700" aria-hidden="true" />
      <h2 className="text-lg font-semibold text-slate-950">{title}</h2>
      <p className="mt-2 text-sm leading-6 text-slate-600">{description}</p>
    </Link>
  );
}

function Layout({ children }) {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link to="/" className="text-base font-semibold">
            Ent_RAG
          </Link>
          <nav className="flex gap-4 text-sm text-slate-600">
            <Link className="hover:text-slate-950" to="/user">User</Link>
            <Link className="hover:text-slate-950" to="/admin">Admin</Link>
            <Link className="hover:text-slate-950" to="/super-admin">Super Admin</Link>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
    </div>
  );
}

function Home() {
  return (
    <Layout>
      <section className="mb-8">
        <h1 className="text-3xl font-semibold tracking-normal">Enterprise AI Knowledge Base</h1>
        <p className="mt-3 max-w-3xl text-slate-600">
          A multi-tenant document intelligence platform for secure ingestion,
          retrieval, administration, and monitoring.
        </p>
      </section>
      <section className="grid gap-4 md:grid-cols-3">
        <WorkspaceCard
          icon={Building2}
          title="User Workspace"
          description="Search approved knowledge sources, inspect document answers, and manage personal activity."
          to="/user"
        />
        <WorkspaceCard
          icon={UserRoundCog}
          title="Admin Workspace"
          description="Manage organization users, departments, document ingestion, and access controls."
          to="/admin"
        />
        <WorkspaceCard
          icon={ShieldCheck}
          title="Super Admin Workspace"
          description="Oversee tenants, platform health, compliance controls, and global monitoring."
          to="/super-admin"
        />
      </section>
    </Layout>
  );
}

function Workspace({ title, description }) {
  return (
    <Layout>
      <h1 className="text-2xl font-semibold">{title}</h1>
      <p className="mt-3 max-w-3xl text-slate-600">{description}</p>
      <div className="mt-6 rounded border border-dashed border-slate-300 bg-white p-6 text-sm text-slate-600">
        Workspace implementation placeholder for Phase 2.
      </div>
    </Layout>
  );
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/dashboard" element={<UserDashboard />} />
      <Route path="/chat" element={<ChatInterface />} />
      <Route path="/chat/:sessionId" element={<ChatInterface />} />
      <Route path="/history" element={<ChatHistory />} />
      <Route path="/help" element={<HelpSection />} />
      <Route path="/admin/dashboard" element={<AdminDashboard />} />
      <Route path="/admin/approvals" element={<ApprovalQueue />} />
      <Route path="/admin/documents" element={<DocumentManagement />} />
      <Route path="/admin/documents/:documentId/versions" element={<DocumentVersions />} />
      <Route
        path="/user"
        element={<Workspace title="User Workspace" description="Tenant-scoped knowledge retrieval and document intelligence." />}
      />
      <Route
        path="/admin"
        element={<Workspace title="Admin Workspace" description="Organization-level controls for documents, users, and departments." />}
      />
      <Route path="/monitoring" element={<MonitoringDashboard />} />
      <Route path="/monitoring/alerts" element={<AlertsPanel />} />
      <Route path="/monitoring/debugging" element={<DebuggingAssistant />} />
      <Route path="/monitoring/ai-trust" element={<AITrustReport />} />
      <Route path="/compliance/audit-logs" element={<AuditLogs />} />
      <Route path="/compliance/reports" element={<ComplianceReports />} />
      <Route path="/compliance/retention" element={<DataRetentionSettings />} />
      <Route path="/security" element={<SecurityDashboard />} />
      <Route path="/backup" element={<BackupManagement />} />
      <Route path="/superadmin/dashboard" element={<SuperAdminDashboard />} />
      <Route path="/superadmin/users" element={<UserManagement />} />
      <Route
        path="/super-admin"
        element={<Workspace title="Super Admin Workspace" description="Platform-wide tenant operations, security, and monitoring." />}
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function AppWithErrorBoundary() {
  return (
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  );
}
