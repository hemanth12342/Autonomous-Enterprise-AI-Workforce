'use client';
import DashboardLayout from '@/components/DashboardLayout';
import { useEffect, useState } from 'react';
import { costsApi } from '@/lib/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { DollarSign, TrendingUp, Cpu } from 'lucide-react';

const COLORS = ['#6366f1', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#a855f7', '#84cc16', '#f97316', '#a78bfa'];

export default function CostsPage() {
  const [summary, setSummary] = useState<any>(null);
  const [byAgent, setByAgent] = useState<any[]>([]);
  const [byModel, setByModel] = useState<any[]>([]);

  useEffect(() => {
    Promise.allSettled([costsApi.summary(), costsApi.byAgent(), costsApi.byModel()]).then(([s, a, m]) => {
      if (s.status === 'fulfilled') setSummary(s.value);
      if (a.status === 'fulfilled') setByAgent(a.value);
      if (m.status === 'fulfilled') setByModel(m.value);
    });
  }, []);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null;
    return (
      <div className="glass-card px-3 py-2 text-xs">
        <div className="text-slate-300 font-medium mb-1">{label}</div>
        {payload.map((p: any) => (
          <div key={p.name} style={{ color: p.color }}>${p.value?.toFixed(6)}</div>
        ))}
      </div>
    );
  };

  return (
    <DashboardLayout title="Cost Monitor">
      <div className="space-y-6">
        {/* ─── KPIs ─────────────────────────────────────────────── */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[
            { label: 'Total LLM Cost', value: `$${(summary?.total_cost_usd || 0).toFixed(6)}`, icon: DollarSign, color: '#6366f1' },
            { label: 'Total Tokens', value: (summary?.total_tokens || 0).toLocaleString(), icon: Cpu, color: '#06b6d4' },
            { label: 'LLM API Calls', value: (summary?.total_llm_calls || 0).toLocaleString(), icon: TrendingUp, color: '#10b981' },
          ].map(({ label, value, icon: Icon, color }) => (
            <div key={label} className="glass-card p-5">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ background: `${color}20`, border: `1px solid ${color}40` }}>
                  <Icon size={18} style={{ color }} />
                </div>
                <span className="text-xs text-slate-500">{label}</span>
              </div>
              <div className="text-2xl font-bold text-slate-100">{value}</div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {/* ─── Cost by Agent ─────────────────────────────────── */}
          <div className="glass-card p-5">
            <h3 className="text-sm font-semibold text-slate-200 mb-4">Cost by Agent</h3>
            {byAgent.length === 0 ? (
              <div className="h-48 flex items-center justify-center text-slate-600 text-xs">No cost data yet. Run a demo.</div>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={byAgent}>
                  <XAxis dataKey="agent_type" tick={{ fontSize: 10, fill: '#64748b' }} />
                  <YAxis tick={{ fontSize: 10, fill: '#64748b' }} tickFormatter={(v) => `$${v.toFixed(4)}`} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="cost_usd" radius={[4, 4, 0, 0]}>
                    {byAgent.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* ─── Cost by Model ─────────────────────────────────── */}
          <div className="glass-card p-5">
            <h3 className="text-sm font-semibold text-slate-200 mb-4">Cost by Model</h3>
            {byModel.length === 0 ? (
              <div className="h-48 flex items-center justify-center text-slate-600 text-xs">No model data yet.</div>
            ) : (
              <div className="flex items-center gap-6">
                <ResponsiveContainer width="50%" height={200}>
                  <PieChart>
                    <Pie data={byModel} dataKey="cost_usd" nameKey="model" cx="50%" cy="50%" innerRadius={50} outerRadius={80}>
                      {byModel.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
                <div className="space-y-2">
                  {byModel.map((m, i) => (
                    <div key={m.model} className="flex items-center gap-2">
                      <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: COLORS[i % COLORS.length] }} />
                      <span className="text-xs text-slate-400 font-mono truncate max-w-28">{m.model}</span>
                      <span className="text-xs font-semibold ml-auto" style={{ color: COLORS[i % COLORS.length] }}>${m.cost_usd?.toFixed(6)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ─── Cost Efficiency Info ──────────────────────────────── */}
        <div className="glass-card p-5">
          <h3 className="text-sm font-semibold text-slate-200 mb-3">💡 Cost Efficiency</h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs text-slate-400">
            <div className="p-3 rounded-lg bg-white/3 border border-white/5">
              <div className="font-semibold text-emerald-400 mb-1">Smart Model Routing</div>
              Simple tasks (docs, summaries) use fast/cheap models. Complex reasoning uses premium models.
            </div>
            <div className="p-3 rounded-lg bg-white/3 border border-white/5">
              <div className="font-semibold text-brand-400 mb-1">Per-task Budget</div>
              Each agent has a cost budget. If exceeded, it escalates to human instead of over-spending.
            </div>
            <div className="p-3 rounded-lg bg-white/3 border border-white/5">
              <div className="font-semibold text-amber-400 mb-1">Real-time Tracking</div>
              Every LLM call logs prompt tokens, completion tokens, model, provider, and cost.
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
