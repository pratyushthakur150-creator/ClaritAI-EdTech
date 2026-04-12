// Dashboard Types
export type DateRangeType = 'last_7_days' | 'last_30_days' | 'last_90_days' | 'last_12_months';

export interface DashboardMetrics {
  total_leads: number;
  demos_scheduled: number;
  enrollments: number;
  no_shows: number;
  conversion_rate: string;
  avg_call_time: string;
  leads_trend: number;
  demos_trend: number;
  enrollments_trend: number;
  no_shows_trend: number;
  conversion_trend: number;
}

export interface MetricCardProps {
  title: string;
  value: string | number;
  trend?: number;
  icon: React.ReactNode;
  color?: 'blue' | 'green' | 'red' | 'yellow' | 'purple' | 'indigo' | 'orange';
  trendInverted?: boolean;
}

export interface DateRangeSelectorProps {
  value: DateRangeType;
  onChange: (value: DateRangeType) => void;
}

// API Types
export interface ApiResponse<T> {
  data: T[];
  pagination: {
    total: number;
    page: number;
    per_page: number;
    pages: number;
  };
  meta?: Record<string, any>;
}

export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, any>;
}

// Lead Types
export interface Lead {
  id: string;
  name: string;
  email: string;
  phone?: string;
  source: string;
  status: 'new' | 'contacted' | 'qualified' | 'demo_scheduled' | 'enrolled' | 'lost';
  created_at: string;
  updated_at: string;
  metadata?: Record<string, any>;
}

// Demo Types
export interface Demo {
  id: string;
  lead_id: string;
  scheduled_at: string;
  outcome: 'scheduled' | 'completed' | 'no_show' | 'cancelled' | 'rescheduled';
  duration_seconds?: number;
  notes?: string;
  created_at: string;
  updated_at: string;
}

// Enrollment Types
export interface Enrollment {
  id: string;
  lead_id: string;
  course_id: string;
  status: 'active' | 'inactive' | 'suspended' | 'completed';
  enrolled_at: string;
  completion_date?: string;
  metadata?: Record<string, any>;
}

// Chart Data Types
export interface ChartDataPoint {
  date: string;
  count: number;
  label?: string;
}

export interface TrendChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    borderColor: string;
    backgroundColor: string;
    tension?: number;
  }[];
}

// User Types
export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'manager' | 'agent';
  avatar_url?: string;
  created_at: string;
  last_login?: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

// Filter Types
export interface FilterOptions {
  dateRange: DateRangeType;
  status?: string[];
  source?: string[];
  agent?: string[];
}

// Component Props Types
export interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  color?: string;
}

export interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<{ error: Error; retry: () => void }>;
}
