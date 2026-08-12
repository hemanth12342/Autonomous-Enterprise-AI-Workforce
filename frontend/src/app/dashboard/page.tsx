'use client';
import DashboardLayout from '@/components/DashboardLayout';
import { useStore } from '@/store';
import { useEffect, useState } from 'react';
import { projectsApi, agentsApi, costsApi, demoApi } from '@/lib/api';
import { toast } from 'sonner';
import {
  Bot, FolderKanban, DollarSign, ShieldCheck, Zap,
  TrendingUp, Clock, CheckCircle2, AlertTriangle, Play,
  ChevronRight, ArrowRight
} from 'lucide-react';
import Link from 'next/link';
import clsx from 'clsx';

const AGENT_COLORS: Record<string, string> = {
  ceo:              '#6366f1',
  project_manager:  '#8b5cf6',
  developer:        '#06b6d4',
  qa:               '#10b981',
  security:         '#f59e0b',
  devops:           '#ef4444',
  documentation:    '#84cc16',
  support:          '#f97316',
  research:         '#a78bfa',
};

export default function DashboardPage() {
  const { projects, setProjects, agents, setAgents, pendingApprovalCount, events } = useStore();
  const [costs, setCosts] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [demoLoading, setDemoLoading] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [p, a, c] = await Promise.allSettled([
          projectsApi.list(),
          agentsApi.list(),
          costsApi.summary(),
        ]);
        if (p.status === 'fulfilled') setProjects(p.value);
        if (a.status === 'fulfilled') setAgents(a.value);
        if (c.status === 'fulfilled') setCosts(c.value);
      } catch {}
      finally { setLoading(false); }
    })();
  }, [setProjects, setAgents]);

  const startDemo = async (key: string) => {
    setDemoLoading(key);
    try {
      const res = await demoApi.start(key);
      toast.success(`🚀 Demo started! Watch the activity feed.`);
      setProjects([{ id: res.project_id, name: res.project_name, business_objective: res.objective, status: 'planning', priority: 'high', progress_percent: 0, total_tasks: 0, completed_tasks: 0, actual_cost_usd: 0, budget_usd: 5, created_at: new Date().toISOString(), is_demo: true }, ...projects]);
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Failed to start demo');
    } finally { setDemoLoading(null); }
  };

  const statusColor: Record<string, string> = {
    draft: 'badge-idle', planning: 'badge-running', active: 'badge-working',
    completed: 'badge-success', failed: 'badge-failed', awaiting_approval: 'badge-approval',
  };

  const activeAgents = agents.filter((a) => a.status === 'working').length;
  const completedProjects = projects.filter((p) => p.status === 'completed').length;
  const totalCost = costs?.total_cost_usd ?? 0;

  return (
    <DashboardLayout title="Dashboard">
      <div className="space-y-6 animate-fade-in">

        {/* ─── KPI Cards ─────────────────────────────────────────── */}
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
          {[
            { label: 'Total Projects', value: projects.length, icon: FolderKanban, color: '#6366f1', sub: `${completedProjects} completed` },
            { label: 'Active Agents', value: `${activeAgents}/9`, icon: Bot, color: '#06b6d4', sub: 'Working right now' },
            { label: 'Pending Approvals', value: pendingApprovalCount, icon: ShieldCheck, color: '#f59e0b', sub: 'Awaiting human review', alert: pendingApprovalCount > 0 },
            { label: 'Total LLM Cost', value: `$${totalCost.toFixed(4)}`, icon: DollarSign, color: '#10b981', sub: 'Across all projects' },
          ].map(({ label, value, icon: Icon, color, sub, alert }) => (
            <div key={label} className={clsx('glass-card p-5 glass-card-hover', alert && 'border-amber-500/30')}>
              <div className="flex items-start justify-between mb-3">
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center"
                  style={{ background: `${color}20`, border: `1px solid ${color}40` }}
                >
                  <Icon size={20} style={{ color }} />
                </div>
                {alert && <span className="text-amber-400 animate-pulse text-xs">●</span>}
              </div>
              <div className="text-2xl font-bold text-slate-100 mb-0.5">{value}</div>
              <div className="text-xs text-slate-400">{label}</div>
              <div className="text-[11px] text-slate-600 mt-1">{sub}</div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* ─── Agent Status Grid ──────────────────────────────── */}
          <div className="xl:col-span-2 glass-card p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <Bot size={16} className="text-brand-400" /> AI Workforce Status
              </h2>
              <Link href="/agents" className="text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1">
                View all <ChevronRight size={12} />
              </Link>
            </div>
            <div className="grid grid-cols-3 gap-3">
              {agents.map((agent) => (
                <div
                  key={agent.agent_type}
                  className="p-3 rounded-xl border border-white/5 bg-white/3 hover:bg-white/5 transition-all cursor-default"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-lg">{agent.icon}</span>
                    <div className={clsx('status-dot', agent.status)} />
                  </div>
                  <div className="text-xs font-medium text-slate-300 leading-tight">{agent.name}</div>
                  <div className="text-[10px] text-slate-600 mt-1 capitalize">{agent.status}</div>
                  {agent.current_task && (
                    <div className="text-[9px] text-brand-400 mt-1 truncate">{agent.current_task}</div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* ─── Live Activity Feed ─────────────────────────────── */}
          <div className="glass-card p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <Zap size={16} className="text-amber-400" /> Live Activity
              </h2>
              <Link href="/activity" className="text-xs text-brand-400 hover:text-brand-300">
                All <ChevronRight size={12} className="inline" />
              </Link>
            </div>
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {events.length === 0 ? (
                <div className="text-center py-8 text-slate-600 text-xs">
                  <Bot size={24} className="mx-auto mb-2 opacity-30" />
                  No activity yet. Start a demo!
                </div>
              ) : events.slice(0, 15).map((ev) => (
                <div key={ev.id} className="activity-item pb-3">
                  <div className="text-xs text-slate-300 leading-tight">{ev.message}</div>
                  <div className="text-[10px] text-slate-600 mt-0.5">
                    {ev.agent_name && <span className="text-brand-500">{ev.agent_name} · </span>}
                    {new Date(ev.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ─── Demo Launcher ─────────────────────────────────────── */}
        <div className="glass-card p-6">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center glow-purple">
              <Zap size={20} className="text-white" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-slate-200">🚀 One-Click Autonomous Company Demo</h2>
              <p className="text-xs text-slate-500">Watch 9 AI agents build a complete production system end-to-end</p>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
            {[
              { key: 'customer_support', label: 'AI Customer Support', desc: 'RAG + citations + escalation', icon: '🎧' },
              { key: 'ecommerce', label: 'E-Commerce Platform', desc: 'Cart + payments + AI recs', icon: '🛍️' },
              { key: 'analytics', label: 'Analytics Dashboard', desc: 'Real-time insights + forecasting', icon: '📊' },
              { key: 'saas', label: 'SaaS Platform', desc: 'Multi-tenant + billing + RBAC', icon: '⚡' },
            ].map(({ key, label, desc, icon }) => (
              <button
                key={key}
                onClick={() => startDemo(key)}
                disabled={!!demoLoading}
                className={clsx(
                  'p-4 rounded-xl border text-left transition-all duration-200 group',
                  demoLoading === key
                    ? 'border-brand-500/50 bg-brand-500/10'
                    : 'border-white/10 bg-white/3 hover:border-brand-500/40 hover:bg-brand-500/5'
                )}
              >
                <div className="text-2xl mb-2">{icon}</div>
                <div className="text-xs font-semibold text-slate-200 mb-1">{label}</div>
                <div className="text-[11px] text-slate-500">{desc}</div>
                {demoLoading === key ? (
                  <div className="flex items-center gap-1 mt-3 text-brand-400 text-[11px]">
                    <div className="typing-dots"><span/><span/><span/></div>
                    <span>Starting...</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-1 mt-3 text-brand-400 text-[11px] opacity-0 group-hover:opacity-100 transition-opacity">
                    <Play size={10} /> Start demo
                  </div>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* ─── Recent Projects ────────────────────────────────────── */}
        {projects.length > 0 && (
          <div className="glass-card p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <FolderKanban size={16} className="text-brand-400" /> Recent Projects
              </h2>
              <Link href="/projects" className="text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1">
                All projects <ArrowRight size={12} />
              </Link>
            </div>
            <div className="space-y-2">
              {projects.slice(0, 5).map((p) => (
                <Link
                  key={p.id}
                  href={`/projects/${p.id}`}
                  className="flex items-center gap-4 p-3 rounded-xl hover:bg-white/5 transition-all group"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-medium text-slate-200 truncate">{p.name}</span>
                      {p.is_demo && <span className="text-[9px] px-1.5 py-0.5 bg-brand-500/20 text-brand-400 rounded-full border border-brand-500/30">DEMO</span>}
                    </div>
                    <div className="progress-bar w-full mb-1">
                      <div className="progress-fill" style={{ width: `${p.progress_percent}%` }} />
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={clsx('text-[10px] px-1.5 py-0.5 rounded-full', statusColor[p.status] || 'badge-idle')}>{p.status}</span>
                      <span className="text-[10px] text-slate-600">${p.actual_cost_usd.toFixed(4)} spent</span>
                    </div>
                  </div>
                  <ChevronRight size={14} className="text-slate-600 group-hover:text-brand-400 transition-colors flex-shrink-0" />
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
