'use client';
import DashboardLayout from '@/components/DashboardLayout';
import { useStore } from '@/store';
import { useEffect, useState } from 'react';
import { approvalsApi } from '@/lib/api';
import { toast } from 'sonner';
import { ShieldCheck, CheckCircle2, XCircle, MessageSquare, Clock, AlertTriangle } from 'lucide-react';
import clsx from 'clsx';

export default function ApprovalsPage() {
  const { approvals, setApprovals, updateApproval } = useStore();
  const [loading, setLoading] = useState(true);
  const [deciding, setDeciding] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'pending' | 'all'>('pending');

  useEffect(() => {
    approvalsApi.list('all')
      .then((data) => { setApprovals(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [setApprovals]);

  const decide = async (id: string, decision: string) => {
    setDeciding(id);
    try {
      await approvalsApi.decide(id, decision);
      updateApproval(id, { status: decision });
      toast.success(`Decision: ${decision}`);
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Failed to process decision');
    } finally { setDeciding(null); }
  };

  const filtered = activeTab === 'pending'
    ? approvals.filter((a) => a.status === 'pending')
    : approvals;

  const riskColors: Record<string, string> = {
    low: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
    medium: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
    high: 'text-red-400 bg-red-500/10 border-red-500/20',
    critical: 'text-red-300 bg-red-500/20 border-red-400/40',
  };

  return (
    <DashboardLayout title="Approvals — Human-in-the-Loop">
      <div className="space-y-6">
        {/* ─── Header ─────────────────────────────────────────────── */}
        <div className="glass-card p-5">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
              <ShieldCheck size={24} className="text-amber-400" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-100">Deployment Approval Gate</h2>
              <p className="text-xs text-slate-500 mt-0.5">
                AI agents pause here. Humans review and approve or reject production deployments.
              </p>
            </div>
            <div className="ml-auto flex items-center gap-3">
              <div className="text-center">
                <div className="text-2xl font-bold text-amber-400">{approvals.filter(a => a.status === 'pending').length}</div>
                <div className="text-[10px] text-slate-500">Pending</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-emerald-400">{approvals.filter(a => a.status === 'approved').length}</div>
                <div className="text-[10px] text-slate-500">Approved</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-400">{approvals.filter(a => a.status === 'rejected').length}</div>
                <div className="text-[10px] text-slate-500">Rejected</div>
              </div>
            </div>
          </div>
        </div>

        {/* ─── Tabs ───────────────────────────────────────────────── */}
        <div className="flex gap-2">
          {(['pending', 'all'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={clsx(
                'px-4 py-2 rounded-lg text-xs font-medium transition-all',
                activeTab === tab
                  ? 'bg-brand-500/20 text-brand-300 border border-brand-500/30'
                  : 'bg-white/5 text-slate-400 hover:bg-white/10'
              )}
            >
              {tab === 'pending' ? `Pending (${approvals.filter(a => a.status === 'pending').length})` : 'All Approvals'}
            </button>
          ))}
        </div>

        {/* ─── Approvals List ─────────────────────────────────────── */}
        {loading ? (
          <div className="space-y-3">
            {[1,2].map(i => <div key={i} className="glass-card h-40 animate-pulse" />)}
          </div>
        ) : filtered.length === 0 ? (
          <div className="glass-card p-12 text-center">
            <CheckCircle2 size={40} className="mx-auto mb-3 text-emerald-400 opacity-50" />
            <p className="text-slate-400 text-sm">No {activeTab === 'pending' ? 'pending' : ''} approvals</p>
            <p className="text-slate-600 text-xs mt-1">
              {activeTab === 'pending' ? 'Start a demo to trigger an approval request.' : 'Approvals will appear here when agents need deployment authorization.'}
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {filtered.map((approval) => (
              <div key={approval.id} className={clsx(
                'glass-card p-5',
                approval.status === 'pending' && 'border-amber-500/30 shadow-lg shadow-amber-500/5'
              )}>
                {/* Top row */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center flex-shrink-0">
                      {approval.status === 'pending' ? (
                        <Clock size={18} className="text-amber-400" />
                      ) : approval.status === 'approved' ? (
                        <CheckCircle2 size={18} className="text-emerald-400" />
                      ) : (
                        <XCircle size={18} className="text-red-400" />
                      )}
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-slate-200">
                        {approval.action_description || `${approval.action_type} — Deploy to Production`}
                      </div>
                      <div className="text-[11px] text-slate-500 mt-0.5">
                        Requested by <span className="text-brand-400">{approval.requesting_agent} agent</span>
                        {' · '}{new Date(approval.created_at).toLocaleString()}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className={clsx('px-2 py-1 rounded-full text-[10px] font-medium border', riskColors[approval.risk_level] || riskColors.medium)}>
                      {approval.risk_level?.toUpperCase() || 'MEDIUM'} RISK
                    </span>
                    <span className={clsx('px-2 py-1 rounded-full text-[10px] font-medium',
                      approval.status === 'pending' ? 'badge-approval' :
                      approval.status === 'approved' ? 'badge-success' : 'badge-failed'
                    )}>
                      {approval.status?.toUpperCase()}
                    </span>
                  </div>
                </div>

                {/* Metrics */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
                  {[
                    { label: 'Files Changed', value: approval.files_changed ?? 'N/A', color: '#06b6d4' },
                    { label: 'Tests Passed', value: approval.tests_passed ?? 'N/A', color: '#10b981' },
                    { label: 'Security', value: approval.security_passed ? '✅ Cleared' : '⚠️ Issues', color: approval.security_passed ? '#10b981' : '#f59e0b' },
                    { label: 'Est. Cost', value: approval.estimated_cost_usd != null ? `$${approval.estimated_cost_usd.toFixed(4)}` : 'N/A', color: '#a855f7' },
                  ].map(({ label, value, color }) => (
                    <div key={label} className="p-2.5 rounded-lg bg-white/3 border border-white/5">
                      <div className="text-xs font-semibold" style={{ color }}>{String(value)}</div>
                      <div className="text-[10px] text-slate-600 mt-0.5">{label}</div>
                    </div>
                  ))}
                </div>

                {/* Summary */}
                {approval.summary && (
                  <div className="p-3 rounded-lg bg-white/3 border border-white/5 mb-4">
                    <p className="text-xs text-slate-400 leading-relaxed">{approval.summary}</p>
                  </div>
                )}

                {/* Actions for pending */}
                {approval.status === 'pending' && (
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => decide(approval.id, 'approved')}
                      disabled={!!deciding}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/30 transition-all text-xs font-medium disabled:opacity-50"
                    >
                      <CheckCircle2 size={14} />
                      {deciding === approval.id ? 'Processing...' : 'Approve Deployment'}
                    </button>
                    <button
                      onClick={() => decide(approval.id, 'rejected')}
                      disabled={!!deciding}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 hover:bg-red-500/20 transition-all text-xs font-medium disabled:opacity-50"
                    >
                      <XCircle size={14} /> Reject
                    </button>
                    <button
                      onClick={() => decide(approval.id, 'changes_requested')}
                      disabled={!!deciding}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-slate-400 hover:bg-white/10 transition-all text-xs font-medium disabled:opacity-50"
                    >
                      <MessageSquare size={14} /> Request Changes
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
