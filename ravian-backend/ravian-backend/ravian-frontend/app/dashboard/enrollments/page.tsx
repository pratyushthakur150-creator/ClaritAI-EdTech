"use client"

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import apiClient from '@/lib/api'
import { GraduationCap, Users, IndianRupee, CheckCircle, Search, MoreHorizontal, ChevronLeft, ChevronRight } from 'lucide-react'

interface Enrollment {
  id: string; studentName: string; email: string; course: string
  enrolledDate: string; status: string; paymentStatus: string; amount: number
}

const STATUS_COLORS: Record<string, { bg: string; color: string; border: string }> = {
  active: { bg: 'rgba(16,185,129,0.1)', color: '#34D399', border: 'rgba(16,185,129,0.2)' },
  completed: { bg: 'rgba(59,130,246,0.1)', color: '#60A5FA', border: 'rgba(59,130,246,0.2)' },
  dropped: { bg: 'rgba(239,68,68,0.1)', color: '#F87171', border: 'rgba(239,68,68,0.2)' },
  pending: { bg: 'rgba(245,158,11,0.1)', color: '#FBBF24', border: 'rgba(245,158,11,0.2)' },
}
const PAY_COLORS: Record<string, { bg: string; color: string; border: string }> = {
  paid: { bg: 'rgba(16,185,129,0.1)', color: '#34D399', border: 'rgba(16,185,129,0.2)' },
  partial: { bg: 'rgba(245,158,11,0.1)', color: '#FBBF24', border: 'rgba(245,158,11,0.2)' },
  pending: { bg: 'rgba(239,68,68,0.1)', color: '#F87171', border: 'rgba(239,68,68,0.2)' },
  failed: { bg: 'rgba(239,68,68,0.1)', color: '#F87171', border: 'rgba(239,68,68,0.2)' },
  cancelled: { bg: 'rgba(107,114,128,0.1)', color: '#9CA3AF', border: 'rgba(107,114,128,0.2)' },
  refunded: { bg: 'rgba(107,114,128,0.1)', color: '#9CA3AF', border: 'rgba(107,114,128,0.2)' },
}

export default function EnrollmentsPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const perPage = 10

  const { data, isLoading } = useQuery({
    queryKey: ['enrollments'],
    queryFn: async () => { try { const res = await apiClient.get(`/api/v1/enrollments`); return res.data } catch { return null } },
  })

  const rawEnrollments = data?.enrollments || data?.data || []
  const enrollments: Enrollment[] = rawEnrollments.map((e: any) => ({
    id: e.id?.toString() || '',
    studentName: e.lead?.name || 'Unknown',
    email: e.lead?.email || '',
    course: e.course?.name || 'N/A',
    enrolledDate: e.enrolled_at || '',
    status: e.payment_status === 'PAID' || e.payment_status === 'COMPLETED' ? 'active' : (e.payment_status === 'FAILED' || e.payment_status === 'CANCELLED' ? 'dropped' : 'pending'),
    paymentStatus: (e.payment_status || 'pending').toLowerCase(),
    amount: e.total_amount || 0,
  }))

  const filtered = enrollments.filter(e =>
    e.studentName.toLowerCase().includes(searchQuery.toLowerCase()) ||
    e.course.toLowerCase().includes(searchQuery.toLowerCase())
  )
  const totalPages = Math.ceil(filtered.length / perPage)
  const paginated = filtered.slice((currentPage - 1) * perPage, currentPage * perPage)
  const totalRevenue = enrollments.reduce((s, e) => s + e.amount, 0)
  const activeCount = enrollments.filter(e => e.status === 'active').length
  const paidCount = enrollments.filter(e => e.paymentStatus === 'paid').length
  const paidRate = enrollments.length > 0 ? Math.round((paidCount / enrollments.length) * 100) : 0

  const fmtDate = (d: string) => {
    if (!d) return '-'
    try {
      const dt = new Date(d)
      return dt.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
    } catch { return '-' }
  }

  const metrics = [
    { label: 'Total Enrollments', value: enrollments.length, icon: GraduationCap, color: '#A855F7' },
    { label: 'Active', value: activeCount, icon: Users, color: '#3B82F6' },
    { label: 'Revenue', value: `₹${totalRevenue.toLocaleString('en-IN')}`, icon: IndianRupee, color: '#10B981' },
    { label: 'Paid Rate', value: `${paidRate}%`, icon: CheckCircle, color: '#F59E0B' },
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
      <div style={{ marginBottom: 32 }}>
        <h2 style={{ fontSize: 28, fontWeight: 700, color: '#fff', marginBottom: 4 }}>Enrollments</h2>
        <p style={{ fontSize: 13, color: '#6B7280' }}>Track student enrollments and payments</p>
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

      {/* Enrollments Table */}
      <div style={{ background: '#13121E', border: '1px solid #2A2840', borderRadius: 16, overflow: 'hidden' }}>
        <div style={{ padding: '16px 24px', borderBottom: '1px solid rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
          <div style={{ position: 'relative', flex: 1, maxWidth: 320 }}>
            <Search size={16} color="#6B7280" style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)' }} />
            <input type="text" placeholder="Search enrollments..." value={searchQuery}
              onChange={e => { setSearchQuery(e.target.value); setCurrentPage(1) }}
              style={{ width: '100%', background: '#0B0B12', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, padding: '8px 16px 8px 36px', fontSize: 13, color: '#D1D5DB', outline: 'none', fontFamily: 'inherit' }}
            />
          </div>
          <p style={{ fontSize: 12, color: '#6B7280', margin: 0 }}>{filtered.length} enrollments</p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '2fr 2fr 0.8fr 0.8fr 1fr 1fr 40px', padding: '10px 24px', borderBottom: '1px solid rgba(255,255,255,0.05)', background: 'rgba(255,255,255,0.02)' }}>
          {['Student', 'Course', 'Status', 'Payment', 'Amount', 'Date', ''].map((h, i) => (
            <span key={i} style={{ fontSize: 10, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: 1 }}>{h}</span>
          ))}
        </div>

        <div>
          {paginated.length === 0 ? (
            <div style={{ padding: '48px 0', textAlign: 'center', color: '#6B7280', fontSize: 14 }}>No enrollments found.</div>
          ) : (
            paginated.map(e => {
              const sc = STATUS_COLORS[e.status] || STATUS_COLORS.pending
              const pc = PAY_COLORS[e.paymentStatus] || PAY_COLORS.pending
              return (
                <div key={e.id} style={{
                  display: 'grid', gridTemplateColumns: '2fr 2fr 0.8fr 0.8fr 1fr 1fr 40px',
                  padding: '14px 24px', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.03)',
                  cursor: 'pointer', transition: 'background 0.15s',
                }}>
                  {/* Student */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'linear-gradient(135deg, #A855F7, #D946EF)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 12, fontWeight: 700, flexShrink: 0 }}>
                      {e.studentName.charAt(0)}
                    </div>
                    <div style={{ minWidth: 0 }}>
                      <p style={{ fontSize: 13, fontWeight: 600, color: '#E5E7EB', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{e.studentName}</p>
                      <p style={{ fontSize: 10, color: '#6B7280', margin: '2px 0 0 0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{e.email}</p>
                    </div>
                  </div>

                  {/* Course */}
                  <span style={{ fontSize: 12, color: '#9CA3AF', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', paddingRight: 8 }}>{e.course}</span>

                  {/* Status */}
                  <div>
                    <span style={{ padding: '3px 8px', borderRadius: 12, fontSize: 10, fontWeight: 600, background: sc.bg, color: sc.color, border: `1px solid ${sc.border}`, textTransform: 'capitalize' }}>
                      {e.status}
                    </span>
                  </div>

                  {/* Payment */}
                  <div>
                    <span style={{ padding: '3px 8px', borderRadius: 12, fontSize: 10, fontWeight: 600, background: pc.bg, color: pc.color, border: `1px solid ${pc.border}`, textTransform: 'capitalize' }}>
                      {e.paymentStatus}
                    </span>
                  </div>

                  {/* Amount */}
                  <span style={{ fontSize: 13, fontWeight: 600, color: '#fff' }}>₹{e.amount.toLocaleString('en-IN')}</span>

                  {/* Date */}
                  <span style={{ fontSize: 12, color: '#6B7280' }}>{fmtDate(e.enrolledDate)}</span>

                  {/* Actions */}
                  <button style={{ padding: 4, background: 'transparent', border: 'none', cursor: 'pointer', borderRadius: 8 }}>
                    <MoreHorizontal size={16} color="#6B7280" />
                  </button>
                </div>
              )
            })
          )}
        </div>

        {totalPages > 1 && (
          <div style={{ padding: '12px 24px', borderTop: '1px solid rgba(255,255,255,0.05)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <p style={{ fontSize: 12, color: '#6B7280', margin: 0 }}>Page {currentPage} of {totalPages} · {filtered.length} enrollments</p>
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
