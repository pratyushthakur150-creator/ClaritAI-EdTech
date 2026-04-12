import { useQuery } from '@tanstack/react-query';
import apiClient from '@/lib/api';
import type { FunnelApiResponse, FunnelStage } from '@/types/funnel';
import type { DateRangeType } from '@/types/dashboard';

export function useFunnelData(dateRange: DateRangeType) {
  return useQuery({
    queryKey: ['funnel-analytics', dateRange],
    queryFn: async (): Promise<FunnelStage[]> => {
      try {
        console.log(`Fetching funnel data for date range: ${dateRange}`);

        const response = await apiClient.get<FunnelApiResponse>(
          `/api/v1/attribution/funnel?date_range=${dateRange}`
        );

        const data = response.data;
        console.log('Funnel API Response:', data);

        // Validate API response structure
        if (!data || typeof data !== 'object') {
          throw new Error('Invalid API response format');
        }

        // Extract and validate numeric values
        const visitors = Number(data.visitors) || 0;
        const chatbotEngaged = Number(data.chatbot_engaged) || 0;
        const callsAnswered = Number(data.calls_answered) || 0;
        const demosScheduled = Number(data.demos_scheduled) || 0;
        const demosAttended = Number(data.demos_attended) || 0;
        const enrolled = Number(data.enrolled) || 0;

        // Calculate funnel stages with conversion percentages
        const stages: FunnelStage[] = [
          {
            label: 'Website Visitors',
            count: visitors,
            percentage: 100
          },
          {
            label: 'Chatbot Engaged',
            count: chatbotEngaged,
            percentage: visitors > 0 ? Math.round((chatbotEngaged / visitors) * 100) : 0
          },
          {
            label: 'Calls Answered',
            count: callsAnswered,
            percentage: chatbotEngaged > 0 ? Math.round((callsAnswered / chatbotEngaged) * 100) : 0
          },
          {
            label: 'Demos Scheduled',
            count: demosScheduled,
            percentage: callsAnswered > 0 ? Math.round((demosScheduled / callsAnswered) * 100) : 0
          },
          {
            label: 'Demos Attended',
            count: demosAttended,
            percentage: demosScheduled > 0 ? Math.round((demosAttended / demosScheduled) * 100) : 0
          },
          {
            label: 'Students Enrolled',
            count: enrolled,
            percentage: demosAttended > 0 ? Math.round((enrolled / demosAttended) * 100) : 0
          },
        ];

        // Filter out stages with zero counts for cleaner display
        // but keep at least the first stage
        const filteredStages = stages.filter((stage, index) => stage.count > 0 || index === 0);

        console.log('Processed funnel stages:', filteredStages);

        return filteredStages;
      } catch (error) {
        console.error('Error fetching funnel data:', error);

        // Enhanced error handling
        if (error instanceof Error) {
          if (error.message.includes('401')) {
            throw new Error('Authentication required. Please log in again.');
          } else if (error.message.includes('403')) {
            throw new Error('Access denied. Insufficient permissions to view funnel data.');
          } else if (error.message.includes('404')) {
            throw new Error('Funnel analytics endpoint not found.');
          } else if (error.message.includes('500')) {
            throw new Error('Server error. Please try again later.');
          } else if (error.message.includes('Network Error')) {
            throw new Error('Network connection failed. Please check your internet connection.');
          }
          throw error;
        }

        throw new Error('Failed to fetch funnel analytics data. Please try again.');
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes - data doesn't change frequently
    gcTime: 10 * 60 * 1000, // 10 minutes - keep in cache longer
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000), // Exponential backoff
    refetchOnWindowFocus: false, // Don't refetch on window focus for analytics data
    refetchOnMount: true,

    // Enable background refetching for real-time updates
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes

    // Error boundary integration
    throwOnError: false,

    // Data transformation and validation
    select: (data: FunnelStage[]) => {
      // Additional client-side processing if needed
      return data.map((stage, index) => ({
        ...stage,
        // Add sequential ordering
        order: index,
        // Add trend indicators (could be enhanced with historical data)
        trend: index === 0 ? 'stable' : 'unknown'
      }));
    }
  });
}

// Additional utility hook for funnel metrics calculation
export function useFunnelMetrics(stages: FunnelStage[]) {
  if (!stages || stages.length === 0) {
    return {
      totalVolume: 0,
      overallConversion: 0,
      topOfFunnel: 0,
      bottomOfFunnel: 0,
      largestDropoff: { stage: '', percentage: 0 },
      bestConversion: { stage: '', percentage: 0 }
    };
  }

  const totalVolume = stages.reduce((sum, stage) => sum + stage.count, 0);
  const topOfFunnel = stages[0]?.count || 0;
  const bottomOfFunnel = stages[stages.length - 1]?.count || 0;
  const overallConversion = topOfFunnel > 0 ? (bottomOfFunnel / topOfFunnel) * 100 : 0;

  // Find largest dropoff between consecutive stages
  let largestDropoff = { stage: '', percentage: 0 };
  let bestConversion = { stage: '', percentage: 0 };

  for (let i = 1; i < stages.length; i++) {
    const previousCount = stages[i - 1].count;
    const currentCount = stages[i].count;

    if (previousCount > 0) {
      const dropoffPercentage = ((previousCount - currentCount) / previousCount) * 100;
      const conversionPercentage = (currentCount / previousCount) * 100;

      if (dropoffPercentage > largestDropoff.percentage) {
        largestDropoff = {
          stage: `${stages[i - 1].label} to ${stages[i].label}`,
          percentage: dropoffPercentage
        };
      }

      if (conversionPercentage > bestConversion.percentage) {
        bestConversion = {
          stage: `${stages[i - 1].label} to ${stages[i].label}`,
          percentage: conversionPercentage
        };
      }
    }
  }

  return {
    totalVolume,
    overallConversion: Math.round(overallConversion * 100) / 100,
    topOfFunnel,
    bottomOfFunnel,
    largestDropoff,
    bestConversion
  };
}