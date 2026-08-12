'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const router = useRouter();
  useEffect(() => { router.replace('/dashboard'); }, [router]);
  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-0">
      <div className="text-center">
        <div className="text-4xl mb-4">🤖</div>
        <p className="text-slate-400 animate-pulse">Loading AI Workforce OS...</p>
      </div>
    </div>
  );
}
