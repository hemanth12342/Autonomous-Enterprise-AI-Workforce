'use client';
import DashboardLayout from '@/components/DashboardLayout';
import { useEffect, useState } from 'react';
import { projectsApi } from '@/lib/api';
import { useParams } from 'next/navigation';
import { useProjectWebSocket } from '@/hooks/useWebSocket';
import { useStore } from '@/store';
import Link from 'next/link';
import {
  ArrowLeft, ExternalLink, CheckCircle2, AlertTriangle,
  Clock, Loader2, Bot, FileText, ShieldCheck, Rocket
} from 'lucide-react';
import clsx from 'clsx';

const AGENT_ICONS: Record<string, string> = {
  ceo: '🧠', project_manager: '📋', developer: '💻', qa: '🧪',
  security: '🔒', devops: '🚀', documentation: '📚', research: '🔬', support: '🎧',
};

const TASK_STATUS_STYLE: Record<string, string> = {
  pending:   'badge-idle',
  running:   'badge-working',
  completed: 'badge-success',
  failed:    'badge-failed',
  cancelled: 'badge-idle',
};

export default function ProjectDetailPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [project, setProject] = useState<any>(null);
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const { events } = useStore();

  useProjectWebSocket(projectId);

  useEffect(() => {
    (async () => {
      try {
        const p = await projectsApi.get(projectId);
        setProject(p);
        setTasks(p.tasks || []);
      } catch {}
      finally { setLoading(false); }
    })();
  }, [projectId]);

  // Refresh tasks on events
  useEffect(() => {
    const lastEvent = events[0];
    if (lastEvent?.project_id === projectId) {
      projectsApi.get(projectId).then((p) => {
        setProject(p);
        setTasks(p.tasks || []);
      }).catch(() => {});
    }
  }, [events, projectId]);

  const projectEvents = events.filter(e => e.project_id === projectId);

  if (loading) {
    return (
      <DashboardLayout title="Project">
        <div className="flex items-center justify-center h-64">
          <Loader2 size={24} className="animate-spin text-brand-400" />
        </div>
      </DashboardLayout>
    );
  }

  if (!project) {
    return (
      <DashboardLayout title="Project Not Found">
        <div className="text-center py-16">
          <p className="text-slate-500">Project not found</p>
          <Link href="/projects" className="text-brand-400 text-sm mt-2 inline-block">← Back to projects</Link>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title={project.name}>
      <div className="space-y-5">
        {/* ─── Back + Header ──────────────────────────────────────── */}
        <div className="flex items-center gap-4">
          <Link href="/projects" className="text-slate-400 hover:text-slate-200 transition-colors">
            <ArrowLeft size={20} />
          </Link>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3">
              <h2 className="text-lg font-bold text-slate-100 truncate">{project.name}</h2>
              {project.is_demo && (
                <span className="px-2 py-0.5 text-[10px] font-bold bg-brand-500/10 text-brand-400 border border-brand-500/20 rounded-full">DEMO</span>
              )}
              <span className={clsx('px-2 py-0.5 text-[10px] font-medium rounded-full', TASK_STATUS_STYLE[project.status] || 'badge-idle')}>
                {project.status?.toUpperCase()}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5 line-clamp-1">{project.business_objective}</p>
          </div>
          {project.deployment_url && (
            <a href={project.deployment_url} target="_blank"
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 hover:bg-emerald-500/20 transition-all text-sm font-medium">
              <ExternalLink size={14} /> Live App
            </a>
          )}
        </div>

        {/* ─── Progress Bar ────────────────────────────────────────── */}
        <div className="glass-card p-5">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
            <span>Project Progress</span>
            <span>{project.progress_percent}% — {project.completed_tasks}/{project.total_tasks} tasks</span>
          </div>
          <div className="progress-bar mb-4" style={{ height: '8px' }}>
            <div className="progress-fill" style={{ width: `${project.progress_percent}%`, height: '8px' }} />
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {[
              { label: 'Tasks Done', value: project.completed_tasks, color: '#10b981' },
              { label: 'Total Tasks', value: project.total_tasks, color: '#6366f1' },
              { label: 'Cost (USD)', value: `$${project.actual_cost_usd?.toFixed(4) || '0.0000'}`, color: '#a855f7' },
              { label: 'Budget', value: `$${project.budget_usd?.toFixed(2) || '5.00'}`, color: '#f59e0b' },
            ].map(({ label, value, color }) => (
              <div key={label}>
                <div className="text-lg font-bold" style={{ color }}>{value}</div>
                <div className="text-[10px] text-slate-600">{label}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
          {/* ─── Task DAG ────────────────────────────────────────── */}
          <div className="xl:col-span-2 glass-card p-5">
            <h3 className="text-sm font-semibold text-slate-200 mb-4 flex items-center gap-2">
              <Bot size={16} className="text-brand-400" /> Agent Task Pipeline
            </h3>
            {tasks.length === 0 ? (
              <div className="text-center py-8 text-slate-600 text-xs">
                Tasks will appear here once the AI Workforce starts
              </div>
            ) : (
              <div className="space-y-2">
                {tasks.map((task, i) => (
                  <div
                    key={task.id}
                    className={clsx(
                      'flex items-start gap-3 p-3 rounded-xl border transition-all',
                      task.status === 'running' ? 'border-brand-500/40 bg-brand-500/5' :
                      task.status === 'completed' ? 'border-emerald-500/20 bg-emerald-500/3' :
                      task.status === 'failed' ? 'border-red-500/20 bg-red-500/3' :
                      'border-white/5 bg-white/2'
                    )}
                  >
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <span className="text-[10px] font-mono text-slate-600 w-6 text-right">{i + 1}</span>
                      <div className="text-lg">{AGENT_ICONS[task.assigned_agent_type] || '🤖'}</div>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="text-xs font-medium text-slate-200 truncate">{task.title}</span>
                        {task.requires_approval && (
                          <span className="text-[9px] px-1.5 py-0.5 bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded-full flex-shrink-0">APPROVAL</span>
                        )}
                        {task.can_run_parallel && (
                          <span className="text-[9px] px-1.5 py-0.5 bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 rounded-full flex-shrink-0">PARALLEL</span>
                        )}
                      </div>
                      <div className="text-[10px] text-slate-500">{task.assigned_agent_type} · {task.task_type?.replace(/_/g, ' ')}</div>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {task.status === 'running' && <Loader2 size={14} className="text-brand-400 animate-spin" />}
                      {task.status === 'completed' && <CheckCircle2 size={14} className="text-emerald-400" />}
                      {task.status === 'failed' && <AlertTriangle size={14} className="text-red-400" />}
                      <span className={clsx('text-[10px] px-1.5 py-0.5 rounded-full', TASK_STATUS_STYLE[task.status])}>
                        {task.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* ─── Project Activity ────────────────────────────────── */}
          <div className="glass-card p-5">
            <h3 className="text-sm font-semibold text-slate-200 mb-4 flex items-center gap-2">
              <Clock size={16} className="text-brand-400" /> Live Events
            </h3>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {projectEvents.length === 0 ? (
                <div className="text-center py-8 text-slate-600 text-xs">No events yet</div>
              ) : projectEvents.map((ev) => (
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

        {/* ─── Final Report ─────────────────────────────────────────── */}
        {project.final_report && (
          <div className="glass-card p-5">
            <h3 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
              <FileText size={16} className="text-emerald-400" /> Executive Report
            </h3>
            <div className="prose prose-sm prose-invert max-w-none">
              <pre className="whitespace-pre-wrap text-xs text-slate-400 leading-relaxed font-sans">
                {project.final_report}
              </pre>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
