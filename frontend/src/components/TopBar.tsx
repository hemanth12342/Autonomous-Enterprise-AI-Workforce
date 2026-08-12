'use client';
import { useStore } from '@/store';
import { Bell, Menu, Wifi, WifiOff } from 'lucide-react';
import { useState, useEffect } from 'react';

export default function TopBar({ title }: { title: string }) {
  const { pendingApprovalCount, setSidebarOpen, sidebarOpen } = useStore();
  const [connected, setConnected] = useState(true);
  const [time, setTime] = useState('');

  useEffect(() => {
    const tick = () => setTime(new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <header className="h-14 border-b border-brand-500/10 bg-surface-1/80 backdrop-blur-md flex items-center justify-between px-6 flex-shrink-0 sticky top-0 z-10">
      <div className="flex items-center gap-4">
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="text-slate-400 hover:text-slate-200 transition-colors lg:hidden"
        >
          <Menu size={20} />
        </button>
        <h1 className="text-base font-semibold text-slate-200">{title}</h1>
      </div>

      <div className="flex items-center gap-4">
        {/* ─── Live Clock ─────────────────────────────────── */}
        <span className="text-xs font-mono text-slate-500 hidden sm:block">{time}</span>

        {/* ─── Connection Status ───────────────────────────── */}
        <div className="flex items-center gap-1.5 text-xs">
          {connected ? (
            <>
              <Wifi size={12} className="text-emerald-400" />
              <span className="text-emerald-400 hidden sm:inline">Live</span>
            </>
          ) : (
            <>
              <WifiOff size={12} className="text-red-400" />
              <span className="text-red-400 hidden sm:inline">Offline</span>
            </>
          )}
        </div>

        {/* ─── Approval Badge ──────────────────────────────── */}
        {pendingApprovalCount > 0 && (
          <a
            href="/approvals"
            className="relative flex items-center justify-center w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/30 hover:bg-amber-500/20 transition-colors"
          >
            <Bell size={15} className="text-amber-400" />
            <span className="absolute -top-1 -right-1 w-4 h-4 text-[9px] font-bold bg-amber-500 text-white rounded-full flex items-center justify-center">
              {pendingApprovalCount}
            </span>
          </a>
        )}

        {/* ─── System Status Dot ───────────────────────────── */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
          <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
          <span className="text-[11px] text-emerald-400 font-medium hidden sm:inline">AI Online</span>
        </div>
      </div>
    </header>
  );
}
