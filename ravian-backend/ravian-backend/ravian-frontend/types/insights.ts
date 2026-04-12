export interface Insight {
  id: string;
  type: 'opportunity' | 'warning' | 'recommendation' | 'trend';
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  timestamp: string;
  category: string;
  action_items?: string[];
  metrics?: InsightMetrics;
  tags?: string[];
  source?: string;
  affected_entities?: string[];
  estimated_impact?: {
    revenue?: number;
    conversions?: number;
    efficiency?: number;
  };
}

export interface InsightMetrics {
  impact_score: number; // 0-10 scale
  confidence: number; // 0-1 scale
  urgency?: number; // 0-10 scale
  complexity?: number; // 0-10 scale
  effort_required?: 'low' | 'medium' | 'high';
}

export interface InsightCardProps {
  insight: Insight;
  onMarkAsRead?: (insightId: string) => void;
  onDismiss?: (insightId: string) => void;
  onActionTaken?: (insightId: string, actionIndex: number) => void;
  className?: string;
}

export interface InsightsApiResponse {
  insights: Insight[];
  pagination?: {
    total: number;
    page: number;
    per_page: number;
    has_more: boolean;
  };
  status: string;
  message?: string;
  generated_at: string;
  version: string;
}

export interface InsightFilters {
  type?: InsightType | 'all';
  priority?: InsightPriority | 'all';
  category?: string;
  date_range?: {
    start: string;
    end: string;
  };
  tags?: string[];
  min_impact_score?: number;
  min_confidence?: number;
}

export interface InsightSortOptions {
  field: 'timestamp' | 'priority' | 'impact_score' | 'confidence' | 'title';
  direction: 'asc' | 'desc';
}

export interface InsightSummary {
  total_count: number;
  by_type: {
    opportunity: number;
    warning: number;
    recommendation: number;
    trend: number;
  };
  by_priority: {
    high: number;
    medium: number;
    low: number;
  };
  by_category: Record<string, number>;
  average_impact_score: number;
  average_confidence: number;
  recent_activity: {
    last_24h: number;
    last_week: number;
    last_month: number;
  };
}

export interface InsightAction {
  id: string;
  insight_id: string;
  title: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'dismissed';
  assigned_to?: string;
  due_date?: string;
  created_at: string;
  updated_at: string;
  estimated_effort?: string;
  actual_effort?: string;
  results?: {
    success: boolean;
    impact_measured?: number;
    notes?: string;
  };
}

export interface InsightTrend {
  period: string; // ISO date string
  total_insights: number;
  high_priority_insights: number;
  average_impact_score: number;
  most_common_category: string;
  insights_addressed: number;
  insights_dismissed: number;
}

export interface InsightConfiguration {
  enabled_types: InsightType[];
  priority_thresholds: {
    high_impact_score: number;
    medium_impact_score: number;
    high_confidence: number;
    medium_confidence: number;
  };
  notification_settings: {
    email_enabled: boolean;
    push_enabled: boolean;
    high_priority_immediate: boolean;
    digest_frequency: 'daily' | 'weekly' | 'monthly';
  };
  auto_dismiss: {
    enabled: boolean;
    low_priority_after_days: number;
    low_confidence_after_days: number;
  };
}

// Type aliases for better readability
export type InsightType = Insight['type'];
export type InsightPriority = Insight['priority'];
export type InsightCategory = string;

// Utility types
export type InsightWithActions = Insight & {
  actions: InsightAction[];
};

export type InsightStats = {
  insight: Insight;
  views: number;
  actions_taken: number;
  time_to_action?: number; // milliseconds
  effectiveness_score?: number; // 0-10
};

// Hook return types
export interface UseInsightsReturn {
  data: Insight[] | undefined;
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
  hasNextPage?: boolean;
  fetchNextPage?: () => void;
  isFetchingNextPage?: boolean;
}

export interface UseInsightFiltersReturn {
  filters: InsightFilters;
  setFilters: (filters: Partial<InsightFilters>) => void;
  resetFilters: () => void;
  activeFilterCount: number;
}

export interface UseInsightActionsReturn {
  markAsRead: (insightId: string) => Promise<void>;
  dismiss: (insightId: string) => Promise<void>;
  takeAction: (insightId: string, actionIndex: number) => Promise<void>;
  bulkActions: {
    markMultipleAsRead: (insightIds: string[]) => Promise<void>;
    dismissMultiple: (insightIds: string[]) => Promise<void>;
  };
}

// Component prop types
export interface InsightListProps {
  insights: Insight[];
  loading?: boolean;
  error?: Error | null;
  onInsightAction?: (insight: Insight, action: string) => void;
  emptyMessage?: string;
  className?: string;
}

export interface InsightFiltersProps {
  filters: InsightFilters;
  onFiltersChange: (filters: Partial<InsightFilters>) => void;
  availableCategories: string[];
  className?: string;
}

export interface InsightSummaryProps {
  summary: InsightSummary;
  loading?: boolean;
  className?: string;
}
