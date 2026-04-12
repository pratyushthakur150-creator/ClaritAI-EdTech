export interface TASource {
  document_title: string
  document_type: string
  source_file: string
  page_number: string
  timestamp_label: string
  relevance_score?: number
}

export interface TAInteraction {
  interaction_id: string
  question: string
  answer: string
  sources: TASource[]
  confidence: number
  rag_used: boolean
  audio_url?: string | null
  transcribed_question?: string
}

export interface DocumentItem {
  document_id: string
  title: string
  document_type: string
  status: string
  chunk_count: number
  file_size: number
  upload_timestamp: string
  error_message?: string
  chroma_collection?: string
}

export interface AtRiskStudent {
  student_id: string
  risk_score: number
  risk_level: 'low' | 'medium' | 'high' | 'critical'
  risk_factors: Array<{ factor_name?: string; factor: string; score: number; description: string }>
  student_name?: string
}

export interface ConfusionTopic {
  topic: string
  confusion_count: number
  total_questions?: number
  avg_confidence: number
  student_count?: number
}
