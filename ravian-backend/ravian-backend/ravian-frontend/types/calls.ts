// Call Intelligence TypeScript Interface Definitions
// Defines all types and interfaces for call logs, transcripts, and related API responses

// API types matching backend /api/v1/calls
export interface CallLogCreate {
  lead_id: string;
  call_direction: string;
  duration?: number;
  phone_number?: string;
  transcript?: string;
  summary?: string;
  sentiment?: string;
  outcome: string;
  recording_url?: string;
  notes?: string;
  follow_up_required?: boolean;
  next_action?: string;
}

export interface CallLogResponse {
  id: string;
  lead_id: string;
  call_direction: string;
  duration: number | null;
  phone_number: string | null;
  transcript: string | null;
  summary: string | null;
  sentiment: string | null;
  outcome: string;
  recording_url: string | null;
  cost: number | null;
  notes: string | null;
  follow_up_required: boolean;
  next_action: string | null;
  created_at: string;
  updated_at: string;
}

export interface CallListResponse {
  data: CallLogResponse[];
  pagination: {
    current_page: number;
    total_pages: number;
    total_count: number;
    page_size: number;
    has_next: boolean;
    has_previous: boolean;
  };
  filters_applied?: Record<string, string | null> | null;
}

export interface CallLog {
  id: string;
  lead_name?: string;
  lead_id?: string;
  course?: string;
  timestamp: string;
  created_at?: string;
  duration: number; // Duration in seconds
  outcome: string;
  sentiment: 'positive' | 'neutral' | 'negative';
}

export interface TranscriptMessage {
  role: 'agent' | 'user';
  content: string;
  timestamp: string;
  sentiment: 'positive' | 'neutral' | 'negative';
  intent?: string; // Optional intent classification
}

export interface CallTranscript {
  id: string;
  lead_name: string;
  course: string;
  duration: number; // Duration in seconds
  outcome: string;
  messages: TranscriptMessage[];
  action_taken?: string; // Optional action taken after the call
}

export interface CallLogsResponse {
  data: CallLog[];
  pagination: {
    total: number;
    page: number;
    per_page: number;
    total_pages: number;
  };
}

// Additional utility types for Call Intelligence
export type SentimentType = 'positive' | 'neutral' | 'negative';
export type MessageRole = 'agent' | 'user';

export interface CallFilter {
  sentiment?: SentimentType;
  course?: string;
  page?: number;
  per_page?: number;
}

export interface SentimentStats {
  positive: number;
  neutral: number;
  negative: number;
  total: number;
}
