export interface Course {
  id: string
  name: string
  description?: string
  student_count?: number
  status: 'active' | 'draft' | 'archived'
  created_at?: string
  updated_at?: string
}

export interface CourseCreatePayload {
  name: string
  description?: string
  status?: Course['status']
}
