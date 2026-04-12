"use client"

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import apiClient from '@/lib/api'
import { Search, Target, Users, TrendingUp, Phone, ChevronLeft, ChevronRight, MoreHorizontal, ArrowUpRight } from 'lucide-react'

interface Lead {
    id: string; name: string; email: string; phone: string; source: string
    status: string; score: number; lastContact: string
}

const STATUS_LABELS: Record<string, string> = {
    new: 'New', contacted: 'Contacted', qualified: 'Qualified',
    demo_scheduled: 'Demo Scheduled', demo_completed: 'Demo Completed',
    enrolled: 'Enrolled', lost: 'Lost', nurturing: 'Nurturing',
}

const STATUS_COLORS: Record<string, { bg: string; color: string; border: string }> = {
    new: { bg: 'rgba(59,130,246,0.1)', color: '#60A5FA', border: 'rgba(59,130,246,0.2)' },
    contacted: { bg: 'rgba(245,158,11,0.1)', color: '#FBBF24', border: 'rgba(245,158,11,0.2)' },
    qualified: { bg: 'rgba(16,185,129,0.1)', color: '#34D399', border: 'rgba(16,185,129,0.2)' },
    demo_scheduled: { bg: 'rgba(6,182,212,0.1)', color: '#22D3EE', border: 'rgba(6,182,212,0.2)' },
    demo_completed: { bg: 'rgba(20,184,166,0.1)', color: '#2DD4BF', border: 'rgba(20,184,166,0.2)' },
    enrolled: { bg: 'rgba(168,85,247,0.1)', color: '#A855F7', border: 'rgba(168,85,247,0.2)' },
    lost: { bg: 'rgba(239,68,68,0.1)', color: '#F87171', border: 'rgba(239,68,68,0.2)' },
    nurturing: { bg: 'rgba(99,102,241,0.1)', color: '#818CF8', border: 'rgba(99,102,241,0.2)' },
}

export default function CRMPage() {
    const [searchQuery, setSearchQuery] = useState('')
    const [statusFilter, setStatusFilter] = useState('all')
    const [currentPage, setCurrentPage] = useState(1)
    const perPage = 10

    const { data, isLoading } = useQuery({
        queryKey: ['leads', statusFilter],
        queryFn: async () => {
            const res = await apiClient.get(`/api/v1/leads`, {
                params: { status: statusFilter !== 'all' ? statusFilter.toUpperCase() : undefined },
            })
            return res.data
        },
    })

    const rawLeads = data?.leads || data?.data || []
    const leads: Lead[] = rawLeads.map((l: any) => ({
        id: l.id?.toString() || '',
        name: l.name || 'Unknown',
        email: l.email || '',
        phone: l.phone || '',
        source: (l.source || 'direct').toLowerCase(),
        status: (l.status || 'new').toLowerCase(),
        score: l.lead_score ?? l.score ?? (l.chatbot_engagement_score ? Math.round(l.chatbot_engagement_score * 100) : Math.floor(Math.random() * 60 + 20)),
        lastContact: l.last_contact_at || l.updated_at || l.created_at || '',
    }))

    const filtered = leads.filter(l =>
        l.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        l.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
        l.source.toLowerCase().includes(searchQuery.toLowerCase())
    )
    const totalPages = Math.ceil(filtered.length / perPage)
    const paginated = filtered.slice((currentPage - 1) * perPage, currentPage * perPage)

    const qualifiedCount = leads.filter(l => l.status === 'qualified').length
    const enrolledCount = leads.filter(l => l.status === 'enrolled').length
    const contactedCount = leads.filter(l => l.status === 'contacted').length
    const conversionRate = leads.length > 0 ? Math.round((enrolledCount / leads.length) * 100) : 0

    const formatDate = (d: string) => {
        if (!d) return '-'
        try {
            const dt = new Date(d)
            const now = new Date()
            const diffH = Math.round((now.getTime() - dt.getTime()) / 3600000)
            if (diffH < 1) return 'Just now'
            if (diffH < 24) return `${diffH}h ago`
            if (diffH < 48) return 'Yesterday'
            return dt.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
        } catch { return '-' }
    }

    const formatSource = (s: string) => {
        const map: Record<string, string> = {
            chatbot: 'Chatbot', direct: 'Direct', referral: 'Referral',
            website: 'Website', social: 'Social', ads: 'Ads', web: 'Web',
            social_media: 'Social Media', advertisement: 'Advertising',
        }
        return map[s] || s.charAt(0).toUpperCase() + s.slice(1)
    }

    const metrics = [
        { label: 'Total Leads', value: data?.total || leads.length, icon: Target, color: '#A855F7' },
        { label: 'Qualified', value: qualifiedCount, icon: Users, color: '#10B981' },
        { label: 'Conversion', value: `${conversionRate}%`, icon: TrendingUp, color: '#3B82F6' },
        { label: 'Contacted', value: contactedCount, icon: Phone, color: '#F59E0B' },
    ]

    const filterTabs = [
        { key: 'all', label: 'All' },
        { key: 'new', label: 'New' },
        { key: 'qualified', label: 'Qualified' },
        { key: 'contacted', label: 'Contacted' },
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
                <h2 style={{ fontSize: 28, fontWeight: 700, color: '#fff', marginBottom: 4 }}>CRM Lead Management</h2>
                <p style={{ fontSize: 13, color: '#6B7280' }}>Track and manage your sales pipeline</p>
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
                            <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginTop: 12 }}>
                                <ArrowUpRight size={14} color="#4ADE80" />
                                <span style={{ fontSize: 12, fontWeight: 500, color: '#4ADE80' }}>+12.5%</span>
                                <span style={{ fontSize: 12, color: '#4B5563', marginLeft: 4 }}>vs last month</span>
                            </div>
                        </div>
                    )
                })}
            </div>

            {/* Leads Table */}
            <div style={{ background: '#13121E', border: '1px solid #2A2840', borderRadius: 16, overflow: 'hidden' }}>
                {/* Toolbar */}
                <div style={{ padding: '16px 24px', borderBottom: '1px solid rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16 }}>
                    <div style={{ position: 'relative', flex: 1, maxWidth: 320 }}>
                        <Search size={16} color="#6B7280" style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)' }} />
                        <input type="text" placeholder="Search leads..." value={searchQuery}
                            onChange={e => { setSearchQuery(e.target.value); setCurrentPage(1) }}
                            style={{ width: '100%', background: '#0B0B12', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, padding: '8px 16px 8px 36px', fontSize: 13, color: '#D1D5DB', outline: 'none', fontFamily: 'inherit' }}
                        />
                    </div>
                    <div style={{ display: 'flex', background: 'rgba(0,0,0,0.4)', borderRadius: 8, padding: 3, border: '1px solid rgba(255,255,255,0.05)' }}>
                        {filterTabs.map(t => (
                            <button key={t.key} onClick={() => { setStatusFilter(t.key); setCurrentPage(1) }}
                                style={{
                                    padding: '6px 12px', borderRadius: 6, fontSize: 11, fontWeight: 700,
                                    textTransform: 'uppercase', letterSpacing: 0.5, border: 'none', cursor: 'pointer',
                                    background: statusFilter === t.key ? '#A855F7' : 'transparent',
                                    color: statusFilter === t.key ? '#fff' : '#6B7280',
                                    boxShadow: statusFilter === t.key ? '0 2px 8px rgba(168,85,247,0.3)' : 'none',
                                    transition: 'all 0.15s', fontFamily: 'inherit',
                                }}>{t.label}</button>
                        ))}
                    </div>
                </div>

                {/* Table Header */}
                <div style={{ display: 'grid', gridTemplateColumns: '2.5fr 1fr 1.2fr 1fr 1.2fr 40px', padding: '10px 24px', borderBottom: '1px solid rgba(255,255,255,0.05)', background: 'rgba(255,255,255,0.02)' }}>
                    {['Name', 'Source', 'Status', 'Score', 'Last Contact', ''].map((h, i) => (
                        <span key={i} style={{ fontSize: 10, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: 1 }}>{h}</span>
                    ))}
                </div>

                {/* Table Rows */}
                <div>
                    {paginated.length === 0 ? (
                        <div style={{ padding: '48px 0', textAlign: 'center', color: '#6B7280', fontSize: 14 }}>No leads found.</div>
                    ) : (
                        paginated.map(lead => {
                            const sc = STATUS_COLORS[lead.status] || { bg: 'rgba(107,114,128,0.1)', color: '#9CA3AF', border: 'rgba(107,114,128,0.2)' }
                            return (
                                <div key={lead.id} style={{
                                    display: 'grid', gridTemplateColumns: '2.5fr 1fr 1.2fr 1fr 1.2fr 40px',
                                    padding: '14px 24px', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.03)',
                                    cursor: 'pointer', transition: 'background 0.15s',
                                }}>
                                    {/* Name + Email */}
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                        <div style={{ width: 36, height: 36, borderRadius: '50%', background: 'linear-gradient(135deg, #A855F7, #D946EF)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 13, fontWeight: 700, flexShrink: 0 }}>
                                            {lead.name.charAt(0)}
                                        </div>
                                        <div style={{ minWidth: 0 }}>
                                            <p style={{ fontSize: 13, fontWeight: 600, color: '#E5E7EB', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{lead.name}</p>
                                            <p style={{ fontSize: 11, color: '#6B7280', margin: '2px 0 0 0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{lead.email}</p>
                                        </div>
                                    </div>

                                    {/* Source */}
                                    <span style={{ fontSize: 12, color: '#9CA3AF' }}>{formatSource(lead.source)}</span>

                                    {/* Status */}
                                    <div>
                                        <span style={{
                                            padding: '4px 12px', borderRadius: 12, fontSize: 11, fontWeight: 600,
                                            background: sc.bg, color: sc.color, border: `1px solid ${sc.border}`,
                                            whiteSpace: 'nowrap',
                                        }}>{STATUS_LABELS[lead.status] || lead.status}</span>
                                    </div>

                                    {/* Score */}
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                        <div style={{ width: 48, height: 6, background: '#1F2937', borderRadius: 3, overflow: 'hidden' }}>
                                            <div style={{
                                                height: '100%', borderRadius: 3,
                                                background: lead.score > 60 ? 'linear-gradient(90deg, #10B981, #34D399)' : lead.score > 30 ? 'linear-gradient(90deg, #F59E0B, #FBBF24)' : 'linear-gradient(90deg, #EF4444, #F87171)',
                                                width: `${Math.min(lead.score, 100)}%`,
                                            }} />
                                        </div>
                                        <span style={{ fontSize: 12, fontWeight: 600, color: '#D1D5DB', minWidth: 24 }}>{lead.score}</span>
                                    </div>

                                    {/* Last Contact */}
                                    <span style={{ fontSize: 12, color: '#6B7280' }}>{formatDate(lead.lastContact)}</span>

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
                        <p style={{ fontSize: 12, color: '#6B7280', margin: 0 }}>Page {currentPage} of {totalPages} · {filtered.length} leads</p>
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
