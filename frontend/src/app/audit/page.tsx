'use client';
import DashboardLayout from '@/components/DashboardLayout';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Search, FileText } from 'lucide-react';
import clsx from 'clsx';

const SEVERITY_COLORS: Record<string, string> = {
  info:     'text-slate-400',
  warning:  'text-amber-400',
  error:    'text-red-400',
  critical: 'text-red-300',
};

const ACTOR_COLORS: Record<string, string> = {
  'CEO Agent':           '#6366f1',
  'Project Manager':     '#8b5cf6',
  'Developer Agent':     '#06b6d4',
  'QA Agent':            '#10b981',
  'Security Agent':      '#f59e0b',
  'DevOps Agent':        '#ef4444',
  'Documentation Agent': '#84cc16',
  'Research Agent':      '#a78bfa',
  'System':              '#64748b',
};

export default function AuditPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    api.get('/audit/').then((r) => { setLogs(r.data); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  const filtered = logs.filter(l =>
    !search ||
    l.action?.toLowerCase().includes(search.toLowerCase()) ||
    l.actor?.toLowerCase().includes(search.toLowerCase()) ||
    l.resource_type?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <DashboardLayout title="Audit Log">
      <div className="space-y-5">
        {/* ─── Search ─────────────────────────────────────────────── */}
        <div className="flex items-center gap-3">
          <div className="relative flex-1 max-w-sm">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search audit logs..."
              className="w-full pl-9 pr-3 py-2 text-xs rounded-lg bg-white/5 border border-white/10 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-brand-500/50"
            />
          </div>
          <span className="text-xs text-slate-500">{filtered.length} entries</span>
        </div>

        {/* ─── Table ──────────────────────────────────────────────── */}
        <div className="glass-card overflow-hidden">
          {loading ? (
            <div className="p-8 text-center text-slate-600 text-xs">Loading audit log...</div>
          ) : filtered.length === 0 ? (
            <div className="p-16 text-center">
              <FileText size={36} className="mx-auto mb-3 text-slate-600" />
              <p className="text-slate-500 text-sm">No audit records yet</p>
              <p className="text-slate-600 text-xs mt-1">Every agent action is recorded here</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-white/5">
                    {['Timestamp', 'Actor', 'Action', 'Resource', 'Result', 'Severity'].map((h) => (
                      <th key={h} className="px-4 py-3 text-left text-[10px] font-medium text-slate-500 uppercase tracking-wider">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/3">
                  {filtered.map((log) => (
                    <tr key={log.id} className="hover:bg-white/3 transition-colors">
                      <td className="px-4 py-3 font-mono text-slate-600 whitespace-nowrap">
                        {new Date(log.created_at).toLocaleString()}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className="px-2 py-0.5 rounded-full text-[10px] font-medium"
                          style={{
                            color: ACTOR_COLORS[log.actor] || '#94a3b8',
                            background: `${ACTOR_COLORS[log.actor] || '#64748b'}20`,
                          }}
                        >
                          {log.actor}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-300">{log.action}</td>
                      <td className="px-4 py-3 text-slate-500">{log.resource_type}</td>
                      <td className="px-4 py-3">
                        <span className={clsx('font-medium', log.result === 'success' ? 'text-emerald-400' : 'text-red-400')}>
                          {log.result}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={clsx('capitalize font-medium text-[10px]', SEVERITY_COLORS[log.severity] || 'text-slate-400')}>
                          {log.severity}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
