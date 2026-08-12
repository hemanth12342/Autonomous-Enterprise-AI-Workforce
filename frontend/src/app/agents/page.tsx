'use client';
import DashboardLayout from '@/components/DashboardLayout';
import { useStore } from '@/store';
import { useEffect, useState } from 'react';
import { agentsApi } from '@/lib/api';
import clsx from 'clsx';
import { CheckCircle2, XCircle, TrendingUp, DollarSign, Clock } from 'lucide-react';

const CAPABILITY_COLORS: Record<string, string> = {
  code_generation: '#06b6d4', github_operations: '#6366f1', bug_fixing: '#f59e0b',
  sast: '#ef4444', secret_detection: '#ef4444', test_generation: '#10b981',
  docker_build: '#f97316', kubernetes_deploy: '#f97316', monitoring: '#f97316',
  strategic_analysis: '#a855f7', delegation: '#a855f7', task_planning: '#8b5cf6',
};

export default function AgentsPage() {
  const { agents, setAgents } = useStore();
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    agentsApi.list().then((data) => { setAgents(data); setLoading(false); }).catch(() => setLoading(false));
  }, [setAgents]);

  const selectedAgent = agents.find((a) => a.agent_type === selected);

  return (
    <DashboardLayout title="AI Agents">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-100">AI Workforce</h2>
            <p className="text-xs text-slate-500 mt-0.5">9 specialized AI agents, each an expert in their domain</p>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 text-xs text-emerald-400">
              <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
              {agents.filter(a => a.status === 'working').length} active
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
          {loading ? Array.from({ length: 9 }).map((_, i) => (
            <div key={i} className="glass-card p-5 h-40 animate-pulse" />
          )) : agents.map((agent) => (
            <div
              key={agent.agent_type}
              onClick={() => setSelected(selected === agent.agent_type ? null : agent.agent_type)}
              className={clsx(
                'glass-card p-5 agent-card cursor-pointer transition-all duration-300',
                selected === agent.agent_type
                  ? 'border-brand-500/50 shadow-lg shadow-brand-500/10'
                  : 'glass-card-hover'
              )}
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div
                    className="w-11 h-11 rounded-xl flex items-center justify-center text-2xl"
                    style={{ background: `${agent.color}20`, border: `1px solid ${agent.color}40` }}
                  >
                    {agent.icon}
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-slate-200">{agent.name}</div>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      <div className={clsx('status-dot', agent.status)} />
                      <span className="text-[11px] text-slate-500 capitalize">{agent.status}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Description */}
              <p className="text-[11px] text-slate-500 mb-3 leading-relaxed">{agent.description}</p>

              {/* Current task */}
              {agent.current_task && (
                <div className="px-2.5 py-1.5 rounded-lg bg-brand-500/10 border border-brand-500/20 mb-3">
                  <div className="flex items-center gap-1.5">
                    <div className="typing-dots"><span /><span /><span /></div>
                    <span className="text-[11px] text-brand-400 truncate">{agent.current_task}</span>
                  </div>
                </div>
              )}

              {/* Stats */}
              <div className="grid grid-cols-3 gap-2">
                <div className="text-center">
                  <div className="text-sm font-bold text-emerald-400">{agent.tasks_completed}</div>
                  <div className="text-[10px] text-slate-600">Done</div>
                </div>
                <div className="text-center">
                  <div className="text-sm font-bold text-red-400">{agent.tasks_failed}</div>
                  <div className="text-[10px] text-slate-600">Failed</div>
                </div>
                <div className="text-center">
                  <div className="text-sm font-bold text-amber-400">${agent.total_cost_usd.toFixed(3)}</div>
                  <div className="text-[10px] text-slate-600">Cost</div>
                </div>
              </div>

              {/* Capabilities */}
              {selected === agent.agent_type && (
                <div className="mt-3 pt-3 border-t border-white/5 animate-fade-in">
                  <div className="text-[10px] text-slate-500 mb-2 font-medium uppercase tracking-wider">Capabilities</div>
                  <div className="flex flex-wrap gap-1.5">
                    {agent.capabilities?.map((cap: string) => (
                      <span
                        key={cap}
                        className="px-2 py-0.5 rounded-full text-[10px] font-medium"
                        style={{
                          background: `${CAPABILITY_COLORS[cap] || '#6366f1'}20`,
                          color: CAPABILITY_COLORS[cap] || '#818cf8',
                          border: `1px solid ${CAPABILITY_COLORS[cap] || '#6366f1'}30`,
                        }}
                      >
                        {cap.replace(/_/g, ' ')}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
}
