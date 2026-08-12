/**
 * WebSocket hook — subscribes to global + project-specific event channels.
 * Automatically reconnects on disconnect.
 */
'use client';
import { useEffect, useRef, useCallback } from 'react';
import { useStore } from '@/store';
import { toast } from 'sonner';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

// Maps event_type → agent status
const AGENT_EVENT_MAP: Record<string, { status: string; field: 'current_task' }> = {
  agent_started:   { status: 'working', field: 'current_task' },
  agent_thinking:  { status: 'working', field: 'current_task' },
  agent_completed: { status: 'idle',    field: 'current_task' },
  agent_failed:    { status: 'failed',  field: 'current_task' },
};

export function useGlobalWebSocket() {
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<NodeJS.Timeout>();
  const { addEvent, updateAgent, addProject, updateProject, addApproval } = useStore();

  const connect = useCallback(() => {
    try {
      const socket = new WebSocket(`${WS_URL}/api/ws/global`);

      socket.onopen = () => {
        console.log('🔗 Global WebSocket connected');
      };

      socket.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          if (data.event_type === 'ping') return;

          // Add to activity feed
          addEvent({
            id: `${Date.now()}-${Math.random()}`,
            ...data,
            timestamp: data.timestamp || new Date().toISOString(),
          });

          // Update agent status
          if (data.agent_type && AGENT_EVENT_MAP[data.event_type]) {
            const { status } = AGENT_EVENT_MAP[data.event_type];
            updateAgent(data.agent_type, {
              status: status as any,
              current_task: data.event_type === 'agent_started' || data.event_type === 'agent_thinking'
                ? data.message : undefined,
            });
          }

          // Handle specific events
          switch (data.event_type) {
            case 'demo_started':
              toast.success(`🚀 ${data.message}`, { duration: 5000 });
              break;
            case 'demo_completed':
              toast.success(`✅ ${data.message}`, { duration: 8000 });
              break;
            case 'demo_error':
              toast.error(`❌ ${data.message}`);
              break;
            case 'approval_required':
              addApproval({
                id: data.approval_id,
                project_id: data.project_id,
                requesting_agent: 'devops',
                action_type: 'deployment',
                action_description: `Deploy ${data.project_name} to production`,
                risk_level: data.risk_level || 'medium',
                status: 'pending',
                files_changed: data.files_changed,
                tests_passed: data.tests_passed,
                security_passed: data.security_passed,
                estimated_cost_usd: data.estimated_cost_usd,
                created_at: new Date().toISOString(),
              });
              toast(`🔐 Deployment approval required for ${data.project_name}`, {
                action: { label: 'Review', onClick: () => window.location.href = '/approvals' },
                duration: 10000,
              });
              break;
            case 'deployment_complete':
              toast.success('🚀 Deployment successful!');
              if (data.project_id) {
                updateProject(data.project_id, { status: 'completed', deployment_url: data.deployment_url });
              }
              break;
          }

        } catch (err) {
          console.warn('Failed to parse WS message', err);
        }
      };

      socket.onclose = () => {
        console.log('WebSocket disconnected, reconnecting in 3s...');
        reconnectTimeout.current = setTimeout(connect, 3000);
      };

      socket.onerror = () => {
        socket.close();
      };

      ws.current = socket;
    } catch (err) {
      console.warn('WebSocket connection failed', err);
      reconnectTimeout.current = setTimeout(connect, 5000);
    }
  }, [addEvent, updateAgent, addApproval, updateProject]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimeout.current);
      ws.current?.close();
    };
  }, [connect]);
}

export function useProjectWebSocket(projectId: string | null) {
  const ws = useRef<WebSocket | null>(null);
  const { addEvent, updateProject, updateAgent } = useStore();

  useEffect(() => {
    if (!projectId) return;

    const socket = new WebSocket(`${WS_URL}/api/ws/project/${projectId}`);

    socket.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.event_type === 'ping') return;

        addEvent({
          id: `${Date.now()}-${Math.random()}`,
          ...data,
          timestamp: data.timestamp || new Date().toISOString(),
        });

        // Update project progress from workflow events
        if (data.event_type === 'qa_report_ready') {
          const passed = data.data?.report?.test_summary?.passed || 0;
          const total = data.data?.report?.test_summary?.total_tests || 1;
          updateProject(projectId, { progress_percent: 60 });
        }
        if (data.event_type === 'deployment_complete') {
          updateProject(projectId, { status: 'completed', progress_percent: 100 });
        }
      } catch {}
    };

    ws.current = socket;
    return () => socket.close();
  }, [projectId, addEvent, updateProject, updateAgent]);
}
