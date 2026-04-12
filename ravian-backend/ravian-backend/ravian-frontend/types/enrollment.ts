export interface Enrollment {
  id: string
  student_name: string
  student_id?: string
  course: string
  course_id?: string
  enrollment_date: string
  status: 'active' | 'completed' | 'dropped'
  progress: number
  created_at?: string
}

export interface EnrollmentCreatePayload {
  student_id: string
  course_id: string
  status?: Enrollment['status']
}
