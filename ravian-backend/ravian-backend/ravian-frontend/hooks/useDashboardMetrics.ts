import { useQuery } from '@tanstack/react-query';
import apiClient from '@/lib/api';
import { calculateTrend } from '@/lib/utils';
import type { DashboardMetrics, DateRangeType } from '@/types/dashboard';

interface ApiResponse<T> {
  data: T[];
  pagination: {
    total: number;
    page: number;
    per_page: number;
    pages: number;
  };
}

interface Lead {
  id: string;
  created_at: string;
  status: string;
  source: string;
}

interface Demo {
  id: string;
  scheduled_at: string;
  outcome: 'completed' | 'no_show' | 'cancelled' | 'rescheduled';
  duration_seconds?: number;
}

interface Enrollment {
  id: string;
  enrolled_at: string;
  status: 'active' | 'inactive' | 'suspended';
}

function getStartDate(dateRange: DateRangeType): string {
  const now = new Date();
  const date = new Date(now);
  
  switch (dateRange) {
    case 'last_7_days':
      date.setDate(date.getDate() - 7);
      break;
    case 'last_30_days':
      date.setDate(date.getDate() - 30);
      break;
    case 'last_90_days':
      date.setDate(date.getDate() - 90);
      break;
    case 'last_12_months':
      date.setFullYear(date.getFullYear() - 1);
      break;
    default:
      date.setDate(date.getDate() - 30);
  }
  
  return date.toISOString().split('T')[0];
}

function getPreviousStartDate(dateRange: DateRangeType): string {
  const now = new Date();
  const date = new Date(now);
  
  switch (dateRange) {
    case 'last_7_days':
      date.setDate(date.getDate() - 14);
      break;
    case 'last_30_days':
      date.setDate(date.getDate() - 60);
      break;
    case 'last_90_days':
      date.setDate(date.getDate() - 180);
      break;
    case 'last_12_months':
      date.setFullYear(date.getFullYear() - 2);
      break;
    default:
      date.setDate(date.getDate() - 60);
  }
  
  return date.toISOString().split('T')[0];
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}m ${secs}s`;
}

export function useDashboardMetrics(dateRange: DateRangeType) {
  return useQuery<DashboardMetrics, Error>({
    queryKey: ['dashboard-metrics', dateRange],
    queryFn: async (): Promise<DashboardMetrics> => {
      try {
        const startDate = getStartDate(dateRange);
        const previousStartDate = getPreviousStartDate(dateRange);
        
        // Fetch current period data
        const [leadsResponse, demosResponse, enrollmentsResponse] = await Promise.all([
          apiClient.get<ApiResponse<Lead>>(`/api/v1/leads/?created_after=${startDate}`),
          apiClient.get<ApiResponse<Demo>>(`/api/v1/demos/?scheduled_after=${startDate}`),
          apiClient.get<ApiResponse<Enrollment>>(`/api/v1/enrollments/?enrolled_after=${startDate}`),
        ]);

        // Fetch previous period data for trend calculation
        const [prevLeadsResponse, prevDemosResponse, prevEnrollmentsResponse] = await Promise.all([
          apiClient.get<ApiResponse<Lead>>(`/api/v1/leads/?created_after=${previousStartDate}&created_before=${startDate}`),
          apiClient.get<ApiResponse<Demo>>(`/api/v1/demos/?scheduled_after=${previousStartDate}&scheduled_before=${startDate}`),
          apiClient.get<ApiResponse<Enrollment>>(`/api/v1/enrollments/?enrolled_after=${previousStartDate}&enrolled_before=${startDate}`),
        ]);

        const leads = leadsResponse.data;
        const demos = demosResponse.data;
        const enrollments = enrollmentsResponse.data;

        const prevLeads = prevLeadsResponse.data;
        const prevDemos = prevDemosResponse.data;
        const prevEnrollments = prevEnrollmentsResponse.data;

        // Calculate metrics
        const totalLeads = leads.pagination.total;
        const totalDemos = demos.pagination.total;
        const totalEnrollments = enrollments.pagination.total;
        
        const noShows = demos.data.filter(d => d.outcome === 'no_show').length;
        const completedDemos = demos.data.filter(d => d.outcome === 'completed');
        
        // Calculate average call duration
        const totalDuration = completedDemos.reduce((sum, demo) => 
          sum + (demo.duration_seconds || 0), 0
        );
        const avgCallTime = completedDemos.length > 0 
          ? formatDuration(Math.round(totalDuration / completedDemos.length))
          : '0m 0s';

        // Calculate conversion rate
        const conversionRate = totalLeads > 0 
          ? ((totalEnrollments / totalLeads) * 100).toFixed(1)
          : '0.0';

        // Calculate trends
        const leadsTrend = prevLeads.pagination.total > 0
          ? Math.round(((totalLeads - prevLeads.pagination.total) / prevLeads.pagination.total) * 100)
          : 0;

        const demosTrend = prevDemos.pagination.total > 0
          ? Math.round(((totalDemos - prevDemos.pagination.total) / prevDemos.pagination.total) * 100)
          : 0;

        const enrollmentsTrend = prevEnrollments.pagination.total > 0
          ? Math.round(((totalEnrollments - prevEnrollments.pagination.total) / prevEnrollments.pagination.total) * 100)
          : 0;

        const prevNoShows = prevDemos.data.filter(d => d.outcome === 'no_show').length;
        const noShowsTrend = prevNoShows > 0
          ? Math.round(((noShows - prevNoShows) / prevNoShows) * 100)
          : 0;

        const prevConversionRate = prevLeads.pagination.total > 0
          ? (prevEnrollments.pagination.total / prevLeads.pagination.total) * 100
          : 0;
        const conversionTrend = prevConversionRate > 0
          ? Math.round(((parseFloat(conversionRate) - prevConversionRate) / prevConversionRate) * 100)
          : 0;

        return {
          total_leads: totalLeads,
          demos_scheduled: totalDemos,
          enrollments: totalEnrollments,
          no_shows: noShows,
          conversion_rate: conversionRate,
          avg_call_time: avgCallTime,
          leads_trend: leadsTrend,
          demos_trend: demosTrend,
          enrollments_trend: enrollmentsTrend,
          no_shows_trend: noShowsTrend,
          conversion_trend: conversionTrend,
        };
      } catch (error) {
        console.error('Dashboard metrics fetch error:', error);
        throw new Error(
          error instanceof Error 
            ? `Failed to load dashboard metrics: ${error.message}`
            : 'Failed to load dashboard metrics'
        );
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
    retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
}
