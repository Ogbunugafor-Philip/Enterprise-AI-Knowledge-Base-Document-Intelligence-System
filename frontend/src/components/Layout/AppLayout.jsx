import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import {
  LayoutDashboard, MessageSquare, Clock, HelpCircle,
  FileText, CheckSquare, GitBranch,
  Users, Building2, Shield,
  Activity, Bell, Bug, Brain,
  ScrollText, BarChart3,
  Lock, Database,
  Menu, X, ChevronRight, LogOut, ShieldCheck
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext.jsx';

const navGroups = [
  {
    label: 'Workspace',
    roles: ['USER', 'ADMIN', 'SUPER_ADMIN'],
    items: [
      { label: 'Dashboard',    icon: LayoutDashboard, path: '/dashboard' },
      { label: 'Chat',         icon: MessageSquare,   path: '/chat' },
      { label: 'History',      icon: Clock,           path: '/history' },
      { label: 'Help',         icon: HelpCircle,      path: '/help' },
    ],
  },
  {
    label: 'Admin',
    roles: ['ADMIN', 'SUPER_ADMIN'],
    items: [
      { label: 'Documents',    icon: FileText,        path: '/admin/documents' },
      { label: 'Approvals',    icon: CheckSquare,     path: '/admin/approvals' },
      { label: 'Versions',     icon: GitBranch,       path: '/admin/documents/versions' },
    ],
  },
  {
    label: 'Super Admin',
    roles: ['SUPER_ADMIN'],
    items: [
      { label: 'Users',         icon: Users,    path: '/superadmin/users' },
      { label: 'Organizations', icon: Building2, path: '/superadmin/organizations' },
      { label: 'Roles',         icon: Shield,   path: '/superadmin/roles' },
    ],
  },
  {
    label: 'System',
    roles: ['ADMIN', 'SUPER_ADMIN'],
    items: [
      { label: 'Monitoring',   icon: Activity, path: '/monitoring' },
      { label: 'Alerts',       icon: Bell,     path: '/monitoring/alerts' },
      { label: 'Debugging',    icon: Bug,      path: '/monitoring/debugging', roles: ['SUPER_ADMIN'] },
      { label: 'AI Trust',     icon: Brain,    path: '/monitoring/ai-trust' },
    ],
  },
  {
    label: 'Compliance',
    roles: ['ADMIN', 'SUPER_ADMIN'],
    items: [
      { label: 'Audit Logs', icon: ScrollText, path: '/compliance/audit-logs' },
      { label: 'Reports',    icon: BarChart3,  path: '/compliance/reports', roles: ['SUPER_ADMIN'] },
    ],
  },
  {
    label: 'Security',
    roles: ['SUPER_ADMIN'],
    items: [
      { label: 'Security', icon: Lock,     path: '/security' },
      { label: 'Backup',   icon: Database, path: '/backup' },
    ],
  },
];

function getRoleBadge(role) {
  const map = {
    SUPER_ADMIN: 'bg-purple-500/20 text-purple-200',
    ADMIN: 'bg-blue-500/20 text-blue-200',
    USER: 'bg-slate-500/20 text-slate-300',
  };
  return map[role] || map.USER;
}

function getInitials(user) {
  if (!user) return '?';
  return `${(user.first_name || '')[0] || ''}${(user.last_name || '')[0] || ''}`.toUpperCase() || '?';
}

function SidebarContent({ role, user, onNav, location, onLogout }) {
  return (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-slate-700/50">
        <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-blue-600 shadow-lg">
          <ShieldCheck className="w-5 h-5 text-white" />
        </div>
        <div>
          <span className="text-white font-bold text-base tracking-tight">DocIntel</span>
          <div className="text-slate-400 text-xs">Enterprise AI</div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-0.5">
        {navGroups.map((group) => {
          const groupRoles = group.roles || [];
          if (!groupRoles.includes(role)) return null;
          const visibleItems = group.items.filter(item =>
            !item.roles || item.roles.includes(role)
          );
          if (visibleItems.length === 0) return null;
          return (
            <div key={group.label}>
              <div className="sidebar-section">{group.label}</div>
              {visibleItems.map((item) => {
                const active = location.pathname === item.path ||
                  (item.path !== '/dashboard' && location.pathname.startsWith(item.path));
                return (
                  <button
                    key={item.path}
                    onClick={() => onNav(item.path)}
                    className={`sidebar-item w-full text-left ${active ? 'sidebar-item-active' : 'sidebar-item-inactive'}`}
                  >
                    <item.icon className="w-4 h-4 flex-shrink-0" />
                    <span>{item.label}</span>
                    {active && <ChevronRight className="w-3.5 h-3.5 ml-auto opacity-70" />}
                  </button>
                );
              })}
            </div>
          );
        })}
      </nav>

      {/* User profile */}
      <div className="border-t border-slate-700/50 p-4">
        <div className="flex items-center gap-3">
          <div className="flex-shrink-0 w-9 h-9 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm font-semibold">
            {getInitials(user)}
          </div>
          <div className="min-w-0 flex-1">
            <div className="text-white text-sm font-medium truncate">
              {user?.first_name} {user?.last_name}
            </div>
            <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${getRoleBadge(role)}`}>
              {role?.replace('_', ' ')}
            </span>
          </div>
          <button onClick={onLogout} className="text-slate-400 hover:text-white transition-colors p-1 rounded" title="Sign out">
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

export default function AppLayout({ children, title, subtitle, actions }) {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, role, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  function handleNav(path) {
    navigate(path);
    setSidebarOpen(false);
  }

  return (
    <div className="flex h-screen bg-slate-100 overflow-hidden">
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex flex-col w-64 bg-slate-900 shadow-sidebar flex-shrink-0">
        <SidebarContent role={role} user={user} onNav={handleNav} location={location} onLogout={logout} />
      </aside>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setSidebarOpen(false)} />
          <aside className="absolute left-0 top-0 bottom-0 w-64 bg-slate-900 shadow-sidebar">
            <SidebarContent role={role} user={user} onNav={handleNav} location={location} onLogout={logout} />
          </aside>
        </div>
      )}

      {/* Main */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        {/* Top bar */}
        <header className="flex-shrink-0 h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 shadow-sm z-10">
          <div className="flex items-center gap-3">
            <button className="lg:hidden text-gray-500 hover:text-gray-700 p-1.5 rounded-lg hover:bg-gray-100" onClick={() => setSidebarOpen(true)}>
              <Menu className="w-5 h-5" />
            </button>
            <div>
              {title && <h1 className="text-lg font-semibold text-gray-900 leading-tight">{title}</h1>}
              {subtitle && <p className="text-xs text-gray-500 leading-tight">{subtitle}</p>}
            </div>
          </div>
          <div className="flex items-center gap-3">
            {actions}
            <button className="relative text-gray-500 hover:text-gray-700 p-2 rounded-lg hover:bg-gray-100 transition-colors">
              <Bell className="w-5 h-5" />
            </button>
            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs font-semibold cursor-pointer" onClick={() => navigate('/dashboard')}>
              {getInitials(user)}
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
