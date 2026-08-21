/**
 * API client — axios instance with auth interceptor.
 */
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: `${API_URL}/api`,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
});

// ─── Attach auth token from localStorage ─────────────────────────────────────
api.interceptors.request.use((config) => {
  try {
    const stored = localStorage.getItem('ai-workforce-store');
    if (stored) {
      const parsed = JSON.parse(stored);
      const token = parsed?.state?.accessToken;
      if (token) config.headers.Authorization = `Bearer ${token}`;
    }
  } catch {}
  return config;
});

// ─── Handle 401 globally ─────────────────────────────────────────────────────
api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && typeof window !== 'undefined') {
      const store = require('@/store').useStore.getState();
      store.clearAuth();
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

// ─── API methods ──────────────────────────────────────────────────────────────
export const authApi = {
  register: (data: any) => api.post('/auth/register', data).then((r) => r.data),
  login: (username: string, password: string) => {
    const form = new FormData();
    form.append('username', username);
    form.append('password', password);
    return api.post('/auth/token', form, { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }).then((r) => r.data);
  },
  // One-click demo login — auto-creates a demo user/org if none exists
  demoLogin: () => api.post('/auth/demo-login').then((r) => r.data),
};

export const projectsApi = {
  list: () => api.get('/projects/').then((r) => r.data),
  get: (id: string) => api.get(`/projects/${id}`).then((r) => r.data),
  create: (data: any) => api.post('/projects/', data).then((r) => r.data),
  start: (id: string) => api.post(`/projects/${id}/start`).then((r) => r.data),
  activity: (id: string) => api.get(`/projects/${id}/activity`).then((r) => r.data),
  tasks: (id: string) => api.get(`/projects/${id}/tasks`).then((r) => r.data),
};

export const agentsApi = {
  list: () => api.get('/agents/').then((r) => r.data),
  runs: (type: string) => api.get(`/agents/${type}/runs`).then((r) => r.data),
};

export const approvalsApi = {
  list: (status = 'pending') => api.get(`/approvals/?status=${status}`).then((r) => r.data),
  decide: (id: string, decision: string, notes?: string) =>
    api.post(`/approvals/${id}/decide`, { decision, notes }).then((r) => r.data),
};

export const demoApi = {
  start: (objectiveKey = 'customer_support') =>
    api.post(`/demo/start?objective_key=${objectiveKey}`).then((r) => r.data),
  objectives: () => api.get('/demo/objectives').then((r) => r.data),
};

export const costsApi = {
  summary: () => api.get('/costs/summary').then((r) => r.data),
  byAgent: () => api.get('/costs/by-agent').then((r) => r.data),
  byModel: () => api.get('/costs/by-model').then((r) => r.data),
};

export const healthApi = {
  check: () => api.get('/health').then((r) => r.data),
};

export const metricsApi = {
  get: () => api.get('/metrics/').then((r) => r.data),
};
