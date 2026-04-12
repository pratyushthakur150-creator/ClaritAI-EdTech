export interface Lead {
  id: string
  name: string
  email: string
  phone?: string
  course_interest?: string
  lead_source?: string
  status: 'new' | 'contacted' | 'qualified' | 'converted' | 'lost'
  qualification_score?: number
  created_at: string
  updated_at: string
}

export interface LeadCreatePayload {
  name: string
  email: string
  phone?: string
  course_interest?: string
  message?: string
}

export interface LeadUpdatePayload {
  name?: string
  email?: string
  phone?: string
  course_interest?: string
  status?: Lead['status']
}
