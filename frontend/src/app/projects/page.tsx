'use client';
import DashboardLayout from '@/components/DashboardLayout';
import { useStore } from '@/store';
import { useEffect, useState } from 'react';
import { projectsApi, demoApi } from '@/lib/api';
import { toast } from 'sonner';
import Link from 'next/link';
import {
  Plus, FolderKanban, Play, ExternalLink,
  Clock, CheckCircle2, AlertTriangle, Loader2
} from 'lucide-react';
import clsx from 'clsx';

const STATUS_STYLE: Record<string, { label: string; class: string; icon: any }> = {
  draft:              { label: 'Draft',          class: 'badge-idle',     icon: Clock },
  planning:           { label: 'Planning',       class: 'badge-running',  icon: Loader2 },
  active:             { label: 'Active',         class: 'badge-working',  icon: Loader2 },
  awaiting_approval:  { label: 'Needs Approval', class: 'badge-approval', icon: AlertTriangle },
  completed:          { label: 'Completed',      class: 'badge-success',  icon: CheckCircle2 },
  failed:             { label: 'Failed',         class: 'badge-failed',   icon: AlertTriangle },
};

export default function ProjectsPage() {
  const { projects, setProjects, addProject } = useStore();
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ name: '', business_objective: '', budget_usd: 5 });
  const [creating, setCreating] = useState(false);
  const [starting, setStarting] = useState<string | null>(null);

  useEffect(() => {
    projectsApi.list().then((data) => { setProjects(data); setLoading(false); }).catch(() => setLoading(false));
  }, [setProjects]);

  const createProject = async () => {
    if (!form.name || !form.business_objective) return toast.error('Fill all fields');
    setCreating(true);
    try {
      const p = await projectsApi.create(form);
      addProject(p);
      setShowCreate(false);
      setForm({ name: '', business_objective: '', budget_usd: 5 });
      toast.success('Project created!');
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Failed to create');
    } finally { setCreating(false); }
  };

  const startProject = async (id: string) => {
    setStarting(id);
    try {
      await projectsApi.start(id);
      toast.success('🚀 AI Workforce started!');
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Failed to start');
    } finally { setStarting(null); }
  };

  return (
    <DashboardLayout title="Projects">
      <div className="space-y-5">
        {/* ─── Header ─────────────────────────────────────────────── */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-slate-500">Each project triggers the full 9-agent AI workforce</p>
          </div>
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-brand-500/20 border border-brand-500/30 text-brand-300 hover:bg-brand-500/30 transition-all text-sm font-medium"
          >
            <Plus size={16} /> New Project
          </button>
        </div>

        {/* ─── Create Form ────────────────────────────────────────── */}
        {showCreate && (
          <div className="glass-card p-5 border-brand-500/30 animate-slide-up">
            <h3 className="text-sm font-semibold text-slate-200 mb-4">New Project</h3>
            <div className="space-y-3">
              <input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="Project name (e.g. 'Customer Support AI')"
                className="w-full px-3 py-2.5 text-sm rounded-xl bg-white/5 border border-white/10 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-brand-500/50"
              />
              <textarea
                value={form.business_objective}
                onChange={(e) => setForm({ ...form, business_objective: e.target.value })}
                rows={3}
                placeholder="Business objective — describe what you want the AI to build..."
                className="w-full px-3 py-2.5 text-sm rounded-xl bg-white/5 border border-white/10 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-brand-500/50 resize-none"
              />
              <div className="flex items-center gap-3">
                <label className="text-xs text-slate-400">Budget: $</label>
                <input
                  type="number"
                  value={form.budget_usd}
                  onChange={(e) => setForm({ ...form, budget_usd: Number(e.target.value) })}
                  className="w-24 px-3 py-2 text-sm rounded-lg bg-white/5 border border-white/10 text-slate-200 focus:outline-none"
                />
              </div>
              <div className="flex gap-3">
                <button
                  onClick={createProject}
                  disabled={creating}
                  className="px-5 py-2 rounded-xl bg-brand-500/20 border border-brand-500/30 text-brand-300 hover:bg-brand-500/30 transition-all text-sm font-medium flex items-center gap-2"
                >
                  {creating ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />}
                  Create Project
                </button>
                <button
                  onClick={() => setShowCreate(false)}
                  className="px-5 py-2 rounded-xl bg-white/5 border border-white/10 text-slate-400 hover:bg-white/10 transition-all text-sm"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ─── Projects Grid ──────────────────────────────────────── */}
        {loading ? (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
            {[1,2,3].map(i => <div key={i} className="glass-card h-48 animate-pulse" />)}
          </div>
        ) : projects.length === 0 ? (
          <div className="glass-card p-16 text-center">
            <FolderKanban size={40} className="mx-auto mb-3 text-slate-600" />
            <p className="text-slate-400 text-sm">No projects yet</p>
            <p className="text-slate-600 text-xs mt-1">Create a project or run a demo from the Dashboard</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
            {projects.map((p) => {
              const st = STATUS_STYLE[p.status] || STATUS_STYLE.draft;
              const StatusIcon = st.icon;
              return (
                <div key={p.id} className="glass-card p-5 glass-card-hover">
                  {/* Header */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1 min-w-0 mr-3">
                      <div className="flex items-center gap-2 mb-1">
                        <Link href={`/projects/${p.id}`} className="text-sm font-semibold text-slate-200 hover:text-brand-300 transition-colors truncate">
                          {p.name}
                        </Link>
                        {p.is_demo && (
                          <span className="px-1.5 py-0.5 text-[9px] font-bold bg-brand-500/10 text-brand-400 border border-brand-500/20 rounded-full flex-shrink-0">DEMO</span>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-500 line-clamp-2 leading-relaxed">{p.business_objective}</p>
                    </div>
                    <span className={clsx('px-2 py-1 rounded-full text-[10px] font-medium flex items-center gap-1 flex-shrink-0', st.class)}>
                      <StatusIcon size={10} className={p.status === 'planning' || p.status === 'active' ? 'animate-spin' : ''} />
                      {st.label}
                    </span>
                  </div>

                  {/* Progress */}
                  <div className="mb-3">
                    <div className="flex justify-between text-[10px] text-slate-500 mb-1">
                      <span>{p.completed_tasks}/{p.total_tasks} tasks</span>
                      <span>{p.progress_percent}%</span>
                    </div>
                    <div className="progress-bar">
                      <div className="progress-fill" style={{ width: `${p.progress_percent}%` }} />
                    </div>
                  </div>

                  {/* Stats */}
                  <div className="flex items-center gap-4 text-[11px] mb-4">
                    <span className="text-slate-500">💰 ${p.actual_cost_usd.toFixed(4)}</span>
                    <span className="text-slate-500">📅 {new Date(p.created_at).toLocaleDateString()}</span>
                    {p.deployment_url && (
                      <a href={p.deployment_url} target="_blank" className="text-brand-400 hover:text-brand-300 flex items-center gap-1">
                        <ExternalLink size={10} /> Live
                      </a>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2">
                    <Link
                      href={`/projects/${p.id}`}
                      className="flex-1 py-2 rounded-lg bg-white/5 border border-white/10 text-xs text-slate-400 hover:text-slate-200 hover:bg-white/10 text-center transition-all"
                    >
                      View Details
                    </Link>
                    {p.status === 'draft' && (
                      <button
                        onClick={() => startProject(p.id)}
                        disabled={starting === p.id}
                        className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-brand-500/20 border border-brand-500/30 text-brand-400 hover:bg-brand-500/30 transition-all text-xs font-medium"
                      >
                        {starting === p.id ? <Loader2 size={12} className="animate-spin" /> : <Play size={12} />}
                        Start AI
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
