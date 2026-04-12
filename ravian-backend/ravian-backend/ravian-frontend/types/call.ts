export interface Call {
  id: string
  contact_name?: string
  lead_id?: string
  phone?: string
  date: string
  created_at: string
  duration: number
  status: 'completed' | 'missed' | 'scheduled'
  notes?: string
  outcome?: string
  sentiment?: string
}

export interface CallCreatePayload {
  lead_id: string
  contact_name?: string
  phone?: string
  duration?: number
  status: 'completed' | 'missed' | 'scheduled'
  notes?: string
  call_direction?: string
  outcome?: string
  sentiment?: string
}
