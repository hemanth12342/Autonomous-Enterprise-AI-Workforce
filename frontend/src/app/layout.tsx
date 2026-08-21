import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Toaster } from 'sonner';
import AutoLogin from '@/components/AutoLogin';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });

export const metadata: Metadata = {
  title: 'AI Workforce OS — Autonomous Enterprise AI',
  description: 'A Virtual Company Powered by Autonomous AI Agents. CEO, Project Manager, Developer, QA, Security, DevOps agents working autonomously.',
  keywords: ['AI agents', 'autonomous AI', 'enterprise AI', 'multi-agent system', 'LangGraph'],
  openGraph: {
    title: 'AI Workforce OS',
    description: 'A Virtual Company Powered by Autonomous AI Agents',
    type: 'website',
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="icon" href="/favicon.ico" />
      </head>
      <body className={`${inter.variable} font-sans bg-surface-0 text-slate-100 antialiased`}>
        <AutoLogin />
        {children}
        <Toaster
          theme="dark"
          position="top-right"
          toastOptions={{
            style: {
              background: '#13131f',
              border: '1px solid rgba(99,102,241,0.3)',
              color: '#f1f5f9',
            },
          }}
        />
      </body>
    </html>
  );
}

