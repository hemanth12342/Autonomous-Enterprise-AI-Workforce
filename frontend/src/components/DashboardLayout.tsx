'use client';
import Sidebar from '@/components/Sidebar';
import TopBar from '@/components/TopBar';
import { useGlobalWebSocket } from '@/hooks/useWebSocket';
import { useStore } from '@/store';

interface Props {
  title: string;
  children: React.ReactNode;
}

export default function DashboardLayout({ title, children }: Props) {
  useGlobalWebSocket();
  const { sidebarOpen } = useStore();

  return (
    <div className="min-h-screen bg-surface-0 flex">
      <Sidebar />
      <div
        className="flex-1 flex flex-col min-w-0 transition-all duration-300"
        style={{ marginLeft: sidebarOpen ? '260px' : '0' }}
      >
        <TopBar title={title} />
        <main className="flex-1 p-6 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
