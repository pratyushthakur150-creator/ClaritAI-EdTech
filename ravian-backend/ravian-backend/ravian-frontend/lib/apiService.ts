/**
 * API Service - Centralized API base URL and endpoint paths.
 * All endpoints use /api/v1/ prefix to match backend FastAPI routes.
 * Collection endpoints (list/create) have trailing slashes.
 */
import apiClient from '@/lib/api';

/** Backend API base URL (no trailing slash) - use for raw fetch() calls */
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001';

// Endpoint paths with /api/v1/ prefix
export const API_ENDPOINTS = {
  auth: {
    login: '/api/v1/auth/login',      // Auth endpoints don't need trailing slash
    register: '/api/v1/auth/register',
    refresh: '/api/v1/auth/refresh',
  },
  leads: '/api/v1/leads/',  // Collection endpoints require trailing slash
  leadsById: (id: string) => `/api/v1/leads/${id}`,
  calls: '/api/v1/calls',  // No trailing slash
  callsById: (id: string) => `/api/v1/calls/${id}`,
  callTranscript: (callId: string) => `/api/v1/calls/${callId}/transcript`,
  demos: '/api/v1/demos',  // No trailing slash
  enrollments: '/api/v1/enrollments',  // No trailing slash
  analytics: {
    dashboard: '/api/v1/analytics/dashboard',
    funnel: '/api/v1/analytics/funnel',
  },
  assistant: {
    query: '/api/v1/assistant/query',
    history: (studentId: string) => `/api/v1/assistant/history/${studentId}`,
    feedback: '/api/v1/assistant/feedback',
  },
  chatbot: {
    message: '/api/v1/chatbot/message',
    stats: '/api/v1/chatbot/stats',
    sessions: '/api/v1/chatbot/sessions',
    config: (tenantId: string) => `/api/v1/chatbot/config/${tenantId}`,
  },
  teaching: {
    courses: '/api/v1/teaching/courses',
  },
  students: {
    confusion: '/api/v1/students/confusion',
    risk: '/api/v1/students/risk',
    heatmap: '/api/v1/students/heatmap',
  },
  attribution: {
    funnel: '/api/v1/attribution/funnel',
  },
  ai: {
    insights: '/api/v1/ai/insights',
  },
} as const;

export default apiClient;
