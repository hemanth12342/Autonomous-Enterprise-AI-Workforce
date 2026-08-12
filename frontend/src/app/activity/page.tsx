'use client';
import DashboardLayout from '@/components/DashboardLayout';
import { useStore } from '@/store';
import { useState } from 'react';
import clsx from 'clsx';
import { Bot, Zap, Search, Filter } from 'lucide-react';

const EVENT_COLORS: Record<string, string> = {
  agent_started:         'text-brand-400',
  agent_thinking:        'text-cyan-400',
  agent_completed:       'text-emerald-400',
  agent_failed:          'text-red-400',
  agent_escalated:       'text-amber-400',
  guardrail_violation:   'text-red-500',
  demo_started:          'text-purple-400',
  demo_completed:        'text-emerald-400',
  approval_required:     'text-amber-400',
  approval_decision:     'text-emerald-400',
  deployment_complete:   'text-emerald-400',
  qa_report_ready:       'text-teal-400',
  security_scan_complete:'text-amber-400',
  ceo_analysis_complete: 'text-purple-400',
  pm_plan_created:       'text-violet-400',
  developer_code_written:'text-cyan-400',
};

const EVENT_ICONS: Record<string, string> = {
  agent_started:        '▶',
  agent_thinking:       '💭',
  agent_completed:      '✅',
  agent_failed:         '❌',
  approval_required:    '🔐',
  approval_decision:    '👤',
  deployment_complete:  '🚀',
  guardrail_violation:  '🛡️',
  demo_started:         '⚡',
  security_scan_complete:'🔒',
};

export default function ActivityPage() {
  const { events, clearEvents } = useStore();
  const [search, setSearch] = useState('');
  const [filterAgent, setFilterAgent] = useState('all');

  const agentTypes = ['all', ...Array.from(new Set(events.map(e => e.agent_type || 'system').filter(Boolean)))];

  const filtered = events
    .filter(e => filterAgent === 'all' || (e.agent_type || 'system') === filterAgent)
    .filter(e => !search || e.message.toLowerCase().includes(search.toLowerCase()));

  return (
    <DashboardLayout title="Activity Feed">
      <div className="space-y-4">
        {/* ─── Controls ─────────────────────────────────────────── */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-48">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search events..."
              className="w-full pl-9 pr-3 py-2 text-xs rounded-lg bg-white/5 border border-white/10 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-brand-500/50"
            />
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            {agentTypes.map((type) => (
              <button
                key={type}
                onClick={() => setFilterAgent(type)}
                className={clsx(
                  'px-3 py-1.5 rounded-lg text-xs font-medium transition-all capitalize',
                  filterAgent === type
                    ? 'bg-brand-500/20 text-brand-300 border border-brand-500/30'
                    : 'bg-white/5 text-slate-500 hover:bg-white/10 hover:text-slate-400'
                )}
              >
                {type}
              </button>
            ))}
          </div>
          <div className="ml-auto flex items-center gap-2">
            <span className="text-xs text-slate-500">{filtered.length} events</span>
            {events.length > 0 && (
              <button
                onClick={clearEvents}
                className="px-3 py-1.5 text-xs rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 hover:bg-red-500/20 transition-all"
              >
                Clear
              </button>
            )}
          </div>
        </div>

        {/* ─── Live Indicator ────────────────────────────────────── */}
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
          <span>Live stream · {filtered.length} events</span>
        </div>

        {/* ─── Timeline ──────────────────────────────────────────── */}
        <div className="glass-card p-5">
          {filtered.length === 0 ? (
            <div className="text-center py-16">
              <Zap size={36} className="mx-auto mb-3 text-slate-600" />
              <p className="text-slate-500 text-sm">No events yet</p>
              <p className="text-slate-600 text-xs mt-1">Start a demo from the Dashboard to see agent activity</p>
            </div>
          ) : (
            <div className="space-y-0">
              {filtered.map((event, i) => (
                <div
                  key={event.id}
                  className={clsx(
                    'relative pl-8 pb-4',
                    i < filtered.length - 1 && 'border-l border-brand-500/10'
                  )}
                >
                  {/* Timeline dot */}
                  <div className="absolute left-0 top-1 w-6 h-6 -translate-x-1/2 rounded-full bg-surface-2 border border-brand-500/20 flex items-center justify-center text-[11px]">
                    {EVENT_ICONS[event.event_type] || '●'}
                  </div>

                  <div className="hover:bg-white/3 -mx-4 px-4 py-2 rounded-lg transition-colors">
                    <div className="flex items-center gap-2 mb-0.5">
                      {event.agent_name && (
                        <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-brand-500/10 text-brand-400">
                          {event.agent_name}
                        </span>
                      )}
                      <span className={clsx('text-[10px] font-mono uppercase', EVENT_COLORS[event.event_type] || 'text-slate-500')}>
                        {event.event_type.replace(/_/g, ' ')}
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed">{event.message}</p>
                    {event.data && Object.keys(event.data).length > 0 && (
                      <div className="mt-1.5 p-2 rounded bg-black/20 border border-white/5">
                        <pre className="text-[10px] text-slate-500 font-mono overflow-x-auto max-h-20">
                          {JSON.stringify(event.data, null, 2).slice(0, 400)}
                        </pre>
                      </div>
                    )}
                    <div className="text-[10px] text-slate-600 mt-1">
                      {new Date(event.timestamp).toLocaleTimeString()} · {new Date(event.timestamp).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
