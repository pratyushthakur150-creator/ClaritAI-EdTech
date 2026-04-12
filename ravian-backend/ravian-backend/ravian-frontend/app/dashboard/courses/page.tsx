"use client"

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import apiClient from '@/lib/api'
import { BookOpen, Users, Star, Plus, Search, MoreHorizontal, Clock, GraduationCap } from 'lucide-react'

interface Course {
  id: string; title: string; instructor: string; enrolled: number
  rating: number; status: string; category: string; duration: string
}

const STATUS_COLORS: Record<string, { bg: string; color: string; border: string }> = {
  active: { bg: 'rgba(16,185,129,0.1)', color: '#34D399', border: 'rgba(16,185,129,0.2)' },
  draft: { bg: 'rgba(245,158,11,0.1)', color: '#FBBF24', border: 'rgba(245,158,11,0.2)' },
  archived: { bg: 'rgba(107,114,128,0.1)', color: '#9CA3AF', border: 'rgba(107,114,128,0.2)' },
}

export default function CoursesPage() {
  const [searchQuery, setSearchQuery] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['courses'],
    queryFn: async () => { try { const res = await apiClient.get(`/api/v1/courses`); return res.data } catch { return null } },
  })

  const rawCourses = data?.courses || data?.data || []
  const courses: Course[] = rawCourses.map((c: any) => ({
    id: c.id?.toString() || '',
    title: c.name || c.title || 'Untitled Course',
    instructor: c.instructor || c.instructor_name || 'Staff',
    enrolled: c.enrolled || c.enrolled_count || c.enrollment_count || 0,
    rating: c.rating || c.avg_rating || 4.5,
    status: (c.status || 'active').toLowerCase(),
    category: c.category || c.subject || 'General',
    duration: c.duration || c.duration_weeks ? `${c.duration_weeks || 8} weeks` : '8 weeks',
  }))

  const filtered = courses.filter(c =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.category.toLowerCase().includes(searchQuery.toLowerCase())
  )
  const activeCourses = courses.filter(c => c.status === 'active').length
  const totalEnrolled = courses.reduce((s, c) => s + c.enrolled, 0)
  const avgRating = courses.length > 0 ? (courses.reduce((s, c) => s + c.rating, 0) / courses.length).toFixed(1) : '0.0'

  const metrics = [
    { label: 'Active Courses', value: activeCourses, icon: BookOpen, color: '#A855F7' },
    { label: 'Total Enrolled', value: totalEnrolled.toLocaleString(), icon: Users, color: '#3B82F6' },
    { label: 'Avg Rating', value: avgRating, icon: Star, color: '#F59E0B' },
    { label: 'Categories', value: new Set(courses.map(c => c.category)).size, icon: GraduationCap, color: '#10B981' },
  ]

  if (isLoading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
        <div style={{ width: 40, height: 40, border: '3px solid #A855F7', borderTop: '3px solid transparent', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
        <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
      </div>
    )
  }

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 32 }}>
        <div>
          <h2 style={{ fontSize: 28, fontWeight: 700, color: '#fff', marginBottom: 4 }}>Courses Management</h2>
          <p style={{ fontSize: 13, color: '#6B7280', margin: 0 }}>Manage, analyze, and scale your curriculum</p>
        </div>
        <button style={{
          padding: '10px 20px', borderRadius: 12, border: 'none', cursor: 'pointer',
          background: 'linear-gradient(135deg, #A855F7, #D946EF)', color: '#fff',
          fontWeight: 600, fontSize: 13, display: 'flex', alignItems: 'center', gap: 8,
          boxShadow: '0 4px 12px rgba(168,85,247,0.3)', fontFamily: 'inherit',
        }}><Plus size={16} /> Add Course</button>
      </div>

      {/* Metric Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
        {metrics.map((m, i) => {
          const Icon = m.icon
          return (
            <div key={i} style={{ background: '#13121E', border: '1px solid #2A2840', borderRadius: 16, padding: 20, position: 'relative', overflow: 'hidden' }}>
              <div style={{ position: 'absolute', top: -16, right: -16, width: 60, height: 60, background: m.color, borderRadius: '50%', filter: 'blur(30px)', opacity: 0.12 }} />
              <div style={{ position: 'relative', zIndex: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <p style={{ fontSize: 11, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: 1, margin: 0 }}>{m.label}</p>
                  <p style={{ fontSize: 24, fontWeight: 700, color: '#fff', margin: '4px 0 0 0' }}>{m.value}</p>
                </div>
                <div style={{ width: 40, height: 40, borderRadius: 12, background: m.color, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Icon size={20} color="#fff" />
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Search */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ position: 'relative', maxWidth: 320 }}>
          <Search size={16} color="#6B7280" style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)' }} />
          <input type="text" placeholder="Search courses..." value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            style={{ width: '100%', background: '#13121E', border: '1px solid #2A2840', borderRadius: 8, padding: '8px 16px 8px 36px', fontSize: 13, color: '#D1D5DB', outline: 'none', fontFamily: 'inherit' }}
          />
        </div>
      </div>

      {/* Course Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 16 }}>
        {filtered.length === 0 ? (
          <div style={{ gridColumn: '1 / -1', padding: '48px 0', textAlign: 'center', color: '#6B7280', fontSize: 14 }}>No courses found.</div>
        ) : (
          filtered.map(course => {
            const sc = STATUS_COLORS[course.status] || STATUS_COLORS.active
            return (
              <div key={course.id} style={{
                background: '#13121E', border: '1px solid #2A2840', borderRadius: 16,
                padding: 20, cursor: 'pointer', transition: 'border-color 0.15s',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                      <h3 style={{ fontSize: 14, fontWeight: 600, color: '#E5E7EB', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{course.title}</h3>
                      <span style={{
                        padding: '2px 8px', borderRadius: 12, fontSize: 10, fontWeight: 600,
                        background: sc.bg, color: sc.color, border: `1px solid ${sc.border}`,
                        whiteSpace: 'nowrap', flexShrink: 0,
                      }}>{course.status}</span>
                    </div>
                    <p style={{ fontSize: 12, color: '#6B7280', margin: '0 0 12px 0' }}>{course.instructor}</p>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 12, color: '#6B7280' }}>
                        <Users size={14} /> {course.enrolled.toLocaleString()} enrolled
                      </span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 12, color: '#FBBF24' }}>
                        <Star size={14} style={{ fill: '#FBBF24' }} /> {course.rating}
                      </span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 12, color: '#6B7280' }}>
                        <Clock size={14} /> {course.duration}
                      </span>
                    </div>
                  </div>
                  <button style={{ padding: 4, background: 'transparent', border: 'none', cursor: 'pointer', borderRadius: 8 }}>
                    <MoreHorizontal size={16} color="#6B7280" />
                  </button>
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
