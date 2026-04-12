// Core funnel data types
export interface FunnelStage {
  label: string;
  count: number;
  percentage: number;
  order?: number;
  trend?: 'up' | 'down' | 'stable' | 'unknown';
}

// API response interface matching backend structure
export interface FunnelApiResponse {
  visitors: number;
  chatbot_engaged: number;
  calls_answered: number;
  demos_scheduled: number;
  demos_attended: number;
  enrolled: number;
}

// Component prop types
export interface FunnelChartProps {
  stages: FunnelStage[];
}

export interface FunnelPageProps {
  initialDateRange?: string;
}

// Extended funnel analytics types
export interface FunnelMetrics {
  totalVolume: number;
  overallConversion: number;
  topOfFunnel: number;
  bottomOfFunnel: number;
  largestDropoff: {
    stage: string;
    percentage: number;
  };
  bestConversion: {
    stage: string;
    percentage: number;
  };
}

// Funnel configuration types
export interface FunnelStageConfig {
  id: string;
  label: string;
  description?: string;
  color?: string;
  icon?: string;
  isRequired?: boolean;
}

// Query parameter types for API calls
export interface FunnelQueryParams {
  date_range: string;
  include_empty_stages?: boolean;
  breakdown_by?: 'day' | 'week' | 'month';
  segment?: string;
}

// Error types for funnel operations
export interface FunnelError {
  code: string;
  message: string;
  stage?: string;
  timestamp?: string;
}

// Historical data types for trend analysis
export interface FunnelHistoricalData {
  date: string;
  stages: FunnelStage[];
}

export interface FunnelTrendData {
  current: FunnelStage[];
  previous: FunnelStage[];
  change: {
    percentage: number;
    direction: 'up' | 'down' | 'stable';
  };
}

// Filter and segment types
export type FunnelSegment = 
  | 'all'
  | 'new_visitors'
  | 'returning_visitors'
  | 'mobile'
  | 'desktop'
  | 'organic'
  | 'paid';

export interface FunnelFilters {
  segment?: FunnelSegment;
  source?: string;
  campaign?: string;
  location?: string;
}

// Export aggregated type for easy imports
export type FunnelTypes = {
  FunnelStage: FunnelStage;
  FunnelApiResponse: FunnelApiResponse;
  FunnelChartProps: FunnelChartProps;
  FunnelMetrics: FunnelMetrics;
  FunnelError: FunnelError;
  FunnelFilters: FunnelFilters;
};