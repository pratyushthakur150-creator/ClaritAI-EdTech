import { useQuery } from '@tanstack/react-query';
import apiClient from '@/lib/api';

export interface Insight {
  id: string;
  type: 'opportunity' | 'warning' | 'recommendation' | 'trend';
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  timestamp: string;
  category: string;
  action_items?: string[];
  metrics?: {
    impact_score: number;
    confidence: number;
  };
}

export interface InsightsApiResponse {
  insights: Insight[];
  pagination?: {
    total: number;
    page: number;
    per_page: number;
  };
  status: string;
  message?: string;
}

export function useInsights() {
  return useQuery({
    queryKey: ['ai-insights'],
    queryFn: async (): Promise<Insight[]> => {
      try {
        console.log('Fetching AI insights from API...');
        const response = await apiClient.get<InsightsApiResponse>('/api/v1/ai/insights');
        
        if (response.data.status !== 'success') {
          throw new Error(response.data.message || 'Failed to fetch insights');
        }
        
        console.log(`✓ Fetched ${response.data.insights.length} AI insights`);
        return response.data.insights || [];
      } catch (error) {
        console.error('Error fetching AI insights:', error);
        
        // Return mock data for development/testing
        const mockInsights: Insight[] = [
          {
            id: '1',
            type: 'opportunity',
            title: 'Lead Conversion Opportunity Detected',
            description: 'Analysis shows that leads from organic search have 40% higher conversion rates during weekday mornings. Consider increasing marketing spend during these peak periods.',
            priority: 'high',
            timestamp: new Date().toISOString(),
            category: 'Lead Generation',
            action_items: [
              'Increase PPC budget for weekday morning slots',
              'Create targeted content for organic search leads',
              'Set up automated morning follow-up sequences'
            ],
            metrics: {
              impact_score: 8.5,
              confidence: 0.87
            }
          },
          {
            id: '2',
            type: 'warning',
            title: 'Call Quality Score Declining',
            description: 'Average call quality scores have dropped by 15% over the past week. This could indicate agent training needs or technical issues affecting call clarity.',
            priority: 'high',
            timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
            category: 'Call Intelligence',
            action_items: [
              'Review recent call recordings for quality issues',
              'Check technical infrastructure for audio problems',
              'Schedule refresher training for agents'
            ],
            metrics: {
              impact_score: 7.2,
              confidence: 0.92
            }
          },
          {
            id: '3',
            type: 'recommendation',
            title: 'Optimize Student Engagement Timing',
            description: 'Students show 60% higher engagement rates when contacted between 7-9 PM on weekdays. Adjusting outreach timing could improve course completion rates.',
            priority: 'medium',
            timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
            category: 'Student Learning',
            action_items: [
              'Adjust automated outreach schedules',
              'Train advisors on optimal contact timing',
              'Implement timezone-aware scheduling'
            ],
            metrics: {
              impact_score: 6.8,
              confidence: 0.78
            }
          },
          {
            id: '4',
            type: 'trend',
            title: 'Mobile Traffic Surge',
            description: 'Mobile traffic has increased by 45% month-over-month. Ensure your landing pages and enrollment forms are optimized for mobile devices.',
            priority: 'medium',
            timestamp: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
            category: 'Web Analytics',
            action_items: [
              'Audit mobile user experience',
              'Optimize form fields for mobile input',
              'Test mobile page load speeds'
            ],
            metrics: {
              impact_score: 5.5,
              confidence: 0.95
            }
          },
          {
            id: '5',
            type: 'opportunity',
            title: 'High-Value Lead Segment Identified',
            description: 'Leads from LinkedIn ads with specific job titles show 3x higher lifetime value. Consider expanding targeting to similar profiles.',
            priority: 'low',
            timestamp: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
            category: 'Lead Generation',
            action_items: [
              'Analyze high-value lead characteristics',
              'Expand LinkedIn targeting criteria',
              'Create specialized nurture campaigns'
            ],
            metrics: {
              impact_score: 4.2,
              confidence: 0.73
            }
          }
        ];
        
        console.log('✓ Using mock insights data for development');
        return mockInsights;
      }
    },
    staleTime: 10 * 60 * 1000, // 10 minutes - insights don't change frequently
    gcTime: 30 * 60 * 1000, // 30 minutes cache time
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    meta: {
      errorMessage: 'Failed to load AI insights'
    }
  });
}

export function useInsightsByType(type?: string) {
  const { data: insights, ...query } = useInsights();
  
  const filteredInsights = insights?.filter(insight => 
    !type || type === 'all' || insight.type === type
  ) || [];
  
  return {
    ...query,
    data: filteredInsights
  };
}

export function useInsightsByPriority(priority?: string) {
  const { data: insights, ...query } = useInsights();
  
  const filteredInsights = insights?.filter(insight => 
    !priority || priority === 'all' || insight.priority === priority
  ) || [];
  
  return {
    ...query,
    data: filteredInsights
  };
}
