import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { format, subDays, startOfDay, addDays } from 'date-fns';

// TypeScript interfaces
export interface LeadsTrendChartProps {
  dateRange: 'last_7_days' | 'last_30_days' | 'last_90_days';
}

interface LeadData {
  date: string;
  count: number;
  formattedDate: string;
}

interface UseLeadsTrendDataResult {
  data: LeadData[] | undefined;
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

// Mock data generation function
const generateMockLeadData = (dateRange: LeadsTrendChartProps['dateRange']): LeadData[] => {
  const today = startOfDay(new Date());
  let days: number;
  
  switch (dateRange) {
    case 'last_7_days':
      days = 7;
      break;
    case 'last_30_days':
      days = 30;
      break;
    case 'last_90_days':
      days = 90;
      break;
    default:
      days = 30;
  }
  
  const data: LeadData[] = [];
  
  for (let i = days - 1; i >= 0; i--) {
    const date = subDays(today, i);
    const dateString = format(date, 'yyyy-MM-dd');
    const formattedDate = format(date, 'MMM dd');
    
    // Generate realistic lead counts with some variation
    const baseCount = Math.floor(Math.random() * 50) + 20; // 20-70 base
    const weekdayMultiplier = date.getDay() === 0 || date.getDay() === 6 ? 0.6 : 1; // Lower on weekends
    const count = Math.floor(baseCount * weekdayMultiplier);
    
    data.push({
      date: dateString,
      count,
      formattedDate,
    });
  }
  
  return data;
};

// Custom hook for data fetching
const useLeadsTrendData = (dateRange: LeadsTrendChartProps['dateRange']): UseLeadsTrendDataResult => {
  const query = useQuery({
    queryKey: ['leadsTrend', dateRange],
    queryFn: async (): Promise<LeadData[]> => {
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Simulate occasional API errors for testing
      if (Math.random() < 0.1) {
        throw new Error('Failed to fetch leads data. Please try again.');
      }
      
      return generateMockLeadData(dateRange);
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  });

  return {
    data: query.data,
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
  };
};

// Custom tooltip component
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
        <p className="text-sm font-medium text-gray-900">{`Date: ${payload[0]?.payload?.formattedDate}`}</p>
        <p className="text-sm text-indigo-600">{`Leads: ${payload[0]?.value}`}</p>
      </div>
    );
  }
  return null;
};

// Main component
const LeadsTrendChart: React.FC<LeadsTrendChartProps> = ({ dateRange }) => {
  const { data, isLoading, error, refetch } = useLeadsTrendData(dateRange);
  
  // Get display text for date range
  const getDateRangeText = (range: LeadsTrendChartProps['dateRange']): string => {
    switch (range) {
      case 'last_7_days':
        return 'Last 7 Days';
      case 'last_30_days':
        return 'Last 30 Days';
      case 'last_90_days':
        return 'Last 90 Days';
      default:
        return 'Selected Period';
    }
  };

  // Calculate summary statistics
  const calculateStats = (data: LeadData[]) => {
    if (!data || data.length === 0) return null;
    
    const totalLeads = data.reduce((sum, item) => sum + item.count, 0);
    const averageLeads = Math.round(totalLeads / data.length);
    const maxLeads = Math.max(...data.map(item => item.count));
    
    return { totalLeads, averageLeads, maxLeads };
  };

  const stats = data ? calculateStats(data) : null;

  return (
    <div className="bg-white shadow-sm rounded-lg p-6 border border-gray-200">
      {/* Header */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900">
          Leads Over Time ({getDateRangeText(dateRange)})
        </h3>
        {stats && (
          <div className="mt-2 flex flex-wrap gap-4 text-sm text-gray-600">
            <span>Total: <span className="font-medium text-gray-900">{stats.totalLeads}</span></span>
            <span>Average: <span className="font-medium text-gray-900">{stats.averageLeads}/day</span></span>
            <span>Peak: <span className="font-medium text-gray-900">{stats.maxLeads}</span></span>
          </div>
        )}
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center h-80">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mb-4"></div>
            <p className="text-gray-600">Loading chart...</p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="flex items-center justify-center h-80">
          <div className="text-center">
            <div className="text-red-500 mb-4">
              <svg className="h-12 w-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-gray-900 font-medium mb-2">Failed to load chart data</p>
            <p className="text-gray-600 mb-4">{error.message}</p>
            <button
              onClick={() => refetch()}
              className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors"
            >
              Try Again
            </button>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !error && (!data || data.length === 0) && (
        <div className="flex items-center justify-center h-80">
          <div className="text-center">
            <div className="text-gray-400 mb-4">
              <svg className="h-12 w-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <p className="text-gray-900 font-medium">No data available</p>
            <p className="text-gray-600">No leads data found for the selected period.</p>
          </div>
        </div>
      )}

      {/* Chart */}
      {!isLoading && !error && data && data.length > 0 && (
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={data}
              margin={{
                top: 5,
                right: 30,
                left: 20,
                bottom: 5,
              }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
              <XAxis
                dataKey="formattedDate"
                stroke="#6b7280"
                fontSize={12}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                stroke="#6b7280"
                fontSize={12}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="count"
                stroke="#6366f1"
                strokeWidth={2}
                dot={{ fill: '#6366f1', strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6, stroke: '#6366f1', strokeWidth: 2, fill: '#ffffff' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};

export default LeadsTrendChart;