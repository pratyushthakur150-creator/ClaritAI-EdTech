"use client"

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import apiClient from '@/lib/api'
import { Calendar, Clock, Video, Plus, MoreHorizontal, ArrowUpRight, Users, CheckCircle, XCircle, ChevronLeft, ChevronRight } from 'lucide-react'

interface Demo {
    id: string; title: string; leadName: string; date: string; time: string
    duration: string; status: string; platform: string; outcome: string; nextSteps: string
}

const STATUS_LABELS: Record<string, string> = {
    upcoming: 'Upcoming', live: 'Live', completed: 'Completed',
    cancelled: 'Cancelled', no_show: 'No Show', scheduled: 'Scheduled',
}
const STATUS_COLORS: Record<string, { bg: string; color: string; border: string }> = {
    upcoming: { bg: 'rgba(59,130,246,0.1)', color: '#60A5FA', border: 'rgba(59,130,246,0.2)' },
    scheduled: { bg: 'rgba(59,130,246,0.1)', color: '#60A5FA', border: 'rgba(59,130,246,0.2)' },
    live: { bg: 'rgba(16,185,129,0.1)', color: '#34D399', border: 'rgba(16,185,129,0.2)' },
    completed: { bg: 'rgba(107,114,128,0.1)', color: '#9CA3AF', border: 'rgba(107,114,128,0.2)' },
    cancelled: { bg: 'rgba(239,68,68,0.1)', color: '#F87171', border: 'rgba(239,68,68,0.2)' },
    no_show: { bg: 'rgba(245,158,11,0.1)', color: '#FBBF24', border: 'rgba(245,158,11,0.2)' },
}

export default function DemosPage() {
    const [currentPage, setCurrentPage] = useState(1)
    const perPage = 10

    const { data, isLoading } = useQuery({
        queryKey: ['demos'],
        queryFn: async () => {
            try { const res = await apiClient.get(`/api/v1/demos`); return res.data } catch { return null }
        },
    })

    const rawDemos = data?.demos || data?.data || []
    const demos: Demo[] = rawDemos.map((d: any) => {
        const scheduledAt = d.scheduled_at ? new Date(d.scheduled_at) : null
        const outcome = (d.outcome || '').toLowerCase()
        let status = 'upcoming'
        if (outcome === 'completed') status = 'completed'
        else if (outcome === 'cancelled') status = 'cancelled'
        else if (outcome === 'no_show') status = 'no_show'
        else if (d.completed) status = 'completed'

        return {
            id: d.id?.toString() || '',
            title: d.notes || 'Demo Session',
            leadName: d.lead_name || `Lead ${d.lead_id?.toString()?.slice(0, 8) || ''}`,
            date: scheduledAt ? scheduledAt.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : '-',
            time: scheduledAt ? scheduledAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '',
            duration: d.duration_minutes ? `${d.duration_minutes} min` : '60 min',
            status,
            platform: d.platform || 'Zoom',
            outcome: outcome || '-',
            nextSteps: d.next_steps || '',
        }
    })

    const completedCount = demos.filter(d => d.status === 'completed').length
    const upcomingCount = demos.filter(d => d.status === 'upcoming' || d.status === 'scheduled').length
    const noShowCount = demos.filter(d => d.status === 'no_show').length
    const convRate = demos.length > 0 ? Math.round((completedCount / demos.length) * 100) : 0

    const totalPages = Math.ceil(demos.length / perPage)
    const paginated = demos.slice((currentPage - 1) * perPage, currentPage * perPage)

    const metrics = [
        { label: 'Total Demos', value: demos.length, icon: Video, color: '#A855F7' },
        { label: 'Completed', value: completedCount, icon: CheckCircle, color: '#10B981' },
        { label: 'Upcoming', value: upcomingCount, icon: Calendar, color: '#3B82F6' },
        { label: 'No Shows', value: noShowCount, icon: XCircle, color: '#EF4444' },
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
                    <h2 style={{ fontSize: 28, fontWeight: 700, color: '#fff', marginBottom: 4 }}>Demos & Meetings</h2>
                    <p style={{ fontSize: 13, color: '#6B7280', margin: 0 }}>Schedule, manage, and track demo sessions</p>
                </div>
                <button style={{
                    padding: '10px 20px', borderRadius: 12, border: 'none', cursor: 'pointer',
                    background: 'linear-gradient(135deg, #A855F7, #D946EF)', color: '#fff',
                    fontWeight: 600, fontSize: 13, display: 'flex', alignItems: 'center', gap: 8,
                    boxShadow: '0 4px 12px rgba(168,85,247,0.3)', fontFamily: 'inherit',
                }}><Plus size={16} /> Schedule Demo</button>
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

            {/* Demos Table */}
            <div style={{ background: '#13121E', border: '1px solid #2A2840', borderRadius: 16, overflow: 'hidden' }}>
                {/* Table Header */}
                <div style={{ display: 'grid', gridTemplateColumns: '2fr 1.5fr 1fr 1fr 1fr 1fr 40px', padding: '10px 24px', borderBottom: '1px solid rgba(255,255,255,0.05)', background: 'rgba(255,255,255,0.02)' }}>
                    {['Lead', 'Date & Time', 'Duration', 'Platform', 'Status', 'Outcome', ''].map((h, i) => (
                        <span key={i} style={{ fontSize: 10, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: 1 }}>{h}</span>
                    ))}
                </div>

                {/* Table Rows */}
                <div>
                    {paginated.length === 0 ? (
                        <div style={{ padding: '48px 0', textAlign: 'center', color: '#6B7280', fontSize: 14 }}>No demos scheduled.</div>
                    ) : (
                        paginated.map(demo => {
                            const sc = STATUS_COLORS[demo.status] || STATUS_COLORS.upcoming
                            return (
                                <div key={demo.id} style={{
                                    display: 'grid', gridTemplateColumns: '2fr 1.5fr 1fr 1fr 1fr 1fr 40px',
                                    padding: '14px 24px', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.03)',
                                    cursor: 'pointer', transition: 'background 0.15s',
                                }}>
                                    {/* Lead */}
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                        <div style={{ width: 36, height: 36, borderRadius: '50%', background: 'linear-gradient(135deg, #A855F7, #D946EF)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 13, fontWeight: 700, flexShrink: 0 }}>
                                            {demo.leadName.charAt(0)}
                                        </div>
                                        <div style={{ minWidth: 0 }}>
                                            <p style={{ fontSize: 13, fontWeight: 600, color: '#E5E7EB', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{demo.leadName}</p>
                                            <p style={{ fontSize: 11, color: '#6B7280', margin: '2px 0 0 0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{demo.title}</p>
                                        </div>
                                    </div>

                                    {/* Date & Time */}
                                    <div>
                                        <p style={{ fontSize: 12, color: '#D1D5DB', margin: 0 }}>{demo.date}</p>
                                        <p style={{ fontSize: 11, color: '#6B7280', margin: '2px 0 0 0' }}>{demo.time}</p>
                                    </div>

                                    {/* Duration */}
                                    <span style={{ fontSize: 12, color: '#9CA3AF' }}>{demo.duration}</span>

                                    {/* Platform */}
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                        <Video size={14} color="#6B7280" />
                                        <span style={{ fontSize: 12, color: '#9CA3AF', textTransform: 'capitalize' }}>{demo.platform}</span>
                                    </div>

                                    {/* Status */}
                                    <div>
                                        <span style={{
                                            padding: '3px 10px', borderRadius: 12, fontSize: 10, fontWeight: 600,
                                            background: sc.bg, color: sc.color, border: `1px solid ${sc.border}`,
                                            whiteSpace: 'nowrap',
                                        }}>{STATUS_LABELS[demo.status] || demo.status}</span>
                                    </div>

                                    {/* Outcome */}
                                    <span style={{ fontSize: 12, color: '#6B7280', textTransform: 'capitalize' }}>{demo.outcome}</span>

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
                        <p style={{ fontSize: 12, color: '#6B7280', margin: 0 }}>Page {currentPage} of {totalPages} · {demos.length} demos</p>
                        <div style={{ display: 'flex', gap: 4 }}>
                            <button onClick={() => setCurrentPage(p => Math.max(1, p - 1))} disabled={currentPage === 1}
                                style={{ padding: 6, borderRadius: 8, background: 'transparent', border: 'none', cursor: 'pointer', opacity: currentPage === 1 ? 0.4 : 1 }}>
                                <ChevronLeft size={16} color="#9CA3AF" />
                            </button>
                            <button onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))} disabled={currentPage === totalPages}
                                style={{ padding: 6, borderRadius: 8, background: 'transparent', border: 'none', cursor: 'pointer', opacity: currentPage === totalPages ? 0.4 : 1 }}>
                                <ChevronRight size={16} color="#9CA3AF" />
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
