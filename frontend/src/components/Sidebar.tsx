'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useStore } from '@/store';
import {
  LayoutDashboard, Bot, FolderKanban, ShieldCheck,
  DollarSign, FileText, Activity, ChevronRight,
  Zap, Bell, LogOut, Settings, Menu
} from 'lucide-react';
import clsx from 'clsx';

const nav = [
  { href: '/dashboard',  label: 'Dashboard',    icon: LayoutDashboard },
  { href: '/projects',   label: 'Projects',      icon: FolderKanban },
  { href: '/agents',     label: 'AI Agents',     icon: Bot },
  { href: '/approvals',  label: 'Approvals',     icon: ShieldCheck },
  { href: '/activity',   label: 'Activity Feed', icon: Activity },
  { href: '/costs',      label: 'Cost Monitor',  icon: DollarSign },
  { href: '/audit',      label: 'Audit Log',     icon: FileText },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, pendingApprovalCount, sidebarOpen, setSidebarOpen, clearAuth } = useStore();

  return (
    <>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-20 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside
        className={clsx(
          'sidebar fixed top-0 left-0 h-screen z-30 flex flex-col transition-all duration-300',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0 lg:w-16'
        )}
      >
        {/* ─── Logo ──────────────────────────────────────────────── */}
        <div className="flex items-center gap-3 px-5 py-5 border-b border-brand-500/10">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center flex-shrink-0 glow-purple">
            <Zap size={18} className="text-white" />
          </div>
          {sidebarOpen && (
            <div>
              <div className="text-sm font-bold gradient-text">AI Workforce</div>
              <div className="text-[10px] text-slate-500 font-mono">ENTERPRISE OS v1.0</div>
            </div>
          )}
        </div>

        {/* ─── Navigation ────────────────────────────────────────── */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {nav.map(({ href, label, icon: Icon }) => {
            const active = pathname === href || pathname.startsWith(href + '/');
            const isPendingApprovals = href === '/approvals' && pendingApprovalCount > 0;
            return (
              <Link
                key={href}
                href={href}
                className={clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group relative',
                  active
                    ? 'bg-brand-500/20 text-brand-300 border border-brand-500/30'
                    : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
                )}
              >
                <Icon
                  size={18}
                  className={clsx(
                    'flex-shrink-0 transition-colors',
                    active ? 'text-brand-400' : 'text-slate-500 group-hover:text-slate-300'
                  )}
                />
                {sidebarOpen && <span className="flex-1">{label}</span>}
                {sidebarOpen && isPendingApprovals && (
                  <span className="px-1.5 py-0.5 text-[10px] font-bold rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30 animate-pulse">
                    {pendingApprovalCount}
                  </span>
                )}
                {sidebarOpen && active && (
                  <ChevronRight size={14} className="text-brand-400" />
                )}
              </Link>
            );
          })}
        </nav>

        {/* ─── User Profile ───────────────────────────────────────── */}
        {sidebarOpen && user && (
          <div className="p-3 border-t border-brand-500/10">
            <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl bg-white/5">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center text-xs font-bold flex-shrink-0">
                {user.username?.[0]?.toUpperCase() || 'A'}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-xs font-medium text-slate-200 truncate">{user.username}</div>
                <div className="text-[10px] text-slate-500 capitalize">{user.role?.replace('_', ' ')}</div>
              </div>
              <button
                onClick={() => { clearAuth(); window.location.href = '/login'; }}
                className="text-slate-500 hover:text-red-400 transition-colors"
              >
                <LogOut size={14} />
              </button>
            </div>
          </div>
        )}
      </aside>
    </>
  );
}
