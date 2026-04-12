// Teaching Assistant API types (matches backend /api/v1/assistant)

export interface AssistantQueryRequest {
  student_id: string;
  mode: 'text' | 'voice';
  query?: string;
  audio_url?: string;
  voice_settings?: {
    voice_id?: string;
    speed?: number;
    return_audio?: boolean;
  };
  context?: {
    module_id?: string;
    lesson_id?: string;
    session_id?: string;
  };
}

export interface AssistantSource {
  id: string;
  content: string;
  relevance_score: number;
  metadata?: Record<string, unknown>;
}

export interface EscalationInfo {
  needed: boolean;
  reason: string | null;
  confidence_score: number;
  context_relevance: number;
}

export interface AssistantQueryResponse {
  interaction_id: string;
  timestamp: string;
  student_id: string;
  tenant_id: string;
  mode: string;
  query_text: string;
  answer_text: string;
  confidence_score: number;
  sources: AssistantSource[];
  follow_up_questions: string[];
  escalation: EscalationInfo;
  processing_time: number;
  transcript?: string;
  response_audio_url?: string;
}

export interface InteractionHistoryItem {
  interaction_id: string;
  timestamp: string;
  mode: string;
  query_text: string;
  answer_text: string;
  confidence_score: number;
  escalation_needed: boolean;
  audio_duration?: number;
}

export interface HistoryResponse {
  student_id: string;
  tenant_id: string;
  total_interactions: number;
  interactions: InteractionHistoryItem[];
  request_timestamp: string;
}

// For chat UI
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources?: AssistantSource[];
  followUpQuestions?: string[];
  confidenceScore?: number;
}
