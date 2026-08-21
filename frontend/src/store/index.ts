/**
 * Global Zustand store — manages auth, projects, agents, events, approvals.
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// ─── Types ────────────────────────────────────────────────────────────────────
export interface AgentInfo {
  agent_type: string;
  name: string;
  icon: string;
  color: string;
  description: string;
  status: 'idle' | 'working' | 'completed' | 'failed';
  tasks_completed: number;
  tasks_failed: number;
  total_cost_usd: number;
  success_rate: number;
  current_task?: string;
  capabilities?: string[];
}

export interface Project {
  id: string;
  name: string;
  business_objective: string;
  status: string;
  priority: string;
  progress_percent: number;
  total_tasks: number;
  completed_tasks: number;
  actual_cost_usd: number;
  budget_usd: number;
  deployment_url?: string;
  created_at: string;
  is_demo?: boolean;
}

export interface ActivityEvent {
  id: string;
  event_type: string;
  agent_type?: string;
  agent_name?: string;
  project_id?: string;
  message: string;
  data?: Record<string, any>;
  timestamp: string;
}

export interface ApprovalRequest {
  id: string;
  project_id?: string;
  requesting_agent: string;
  action_type: string;
  action_description?: string;
  risk_level: string;
  status: string;
  files_changed?: number;
  tests_passed?: number;
  security_passed?: boolean;
  estimated_cost_usd?: number;
  summary?: string;
  reviewer_notes?: string;
  created_at: string;
}

export interface User {
  id: string;
  username: string;
  email: string;
  role: string;
}

interface Store {
  // ─── Auth ─────────────────────────────────────────────────────────────────
  user: User | null;
  accessToken: string | null;
  setAuth: (user: User, token: string) => void;
  clearAuth: () => void;

  // ─── Projects ──────────────────────────────────────────────────────────────
  projects: Project[];
  selectedProjectId: string | null;
  setProjects: (projects: Project[]) => void;
  addProject: (project: Project) => void;
  updateProject: (id: string, updates: Partial<Project>) => void;
  setSelectedProject: (id: string | null) => void;

  // ─── Agents ───────────────────────────────────────────────────────────────
  agents: AgentInfo[];
  setAgents: (agents: AgentInfo[]) => void;
  updateAgent: (agentType: string, updates: Partial<AgentInfo>) => void;

  // ─── Activity Feed ─────────────────────────────────────────────────────────
  events: ActivityEvent[];
  addEvent: (event: ActivityEvent) => void;
  clearEvents: () => void;

  // ─── Approvals ─────────────────────────────────────────────────────────────
  approvals: ApprovalRequest[];
  pendingApprovalCount: number;
  setApprovals: (approvals: ApprovalRequest[]) => void;
  addApproval: (approval: ApprovalRequest) => void;
  updateApproval: (id: string, updates: Partial<ApprovalRequest>) => void;

  // ─── UI State ──────────────────────────────────────────────────────────────
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  activeWorkflowProjectId: string | null;
  setActiveWorkflow: (id: string | null) => void;
}

let _eventId = 0;

export const useStore = create<Store>()(
  persist(
    (set, get) => ({
      // ─── Auth ───────────────────────────────────────────────────────────────
      user: null,
      accessToken: null,
      setAuth: (user, token) => set({ user, accessToken: token }),
      clearAuth: () => set({ user: null, accessToken: null }),

      // ─── Projects ───────────────────────────────────────────────────────────
      projects: [],
      selectedProjectId: null,
      setProjects: (projects) => set({ projects }),
      addProject: (project) =>
        set((s) => ({ projects: [project, ...s.projects] })),
      updateProject: (id, updates) =>
        set((s) => ({
          projects: s.projects.map((p) => (p.id === id ? { ...p, ...updates } : p)),
        })),
      setSelectedProject: (id) => set({ selectedProjectId: id }),

      // ─── Agents ─────────────────────────────────────────────────────────────
      agents: [],
      setAgents: (agents) => set({ agents }),
      updateAgent: (agentType, updates) =>
        set((s) => ({
          agents: s.agents.map((a) =>
            a.agent_type === agentType ? { ...a, ...updates } : a
          ),
        })),

      // ─── Activity Feed ───────────────────────────────────────────────────────
      events: [],
      addEvent: (event) =>
        set((s) => ({
          events: [{ ...event, id: event.id || String(++_eventId) }, ...s.events].slice(0, 500),
        })),
      clearEvents: () => set({ events: [] }),

      // ─── Approvals ──────────────────────────────────────────────────────────
      approvals: [],
      pendingApprovalCount: 0,
      setApprovals: (approvals) =>
        set({ approvals, pendingApprovalCount: approvals.filter((a) => a.status === 'pending').length }),
      addApproval: (approval) =>
        set((s) => {
          const approvals = [approval, ...s.approvals];
          return { approvals, pendingApprovalCount: approvals.filter((a) => a.status === 'pending').length };
        }),
      updateApproval: (id, updates) =>
        set((s) => {
          const approvals = s.approvals.map((a) => (a.id === id ? { ...a, ...updates } : a));
          return { approvals, pendingApprovalCount: approvals.filter((a) => a.status === 'pending').length };
        }),

      // ─── UI State ────────────────────────────────────────────────────────────
      sidebarOpen: true,
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      activeWorkflowProjectId: null,
      setActiveWorkflow: (id) => set({ activeWorkflowProjectId: id }),
    }),
    {
      name: 'ai-workforce-store',
      partialize: (s) => ({ user: s.user, accessToken: s.accessToken }),
    }
  )
);
