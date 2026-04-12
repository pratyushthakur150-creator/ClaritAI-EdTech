'use client'

import React, { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import apiClient from '@/lib/api'
import { ArrowLeft, Book, Loader2, Users, Calendar } from 'lucide-react'

interface CourseDetail {
  id: string
  name: string
  description: string | null
  course_code: string | null
  category: string | null
  difficulty_level: string | null
  duration_weeks: number | null
  total_hours: number | null
  price: string | null
  currency: string
  max_students: number | null
  enrollment_count: number
  syllabus: unknown
  modules: string[] | null
  prerequisites: string[] | null
  is_active: string
  is_published: string
  created_at: string | null
}

export default function CourseDetailPage() {
  const params = useParams()
  const router = useRouter()
  const courseId = params?.id as string
  const [course, setCourse] = useState<CourseDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!courseId) return
    setLoading(true)
    setError(null)
    apiClient
      .get<CourseDetail>(`/api/v1/teaching/courses/${courseId}`)
      .then((res) => setCourse(res.data))
      .catch((err: unknown) => {
        const ax = err as { response?: { status?: number; data?: { detail?: string } }; message?: string }
        if (ax?.response?.status === 404) {
          setError('Course not found')
        } else {
          setError(ax?.response?.data?.detail ?? ax?.message ?? 'Failed to load course')
        }
      })
      .finally(() => setLoading(false))
  }, [courseId])

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-brand-600" />
      </div>
    )
  }

  if (error || !course) {
    return (
      <div className="space-y-6">
        <Link
          href="/dashboard/courses"
          className="inline-flex items-center gap-2 text-sm text-slate-600 hover:text-brand-600"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Courses
        </Link>
        <div className="card p-8 text-center">
          <p className="text-red-600">{error ?? 'Course not found'}</p>
          <button
            onClick={() => router.push('/dashboard/courses')}
            className="mt-4 btn-primary"
          >
            Back to Courses
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <Link
        href="/dashboard/courses"
        className="inline-flex items-center gap-2 text-sm text-slate-600 hover:text-brand-600"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Courses
      </Link>

      <div className="card p-6">
        <div className="flex items-start justify-between gap-4 mb-6">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-brand-100 flex items-center justify-center">
              <Book className="w-6 h-6 text-brand-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">{course.name}</h1>
              {course.category && (
                <span className="inline-block mt-1 px-2 py-0.5 text-xs font-medium bg-slate-100 text-slate-600 rounded">
                  {course.category}
                </span>
              )}
            </div>
          </div>
          <span className={`badge ${course.is_active === 'true' ? 'badge-success' : 'badge-neutral'}`}>
            {course.is_active === 'true' ? 'Active' : 'Draft'}
          </span>
        </div>

        {course.description && (
          <p className="text-slate-600 mb-6">{course.description}</p>
        )}

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
          <div className="flex items-center gap-2 p-3 bg-slate-50 rounded-lg">
            <Users className="w-5 h-5 text-brand-600" />
            <div>
              <p className="text-xs text-slate-500">Students</p>
              <p className="font-semibold text-slate-900">{course.enrollment_count ?? 0}</p>
            </div>
          </div>
          <div className="flex items-center gap-2 p-3 bg-slate-50 rounded-lg">
            <Calendar className="w-5 h-5 text-brand-600" />
            <div>
              <p className="text-xs text-slate-500">Duration</p>
              <p className="font-semibold text-slate-900">{course.duration_weeks ? `${course.duration_weeks} weeks` : '—'}</p>
            </div>
          </div>
          <div className="p-3 bg-slate-50 rounded-lg">
            <p className="text-xs text-slate-500">Price</p>
            <p className="font-semibold text-slate-900">{course.price ?? '—'}</p>
          </div>
          <div className="p-3 bg-slate-50 rounded-lg">
            <p className="text-xs text-slate-500">Difficulty</p>
            <p className="font-semibold text-slate-900 capitalize">{course.difficulty_level ?? '—'}</p>
          </div>
        </div>

        {course.modules && Array.isArray(course.modules) && course.modules.length > 0 && (
          <div>
            <h2 className="text-sm font-semibold text-slate-900 mb-3">Modules</h2>
            <ul className="list-disc list-inside space-y-1 text-slate-600">
              {course.modules.map((m, i) => (
                <li key={i}>{m}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}
