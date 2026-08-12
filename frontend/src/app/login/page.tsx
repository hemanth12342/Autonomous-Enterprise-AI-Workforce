'use client';
import { useState } from 'react';
import { authApi } from '@/lib/api';
import { useStore } from '@/store';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { Zap, Loader2, Eye, EyeOff } from 'lucide-react';

export default function LoginPage() {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [form, setForm] = useState({ email: '', username: '', full_name: '', password: '', org_name: 'Demo Organization' });
  const [loading, setLoading] = useState(false);
  const [showPw, setShowPw] = useState(false);
  const { setAuth } = useStore();
  const router = useRouter();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      let data;
      if (mode === 'login') {
        data = await authApi.login(form.email, form.password);
      } else {
        data = await authApi.register({ email: form.email, username: form.username, full_name: form.full_name, password: form.password, org_name: form.org_name });
      }
      setAuth({ id: data.user_id, username: data.username, email: form.email, role: data.role }, data.access_token);
      toast.success('Welcome to AI Workforce OS!');
      router.push('/dashboard');
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Authentication failed');
    } finally { setLoading(false); }
  };

  const inputCls = "w-full px-4 py-3 text-sm rounded-xl bg-white/5 border border-white/10 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-brand-500/50 focus:bg-white/8 transition-all";

  return (
    <div className="min-h-screen bg-surface-0 flex items-center justify-center p-4">
      {/* Background mesh */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-brand-500/5 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-600/5 rounded-full blur-3xl" />
      </div>

      <div className="w-full max-w-md relative">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center mx-auto mb-4 glow-purple">
            <Zap size={28} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold gradient-text">AI Workforce OS</h1>
          <p className="text-sm text-slate-500 mt-1">Autonomous Enterprise AI Platform</p>
        </div>

        {/* Card */}
        <div className="glass-card p-8">
          {/* Tabs */}
          <div className="flex gap-1 p-1 rounded-xl bg-white/5 mb-6">
            {(['login', 'register'] as const).map((m) => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`flex-1 py-2 text-sm rounded-lg font-medium transition-all capitalize ${
                  mode === m ? 'bg-brand-500/30 text-brand-300' : 'text-slate-500 hover:text-slate-400'
                }`}
              >
                {m === 'login' ? 'Sign In' : 'Register'}
              </button>
            ))}
          </div>

          <form onSubmit={submit} className="space-y-4">
            <div>
              <label className="text-xs text-slate-400 mb-1.5 block">Email</label>
              <input
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                placeholder="you@company.com"
                required
                className={inputCls}
              />
            </div>

            {mode === 'register' && (
              <>
                <div>
                  <label className="text-xs text-slate-400 mb-1.5 block">Username</label>
                  <input
                    value={form.username}
                    onChange={(e) => setForm({ ...form, username: e.target.value })}
                    placeholder="johndoe"
                    required
                    className={inputCls}
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 mb-1.5 block">Full Name</label>
                  <input
                    value={form.full_name}
                    onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                    placeholder="John Doe"
                    required
                    className={inputCls}
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 mb-1.5 block">Organization</label>
                  <input
                    value={form.org_name}
                    onChange={(e) => setForm({ ...form, org_name: e.target.value })}
                    placeholder="Acme Corp"
                    className={inputCls}
                  />
                </div>
              </>
            )}

            <div>
              <label className="text-xs text-slate-400 mb-1.5 block">Password</label>
              <div className="relative">
                <input
                  type={showPw ? 'text' : 'password'}
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  placeholder="••••••••"
                  required
                  className={`${inputCls} pr-11`}
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                >
                  {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-brand-500 to-purple-600 text-white font-semibold text-sm hover:opacity-90 transition-all flex items-center justify-center gap-2 disabled:opacity-50 mt-2"
            >
              {loading && <Loader2 size={16} className="animate-spin" />}
              {loading ? 'Please wait...' : mode === 'login' ? 'Sign In' : 'Create Account'}
            </button>
          </form>

          {/* Demo hint */}
          <div className="mt-5 p-3 rounded-xl bg-brand-500/5 border border-brand-500/10">
            <p className="text-[11px] text-slate-500 text-center">
              <span className="text-brand-400">🚀 Demo mode:</span> Register with any email to get started.
              <br />The system includes 4 ready-to-run autonomous company demos.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
