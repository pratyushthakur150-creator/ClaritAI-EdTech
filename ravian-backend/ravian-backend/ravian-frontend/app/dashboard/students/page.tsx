"use client"

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import apiClient from '@/lib/api'
import { Search, Users, AlertTriangle, TrendingUp, ChevronLeft, ChevronRight, MoreHorizontal, BookOpen, Flame } from 'lucide-react'

interface Student {
  id: string; name: string; email: string; course: string
  progress: number; attendance: number; risk: string; lastActive: string
  engagement_score: number; modules_completed: number; modules_total: number
  study_hours: number; login_streak: number; current_module: string
}

export default function StudentsPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const perPage = 10

  const { data, isLoading } = useQuery({
    queryKey: ['students'],
    queryFn: async () => {
      const res = await apiClient.get(`/api/v1/students`)
      return res.data
    },
  })

  const rawStudents = data?.students || []
  const summary = data?.summary || {}
  const students: Student[] = rawStudents.map((s: any) => ({
    id: s.id?.toString() || '',
    name: s.name || s.full_name || `${s.first_name || ''} ${s.last_name || ''}`.trim() || 'Unknown',
    email: s.email || '',
    course: s.course || s.course_name || 'General',
    progress: s.progress ?? s.completion_percentage ?? 0,
    attendance: s.attendance ?? 0,
    risk: s.risk || s.risk_level || 'low',
    lastActive: s.lastActive || s.last_active || '-',
    engagement_score: s.engagement_score ?? 0,
    modules_completed: s.modules_completed ?? 0,
    modules_total: s.modules_total ?? 0,
    study_hours: s.study_hours ?? 0,
    login_streak: s.login_streak ?? 0,
    current_module: s.current_module || '',
  }))

  const filtered = students.filter(s =>
    s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    s.course.toLowerCase().includes(searchQuery.toLowerCase())
  )
  const totalPages = Math.ceil(filtered.length / perPage)
  const paginated = filtered.slice((currentPage - 1) * perPage, currentPage * perPage)

  const avgProgress = summary.avg_progress ?? (students.length > 0 ? Math.round(students.reduce((a: number, s: Student) => a + s.progress, 0) / students.length) : 0)
  const atRisk = summary.at_risk_count ?? students.filter((s: Student) => s.risk === 'high' || s.risk === 'critical').length
  const avgEngagement = summary.avg_engagement ?? (students.length > 0 ? Math.round(students.reduce((a: number, s: Student) => a + s.engagement_score, 0) / students.length) : 0)

  const riskStyle = (risk: string) => {
    switch (risk) {
      case 'high': case 'critical': return { bg: 'rgba(239,68,68,0.1)', color: '#F87171', border: 'rgba(239,68,68,0.2)' }
      case 'medium': return { bg: 'rgba(245,158,11,0.1)', color: '#FBBF24', border: 'rgba(245,158,11,0.2)' }
      default: return { bg: 'rgba(16,185,129,0.1)', color: '#34D399', border: 'rgba(16,185,129,0.2)' }
    }
  }

  // Progress heatmap data (group by course)
  const courseMap: Record<string, { total: number; count: number; risk: number }> = {}
  students.forEach(s => {
    if (!courseMap[s.course]) courseMap[s.course] = { total: 0, count: 0, risk: 0 }
    courseMap[s.course].total += s.progress
    courseMap[s.course].count++
    if (s.risk === 'high' || s.risk === 'critical') courseMap[s.course].risk++
  })
  const heatmapData = Object.entries(courseMap).map(([course, d]) => ({
    course,
    avg: Math.round(d.total / d.count),
    count: d.count,
    risk: d.risk,
  })).sort((a, b) => b.avg - a.avg)

  const totalStudyHrs = Math.round(students.reduce((a: number, s: Student) => a + s.study_hours, 0))

  const metrics = [
    { label: 'Total Students', value: students.length, icon: Users, color: '#A855F7' },
    { label: 'At Risk', value: atRisk, icon: AlertTriangle, color: '#EF4444' },
    { label: 'Avg Progress', value: `${avgProgress}%`, icon: TrendingUp, color: '#10B981' },
    { label: 'Study Hours', value: totalStudyHrs > 0 ? totalStudyHrs.toLocaleString() : `${avgProgress}%`, icon: Flame, color: '#F59E0B' },
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
      <div style={{ marginBottom: 32 }}>
        <h2 style={{ fontSize: 28, fontWeight: 700, color: '#fff', marginBottom: 4 }}>Student Monitoring</h2>
        <p style={{ fontSize: 13, color: '#6B7280' }}>Track student progress and identify at-risk learners</p>
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
                  <p style={{ fontSize: 24, fontWeight: 700, color: '#fff', marginTop: 4, margin: '4px 0 0 0' }}>{m.value}</p>
                </div>
                <div style={{ width: 40, height: 40, borderRadius: 12, background: m.color, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Icon size={20} color="#fff" />
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Engagement Heatmap */}
      {heatmapData.length > 0 && (
        <div style={{ background: '#13121E', border: '1px solid #2A2840', borderRadius: 16, padding: 24, marginBottom: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
            <div style={{ width: 36, height: 36, borderRadius: 10, background: 'linear-gradient(135deg, #A855F7, #D946EF)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <BookOpen size={18} color="#fff" />
            </div>
            <h3 style={{ fontWeight: 600, color: '#fff', fontSize: 16, margin: 0 }}>Course Progress Heatmap</h3>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: `repeat(${Math.min(heatmapData.length, 6)}, 1fr)`, gap: 12 }}>
            {heatmapData.map((item, i) => {
              const intensity = Math.min(item.avg / 100, 1)
              const hue = intensity > 0.6 ? 142 : intensity > 0.3 ? 45 : 0 // green/yellow/red
              return (
                <div key={i} style={{
                  background: `hsla(${hue}, 70%, 50%, ${0.1 + intensity * 0.2})`,
                  border: `1px solid hsla(${hue}, 70%, 50%, 0.2)`,
                  borderRadius: 12, padding: 16, textAlign: 'center',
                }}>
                  <p style={{ fontSize: 11, color: '#9CA3AF', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5, margin: '0 0 8px 0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {item.course.length > 18 ? item.course.slice(0, 16) + '…' : item.course}
                  </p>
                  <p style={{ fontSize: 28, fontWeight: 700, color: '#fff', margin: '0 0 4px 0' }}>{item.avg}</p>
                  <p style={{ fontSize: 10, color: '#6B7280', margin: 0 }}>{item.count} students{item.risk > 0 ? ` · ${item.risk} at risk` : ''}</p>
                </div>
              )
            })}
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 16, marginTop: 12, fontSize: 10, color: '#6B7280' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><span style={{ width: 12, height: 8, borderRadius: 2, background: 'hsla(0, 70%, 50%, 0.3)' }} /> Low (&lt;30)</span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><span style={{ width: 12, height: 8, borderRadius: 2, background: 'hsla(45, 70%, 50%, 0.3)' }} /> Medium (30-60)</span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><span style={{ width: 12, height: 8, borderRadius: 2, background: 'hsla(142, 70%, 50%, 0.3)' }} /> High (&gt;60)</span>
          </div>
        </div>
      )}

      {/* Students Table */}
      <div style={{ background: '#13121E', border: '1px solid #2A2840', borderRadius: 16, overflow: 'hidden' }}>
        <div style={{ padding: '16px 24px', borderBottom: '1px solid rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
          <div style={{ position: 'relative', flex: 1, maxWidth: 320 }}>
            <Search size={16} color="#6B7280" style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)' }} />
            <input type="text" placeholder="Search students..." value={searchQuery}
              onChange={e => { setSearchQuery(e.target.value); setCurrentPage(1) }}
              style={{ width: '100%', background: '#0B0B12', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, padding: '8px 16px 8px 36px', fontSize: 13, color: '#D1D5DB', outline: 'none', fontFamily: 'inherit' }}
            />
          </div>
          <p style={{ fontSize: 12, color: '#6B7280', margin: 0 }}>{filtered.length} students</p>
        </div>

        {/* Table Header */}
        <div style={{ display: 'grid', gridTemplateColumns: '2.5fr 1.5fr 1.2fr 0.8fr 1fr 0.5fr', padding: '10px 24px', borderBottom: '1px solid rgba(255,255,255,0.05)', background: 'rgba(255,255,255,0.02)' }}>
          {['Student', 'Course', 'Progress', 'Risk', 'Last Active', ''].map((h, i) => (
            <span key={i} style={{ fontSize: 10, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: 1 }}>{h}</span>
          ))}
        </div>

        {/* Table Rows */}
        <div>
          {paginated.length === 0 ? (
            <div style={{ padding: '48px 0', textAlign: 'center', color: '#6B7280', fontSize: 14 }}>No students found.</div>
          ) : (
            paginated.map(s => {
              const rs = riskStyle(s.risk)
              return (
                <div key={s.id} style={{
                  display: 'grid', gridTemplateColumns: '2.5fr 1.5fr 1.2fr 0.8fr 1fr 0.5fr',
                  padding: '14px 24px', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.03)',
                  cursor: 'pointer', transition: 'background 0.15s',
                }}>
                  {/* Student */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div style={{ width: 36, height: 36, borderRadius: '50%', background: 'linear-gradient(135deg, #A855F7, #D946EF)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 13, fontWeight: 700, flexShrink: 0 }}>
                      {s.name.charAt(0)}
                    </div>
                    <div style={{ minWidth: 0 }}>
                      <p style={{ fontSize: 13, fontWeight: 600, color: '#E5E7EB', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{s.name}</p>
                      <p style={{ fontSize: 11, color: '#6B7280', margin: '2px 0 0 0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{s.email}</p>
                    </div>
                  </div>

                  {/* Course */}
                  <div style={{ fontSize: 12, color: '#9CA3AF', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{s.course}</div>

                  {/* Progress */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ width: 64, height: 6, background: '#1F2937', borderRadius: 3, overflow: 'hidden' }}>
                      <div style={{
                        height: '100%', borderRadius: 3,
                        background: s.progress > 70 ? 'linear-gradient(90deg, #10B981, #34D399)' : s.progress > 40 ? 'linear-gradient(90deg, #F59E0B, #FBBF24)' : 'linear-gradient(90deg, #EF4444, #F87171)',
                        width: `${s.progress}%`, transition: 'width 0.5s ease',
                      }} />
                    </div>
                    <span style={{ fontSize: 12, fontWeight: 600, color: '#D1D5DB', minWidth: 32 }}>{Math.round(s.progress)}%</span>
                  </div>

                  {/* Risk */}
                  <span style={{ padding: '3px 10px', borderRadius: 12, fontSize: 11, fontWeight: 600, background: rs.bg, color: rs.color, border: `1px solid ${rs.border}`, display: 'inline-block', width: 'fit-content' }}>
                    {s.risk}
                  </span>

                  {/* Last Active */}
                  <span style={{ fontSize: 12, color: '#6B7280' }}>{s.lastActive}</span>

                  {/* Actions */}
                  <button style={{ padding: 4, background: 'transparent', border: 'none', cursor: 'pointer', borderRadius: 8 }}>
                    <MoreHorizontal size={16} color="#6B7280" />
                  </button>
                </div>
              )
            })
          )}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div style={{ padding: '12px 24px', borderTop: '1px solid rgba(255,255,255,0.05)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <p style={{ fontSize: 12, color: '#6B7280', margin: 0 }}>Page {currentPage} of {totalPages}</p>
            <div style={{ display: 'flex', gap: 4 }}>
              <button onClick={() => setCurrentPage(p => Math.max(1, p - 1))} disabled={currentPage === 1} style={{ padding: 6, borderRadius: 8, background: 'transparent', border: 'none', cursor: 'pointer', opacity: currentPage === 1 ? 0.4 : 1 }}>
                <ChevronLeft size={16} color="#9CA3AF" />
              </button>
              <button onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))} disabled={currentPage === totalPages} style={{ padding: 6, borderRadius: 8, background: 'transparent', border: 'none', cursor: 'pointer', opacity: currentPage === totalPages ? 0.4 : 1 }}>
                <ChevronRight size={16} color="#9CA3AF" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
