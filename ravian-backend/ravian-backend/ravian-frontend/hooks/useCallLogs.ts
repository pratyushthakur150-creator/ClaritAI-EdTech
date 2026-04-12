import { useQuery } from '@tanstack/react-query';
import { API_BASE_URL, API_ENDPOINTS } from '@/lib/apiService';

export interface CallLog {
  id: string;
  leadName: string;
  course: string;
  timestamp: string;
  duration: number;
  sentiment: 'positive' | 'neutral' | 'negative';
  outcome: 'demo_booked' | 'callback' | 'not_interested' | 'voicemail' | 'no_answer' | 'information_provided';
}

interface CallLogsResponse {
  calls: CallLog[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

interface UseCallLogsOptions {
  sentimentFilter?: 'positive' | 'neutral' | 'negative';
  page?: number;
  limit?: number;
}

const fetchCallLogs = async (options: UseCallLogsOptions = {}): Promise<CallLog[]> => {
  const { sentimentFilter, page = 1, limit = 50 } = options;

  const searchParams = new URLSearchParams({
    page: page.toString(),
    limit: limit.toString(),
  });

  if (sentimentFilter) {
    searchParams.append('sentiment', sentimentFilter);
  }

  const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.calls}?${searchParams.toString()}`, {
    headers: {
      Authorization: typeof window !== 'undefined' ? `Bearer ${localStorage.getItem('access_token') || ''}` : '',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch call logs: ${response.status} ${response.statusText}`);
  }

  const data: CallLogsResponse = await response.json();
  return data.calls;
};

export const useCallLogs = (
  sentimentFilter?: 'positive' | 'neutral' | 'negative',
  options: Omit<UseCallLogsOptions, 'sentimentFilter'> = {}
) => {
  return useQuery<CallLog[]>({
    queryKey: ['callLogs', sentimentFilter, options.page, options.limit],
    queryFn: () => fetchCallLogs({ sentimentFilter, ...options }),
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
};

// Additional hook for fetching call logs with pagination
export const useCallLogsWithPagination = (
  sentimentFilter?: 'positive' | 'neutral' | 'negative',
  page: number = 1,
  limit: number = 50
) => {
  return useQuery<CallLogsResponse>({
    queryKey: ['callLogsPaginated', sentimentFilter, page, limit],
    queryFn: async (): Promise<CallLogsResponse> => {
      const searchParams = new URLSearchParams({
        page: page.toString(),
        limit: limit.toString(),
      });

      if (sentimentFilter) {
        searchParams.append('sentiment', sentimentFilter);
      }

      const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.calls}?${searchParams.toString()}`, {
        headers: {
          Authorization: typeof window !== 'undefined' ? `Bearer ${localStorage.getItem('access_token') || ''}` : '',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch call logs: ${response.status} ${response.statusText}`);
      }

      return response.json();
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    placeholderData: (prev) => prev, // Keep previous data while fetching new page
  });
};