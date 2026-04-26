"use client"

import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/lib/api'
import { Search, Target, Users, TrendingUp, Phone, ChevronLeft, ChevronRight, MoreHorizontal, ArrowUpRight, X, Mail, BookOpen, GraduationCap, Clock, Globe, Flame, Thermometer, User, MapPin, MessageSquare, Tag, Zap, Edit3, Save, Loader2 } from 'lucide-react'

interface ChatbotContext {
    session_id?: string
    source?: string
    exam_target?: string
    preparation_stage?: string
    city?: string
    grade?: string
    board?: string
    subjects?: string | string[]
    goal?: string
    user_type?: string
    preferred_time?: string
    language?: string
    lead_temperature?: string
}

interface Lead {
    id: string
    name: string
    email: string
    phone: string
    source: string
    status: string
    score: number
    lastContact: string
    intent: string
    interested_courses: string[]
    urgency: string
    chatbot_context: ChatbotContext | null
    notes: string
    tags: string[]
    engagement_score: number
    conversion_probability: number
    created_at: string
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

const TEMP_COLORS: Record<string, { bg: string; color: string; icon: string }> = {
    hot: { bg: 'rgba(239,68,68,0.15)', color: '#F87171', icon: '🔥' },
    warm: { bg: 'rgba(245,158,11,0.15)', color: '#FBBF24', icon: '🌤️' },
    cold: { bg: 'rgba(59,130,246,0.15)', color: '#60A5FA', icon: '❄️' },
}

export default function CRMPage() {
    const [searchQuery, setSearchQuery] = useState('')
    const [statusFilter, setStatusFilter] = useState('all')
    const [currentPage, setCurrentPage] = useState(1)
    const [selectedLead, setSelectedLead] = useState<Lead | null>(null)
    const [actionMenuLeadId, setActionMenuLeadId] = useState<string | null>(null)
    const [editLeadData, setEditLeadData] = useState<Lead | null>(null)
    const queryClient = useQueryClient()
    const perPage = 10

    const { data, isLoading } = useQuery({
        queryKey: ['leads', statusFilter],
        queryFn: async () => {
            const res = await apiClient.get(`/api/v1/leads/`, {
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
        score: l.engagement_score ?? l.lead_score ?? l.score ?? (l.chatbot_engagement_score ? Math.round(l.chatbot_engagement_score * 100) : 0),
        lastContact: l.last_contact_at || l.updated_at || l.created_at || '',
        intent: l.intent || '',
        interested_courses: l.interested_courses || [],
        urgency: (l.urgency || 'MEDIUM').toUpperCase(),
        chatbot_context: l.chatbot_context || null,
        notes: l.notes || '',
        tags: l.tags || [],
        engagement_score: l.engagement_score || 0,
        conversion_probability: l.conversion_probability || 0,
        created_at: l.created_at || '',
    }))

    const filtered = leads.filter(l =>
        l.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        l.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
        l.phone.toLowerCase().includes(searchQuery.toLowerCase()) ||
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

    const getLeadTemp = (lead: Lead): string => {
        return (lead.chatbot_context?.lead_temperature || '').toLowerCase()
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
        <div style={{ display: 'flex', gap: 0, position: 'relative' }}>
            {/* Main Content */}
            <div style={{ flex: 1, transition: 'all 0.3s ease', marginRight: selectedLead ? 420 : 0 }}>
                {/* Header */}
                <div style={{ marginBottom: 32 }}>
                    <h2 style={{ fontSize: 28, fontWeight: 700, color: '#fff', marginBottom: 4 }}>CRM Lead Management</h2>
                    <p style={{ fontSize: 13, color: '#6B7280' }}>Track and manage your sales pipeline — all chatbot-captured data at a glance</p>
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
                    <div style={{ display: 'grid', gridTemplateColumns: '2.5fr 1.2fr 1fr 1.2fr 0.8fr 1fr 1fr 40px', padding: '10px 24px', borderBottom: '1px solid rgba(255,255,255,0.05)', background: 'rgba(255,255,255,0.02)' }}>
                        {['Name & Contact', 'Grade / Subject', 'Source', 'Status', 'Temp', 'Score', 'Last Contact', ''].map((h, i) => (
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
                                const temp = getLeadTemp(lead)
                                const tc = TEMP_COLORS[temp]
                                const isSelected = selectedLead?.id === lead.id

                                // Extract grade/subject for quick view
                                const grade = lead.chatbot_context?.grade || ''
                                const subjects = lead.chatbot_context?.subjects
                                const subjectStr = Array.isArray(subjects) ? subjects.join(', ') : (subjects || '')
                                const gradeSubject = [grade, subjectStr].filter(Boolean).join(' · ') || '-'

                                return (
                                    <div key={lead.id}
                                        onClick={() => setSelectedLead(isSelected ? null : lead)}
                                        style={{
                                            display: 'grid', gridTemplateColumns: '2.5fr 1.2fr 1fr 1.2fr 0.8fr 1fr 1fr 40px',
                                            padding: '14px 24px', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.03)',
                                            cursor: 'pointer', transition: 'background 0.15s',
                                            background: isSelected ? 'rgba(168,85,247,0.08)' : 'transparent',
                                            borderLeft: isSelected ? '3px solid #A855F7' : '3px solid transparent',
                                        }}>
                                        {/* Name + Phone + Email */}
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                            <div style={{ width: 36, height: 36, borderRadius: '50%', background: 'linear-gradient(135deg, #A855F7, #D946EF)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 13, fontWeight: 700, flexShrink: 0 }}>
                                                {lead.name.charAt(0)}
                                            </div>
                                            <div style={{ minWidth: 0 }}>
                                                <p style={{ fontSize: 13, fontWeight: 600, color: '#E5E7EB', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{lead.name}</p>
                                                <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginTop: 2 }}>
                                                    {lead.phone && (
                                                        <span style={{ fontSize: 11, color: '#8B5CF6' }}>{lead.phone}</span>
                                                    )}
                                                    {lead.phone && lead.email && (
                                                        <span style={{ fontSize: 11, color: '#374151' }}>·</span>
                                                    )}
                                                    {lead.email && (
                                                        <span style={{ fontSize: 11, color: '#6B7280', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{lead.email}</span>
                                                    )}
                                                </div>
                                            </div>
                                        </div>

                                        {/* Grade / Subject */}
                                        <span style={{ fontSize: 12, color: '#9CA3AF', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{gradeSubject}</span>

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

                                        {/* Temperature */}
                                        <div>
                                            {tc ? (
                                                <span style={{
                                                    padding: '3px 8px', borderRadius: 8, fontSize: 11, fontWeight: 600,
                                                    background: tc.bg, color: tc.color,
                                                }}>{tc.icon} {temp.charAt(0).toUpperCase() + temp.slice(1)}</span>
                                            ) : (
                                                <span style={{ fontSize: 11, color: '#4B5563' }}>—</span>
                                            )}
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
                                        <div style={{ position: 'relative' }}>
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    setSelectedLead(null);
                                                    setActionMenuLeadId(actionMenuLeadId === lead.id ? null : lead.id);
                                                }}
                                                style={{
                                                    padding: 4, background: actionMenuLeadId === lead.id ? 'rgba(168,85,247,0.15)' : 'transparent',
                                                    border: actionMenuLeadId === lead.id ? '1px solid rgba(168,85,247,0.3)' : '1px solid transparent',
                                                    cursor: 'pointer', borderRadius: 8, transition: 'all 0.15s',
                                                }}>
                                                <MoreHorizontal size={16} color={actionMenuLeadId === lead.id ? '#A855F7' : '#6B7280'} />
                                            </button>
                                            {actionMenuLeadId === lead.id && (
                                                <>
                                                    {/* Backdrop to close menu */}
                                                    <div
                                                        onClick={(e) => { e.stopPropagation(); setActionMenuLeadId(null); }}
                                                        style={{ position: 'fixed', inset: 0, zIndex: 40 }}
                                                    />
                                                    {/* Dropdown Menu */}
                                                    <div style={{
                                                        position: 'absolute', right: 0, top: '100%', marginTop: 4,
                                                        width: 200, background: '#1A1930', border: '1px solid rgba(168,85,247,0.2)',
                                                        borderRadius: 12, padding: '6px 0', zIndex: 9999,
                                                        boxShadow: '0 12px 40px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.05)',
                                                        animation: 'fadeIn 0.15s ease-out',
                                                    }}>
                                                        {[
                                                            { icon: '👁️', label: 'View Details', action: () => { setSelectedLead(lead); setActionMenuLeadId(null); } },
                                                            { icon: '📞', label: 'Call', action: () => { if (lead.phone) window.open(`tel:${lead.phone}`); setActionMenuLeadId(null); } },
                                                            { icon: '✉️', label: 'Send Email', action: () => { if (lead.email) window.open(`mailto:${lead.email}`); setActionMenuLeadId(null); } },
                                                            { divider: true } as any,
                                                            { icon: '✏️', label: 'Edit Lead', action: () => { setEditLeadData(lead); setActionMenuLeadId(null); } },
                                                            { icon: '👤', label: 'Assign Lead', action: () => { setSelectedLead(lead); setActionMenuLeadId(null); } },
                                                            { divider: true } as any,
                                                            { icon: '🗑️', label: 'Delete Lead', danger: true, action: async () => {
                                                                setActionMenuLeadId(null);
                                                                if (!confirm(`Are you sure you want to delete "${lead.name}"? This cannot be undone.`)) return;
                                                                try {
                                                                    await apiClient.delete(`/api/v1/leads/${lead.id}`);
                                                                    queryClient.invalidateQueries({ queryKey: ['leads'] });
                                                                    if (selectedLead?.id === lead.id) setSelectedLead(null);
                                                                } catch (err) { alert('Failed to delete lead'); }
                                                            } },
                                                        ].map((item, idx) =>
                                                            item.divider ? (
                                                                <div key={idx} style={{ height: 1, background: 'rgba(255,255,255,0.06)', margin: '4px 0' }} />
                                                            ) : (
                                                                <button
                                                                    key={idx}
                                                                    onClick={(e) => { e.stopPropagation(); item.action?.(); }}
                                                                    style={{
                                                                        width: '100%', padding: '8px 16px', border: 'none', cursor: 'pointer',
                                                                        background: 'transparent', display: 'flex', alignItems: 'center', gap: 10,
                                                                        fontSize: 13, fontWeight: 500, fontFamily: 'inherit', textAlign: 'left',
                                                                        color: item.danger ? '#F87171' : '#D1D5DB',
                                                                        transition: 'background 0.1s',
                                                                    }}
                                                                    onMouseEnter={(e) => { (e.target as HTMLElement).style.background = item.danger ? 'rgba(239,68,68,0.1)' : 'rgba(168,85,247,0.1)'; }}
                                                                    onMouseLeave={(e) => { (e.target as HTMLElement).style.background = 'transparent'; }}
                                                                >
                                                                    <span style={{ fontSize: 15 }}>{item.icon}</span>
                                                                    {item.label}
                                                                </button>
                                                            )
                                                        )}
                                                    </div>
                                                </>
                                            )}
                                        </div>
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

            {/* Lead Detail Drawer */}
            {selectedLead && <LeadDetailDrawer lead={selectedLead} onClose={() => setSelectedLead(null)} formatDate={formatDate} />}

            {/* Edit Lead Modal */}
            {editLeadData && (
                <EditLeadModal
                    lead={editLeadData}
                    onClose={() => setEditLeadData(null)}
                    onSaved={() => {
                        setEditLeadData(null);
                        queryClient.invalidateQueries({ queryKey: ['leads'] });
                    }}
                />
            )}

            <style>{`
                @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
                @keyframes fadeIn { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }
                @keyframes fadeInScale { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }
                @keyframes spin { to { transform: rotate(360deg) } }
            `}</style>
        </div>
    )
}


/* ─────────────────── Lead Detail Drawer ─────────────────── */

function LeadDetailDrawer({ lead, onClose, formatDate }: { lead: Lead; onClose: () => void; formatDate: (d: string) => string }) {
    const ctx = lead.chatbot_context || {}
    const temp = (ctx.lead_temperature || '').toLowerCase()
    const tc = TEMP_COLORS[temp]

    const subjects = ctx.subjects
    const subjectList = Array.isArray(subjects) ? subjects : (subjects ? [subjects] : [])

    type StatItem = { icon: any; label: string; value: string; highlight?: boolean; badgeColor?: string }
    const sections: { title: string; items: StatItem[] }[] = [
        {
            title: '📞 Contact Information',
            items: [
                { icon: User, label: 'Name', value: lead.name },
                { icon: Phone, label: 'Phone', value: lead.phone || '—', highlight: true },
                { icon: Mail, label: 'Email', value: lead.email || '—' },
                { icon: MapPin, label: 'City', value: ctx.city || '—' },
            ]
        },
        {
            title: '🎓 Academic Details',
            items: [
                { icon: GraduationCap, label: 'Grade / Class', value: ctx.grade || '—' },
                { icon: BookOpen, label: 'Board', value: ctx.board || '—' },
                { icon: BookOpen, label: 'Subjects', value: subjectList.length > 0 ? subjectList.join(', ') : '—' },
                { icon: Target, label: 'Goal / Exam', value: ctx.goal || ctx.exam_target || '—' },
                { icon: Tag, label: 'Preparation Stage', value: ctx.preparation_stage || '—' },
            ]
        },
        {
            title: '👤 Student Profile',
            items: [
                { icon: User, label: 'User Type', value: ctx.user_type || '—' },
                { icon: Clock, label: 'Preferred Time', value: ctx.preferred_time || '—' },
                { icon: Globe, label: 'Language', value: ctx.language || '—' },
            ]
        },
        {
            title: '📊 Lead Intelligence',
            items: [
                { icon: Flame, label: 'Temperature', value: ctx.lead_temperature ? `${tc?.icon || ''} ${ctx.lead_temperature}` : '—', badgeColor: tc?.color },
                { icon: Zap, label: 'Engagement Score', value: lead.engagement_score?.toString() || '—' },
                { icon: TrendingUp, label: 'Conversion Prob.', value: lead.conversion_probability ? `${lead.conversion_probability}%` : '—' },
                { icon: Target, label: 'Intent', value: lead.intent || '—' },
                { icon: BookOpen, label: 'Interested Courses', value: lead.interested_courses?.length > 0 ? lead.interested_courses.join(', ') : '—' },
                { icon: Tag, label: 'Urgency', value: lead.urgency || '—' },
            ]
        },
    ]

    return (
        <div style={{
            position: 'fixed', top: 0, right: 0, bottom: 0, width: 420,
            background: '#13121E', borderLeft: '1px solid #2A2840',
            overflowY: 'auto', zIndex: 50,
            animation: 'slideIn 0.25s ease-out',
            boxShadow: '-8px 0 32px rgba(0,0,0,0.4)',
        }}>
            {/* Drawer Header */}
            <div style={{
                padding: '20px 24px', borderBottom: '1px solid rgba(255,255,255,0.06)',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                background: 'linear-gradient(135deg, rgba(168,85,247,0.08), rgba(217,70,239,0.05))',
                position: 'sticky', top: 0, zIndex: 2,
                backdropFilter: 'blur(12px)',
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div style={{
                        width: 44, height: 44, borderRadius: '50%',
                        background: 'linear-gradient(135deg, #A855F7, #D946EF)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        color: '#fff', fontSize: 18, fontWeight: 700,
                        boxShadow: '0 4px 12px rgba(168,85,247,0.3)',
                    }}>
                        {lead.name.charAt(0)}
                    </div>
                    <div>
                        <p style={{ fontSize: 16, fontWeight: 700, color: '#fff', margin: 0 }}>{lead.name}</p>
                        <p style={{ fontSize: 11, color: '#8B5CF6', margin: '2px 0 0 0' }}>
                            {lead.source === 'chatbot' ? '🤖 Chatbot Lead' : `Source: ${lead.source}`}
                            {' · '}{formatDate(lead.created_at)}
                        </p>
                    </div>
                </div>
                <button onClick={onClose} style={{
                    width: 32, height: 32, borderRadius: 8, border: 'none', cursor: 'pointer',
                    background: 'rgba(255,255,255,0.06)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                    transition: 'background 0.15s',
                }}>
                    <X size={16} color="#9CA3AF" />
                </button>
            </div>

            {/* Status + Temperature Badges */}
            <div style={{ padding: '16px 24px', display: 'flex', gap: 8, flexWrap: 'wrap', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                {(() => {
                    const sc = STATUS_COLORS[lead.status] || { bg: 'rgba(107,114,128,0.1)', color: '#9CA3AF', border: 'rgba(107,114,128,0.2)' }
                    return (
                        <span style={{
                            padding: '5px 14px', borderRadius: 20, fontSize: 12, fontWeight: 600,
                            background: sc.bg, color: sc.color, border: `1px solid ${sc.border}`,
                        }}>● {STATUS_LABELS[lead.status] || lead.status}</span>
                    )
                })()}
                {tc && (
                    <span style={{
                        padding: '5px 14px', borderRadius: 20, fontSize: 12, fontWeight: 600,
                        background: tc.bg, color: tc.color,
                    }}>{tc.icon} {temp.charAt(0).toUpperCase() + temp.slice(1)}</span>
                )}
                {lead.urgency && lead.urgency !== 'MEDIUM' && (
                    <span style={{
                        padding: '5px 14px', borderRadius: 20, fontSize: 12, fontWeight: 600,
                        background: lead.urgency === 'HIGH' || lead.urgency === 'CRITICAL' ? 'rgba(239,68,68,0.1)' : 'rgba(59,130,246,0.1)',
                        color: lead.urgency === 'HIGH' || lead.urgency === 'CRITICAL' ? '#F87171' : '#60A5FA',
                    }}>⚡ {lead.urgency}</span>
                )}
            </div>

            {/* Sections */}
            <div style={{ padding: '8px 0' }}>
                {sections.map((section, si) => (
                    <div key={si} style={{ padding: '12px 24px' }}>
                        <p style={{ fontSize: 13, fontWeight: 700, color: '#A78BFA', margin: '0 0 12px 0', letterSpacing: 0.3 }}>
                            {section.title}
                        </p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                            {section.items.map((item, ii) => {
                                const Icon = item.icon
                                const hasValue = item.value !== '—'
                                return (
                                    <div key={ii} style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                                        <div style={{
                                            width: 28, height: 28, borderRadius: 6,
                                            background: hasValue ? 'rgba(168,85,247,0.1)' : 'rgba(255,255,255,0.03)',
                                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                                            flexShrink: 0,
                                        }}>
                                            <Icon size={14} color={hasValue ? '#A78BFA' : '#4B5563'} />
                                        </div>
                                        <div style={{ flex: 1, minWidth: 0 }}>
                                            <p style={{ fontSize: 10, fontWeight: 600, color: '#6B7280', textTransform: 'uppercase', letterSpacing: 0.8, margin: 0 }}>
                                                {item.label}
                                            </p>
                                            <p style={{
                                                fontSize: 13, fontWeight: hasValue ? 500 : 400,
                                                color: hasValue ? (item.highlight ? '#A855F7' : '#E5E7EB') : '#4B5563',
                                                margin: '2px 0 0 0', wordBreak: 'break-word',
                                            }}>
                                                {item.value}
                                            </p>
                                        </div>
                                    </div>
                                )
                            })}
                        </div>
                        {si < sections.length - 1 && (
                            <div style={{ height: 1, background: 'rgba(255,255,255,0.04)', marginTop: 16 }} />
                        )}
                    </div>
                ))}
            </div>

            {/* Notes Section */}
            {lead.notes && (
                <div style={{ padding: '12px 24px' }}>
                    <p style={{ fontSize: 13, fontWeight: 700, color: '#A78BFA', margin: '0 0 8px 0' }}>
                        💬 Notes
                    </p>
                    <div style={{
                        padding: 12, borderRadius: 10, background: 'rgba(255,255,255,0.03)',
                        border: '1px solid rgba(255,255,255,0.05)',
                    }}>
                        <p style={{ fontSize: 13, color: '#D1D5DB', margin: 0, lineHeight: 1.6 }}>{lead.notes}</p>
                    </div>
                </div>
            )}

            {/* Tags */}
            {lead.tags && lead.tags.length > 0 && (
                <div style={{ padding: '12px 24px' }}>
                    <p style={{ fontSize: 13, fontWeight: 700, color: '#A78BFA', margin: '0 0 8px 0' }}>
                        🏷️ Tags
                    </p>
                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                        {lead.tags.map((tag, i) => (
                            <span key={i} style={{
                                padding: '3px 10px', borderRadius: 12, fontSize: 11, fontWeight: 500,
                                background: 'rgba(168,85,247,0.1)', color: '#C4B5FD',
                                border: '1px solid rgba(168,85,247,0.15)',
                            }}>{tag}</span>
                        ))}
                    </div>
                </div>
            )}

            {/* Bottom Spacer */}
            <div style={{ height: 24 }} />
        </div>
    )
}


/* ─────────────────── Edit Lead Modal ─────────────────── */

function EditLeadModal({ lead, onClose, onSaved }: { lead: Lead; onClose: () => void; onSaved: () => void }) {
    const [form, setForm] = useState({
        name: lead.name || '',
        phone: lead.phone || '',
        email: lead.email || '',
        status: lead.status?.toUpperCase() || 'NEW',
        urgency: lead.urgency?.toUpperCase() || 'MEDIUM',
        interested_courses: (lead.interested_courses || []).join(', '),
        notes: lead.notes || '',
    })
    const [saving, setSaving] = useState(false)
    const [error, setError] = useState('')
    const [success, setSuccess] = useState(false)

    const handleChange = (field: string, value: string) => {
        setForm(prev => ({ ...prev, [field]: value }))
        setError('')
    }

    const handleSave = async () => {
        if (!form.name.trim()) { setError('Name is required'); return }
        if (!form.phone.trim()) { setError('Phone is required'); return }

        setSaving(true)
        setError('')
        try {
            const payload: any = {
                name: form.name.trim(),
                phone: form.phone.trim(),
                status: form.status,
                urgency: form.urgency,
                notes: form.notes.trim() || undefined,
            }
            if (form.email.trim()) payload.email = form.email.trim()
            if (form.interested_courses.trim()) {
                payload.interested_courses = form.interested_courses.split(',').map((s: string) => s.trim()).filter(Boolean)
            }

            await apiClient.patch(`/api/v1/leads/${lead.id}`, payload)
            setSuccess(true)
            setTimeout(() => onSaved(), 800)
        } catch (err: any) {
            setError(err?.response?.data?.detail || 'Failed to update lead')
        } finally {
            setSaving(false)
        }
    }

    const inputStyle = (focused?: boolean): React.CSSProperties => ({
        width: '100%', padding: '10px 14px', borderRadius: 10,
        background: '#0B0B12', border: '1px solid rgba(168,85,247,0.2)',
        color: '#E5E7EB', fontSize: 13, fontFamily: 'inherit', outline: 'none',
        transition: 'border-color 0.2s',
    })

    const labelStyle: React.CSSProperties = {
        fontSize: 11, fontWeight: 700, color: '#8B5CF6', textTransform: 'uppercase',
        letterSpacing: 0.8, marginBottom: 6, display: 'block',
    }

    const selectStyle: React.CSSProperties = {
        ...inputStyle(),
        cursor: 'pointer', appearance: 'none' as any,
        backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%236B7280' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E")`,
        backgroundRepeat: 'no-repeat', backgroundPosition: 'right 12px center',
        paddingRight: 32,
    }

    const STATUS_OPTIONS = [
        'NEW', 'CONTACTED', 'QUALIFIED', 'DEMO_SCHEDULED',
        'DEMO_COMPLETED', 'ENROLLED', 'LOST', 'NURTURING',
    ]
    const URGENCY_OPTIONS = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

    return (
        <div style={{
            position: 'fixed', inset: 0, zIndex: 100,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)',
        }} onClick={onClose}>
            <div
                onClick={(e) => e.stopPropagation()}
                style={{
                    width: 520, maxHeight: '85vh', overflowY: 'auto',
                    background: '#13121E', border: '1px solid rgba(168,85,247,0.2)',
                    borderRadius: 20, boxShadow: '0 24px 80px rgba(0,0,0,0.6)',
                    animation: 'fadeInScale 0.2s ease-out',
                }}
            >
                {/* Modal Header */}
                <div style={{
                    padding: '20px 24px', borderBottom: '1px solid rgba(255,255,255,0.06)',
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    background: 'linear-gradient(135deg, rgba(168,85,247,0.08), rgba(217,70,239,0.05))',
                    borderRadius: '20px 20px 0 0',
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <div style={{
                            width: 40, height: 40, borderRadius: 12,
                            background: 'linear-gradient(135deg, #A855F7, #D946EF)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                        }}>
                            <Edit3 size={18} color="#fff" />
                        </div>
                        <div>
                            <p style={{ fontSize: 16, fontWeight: 700, color: '#fff', margin: 0 }}>Edit Lead</p>
                            <p style={{ fontSize: 11, color: '#8B5CF6', margin: '2px 0 0 0' }}>Update lead information</p>
                        </div>
                    </div>
                    <button onClick={onClose} style={{
                        width: 32, height: 32, borderRadius: 8, border: 'none', cursor: 'pointer',
                        background: 'rgba(255,255,255,0.06)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>
                        <X size={16} color="#9CA3AF" />
                    </button>
                </div>

                {/* Form Body */}
                <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 16 }}>
                    {/* Row: Name + Phone */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                        <div>
                            <label style={labelStyle}>Name *</label>
                            <input value={form.name} onChange={e => handleChange('name', e.target.value)}
                                style={inputStyle()} placeholder="Lead name" />
                        </div>
                        <div>
                            <label style={labelStyle}>Phone *</label>
                            <input value={form.phone} onChange={e => handleChange('phone', e.target.value)}
                                style={inputStyle()} placeholder="Phone number" />
                        </div>
                    </div>

                    {/* Email */}
                    <div>
                        <label style={labelStyle}>Email</label>
                        <input value={form.email} onChange={e => handleChange('email', e.target.value)}
                            style={inputStyle()} placeholder="email@example.com" type="email" />
                    </div>

                    {/* Row: Status + Urgency */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                        <div>
                            <label style={labelStyle}>Status</label>
                            <select value={form.status} onChange={e => handleChange('status', e.target.value)}
                                style={selectStyle}>
                                {STATUS_OPTIONS.map(s => (
                                    <option key={s} value={s} style={{ background: '#13121E', color: '#E5E7EB' }}>
                                        {s.replace(/_/g, ' ')}
                                    </option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label style={labelStyle}>Urgency</label>
                            <select value={form.urgency} onChange={e => handleChange('urgency', e.target.value)}
                                style={selectStyle}>
                                {URGENCY_OPTIONS.map(u => (
                                    <option key={u} value={u} style={{ background: '#13121E', color: '#E5E7EB' }}>
                                        {u}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>

                    {/* Interested Courses */}
                    <div>
                        <label style={labelStyle}>Interested Courses <span style={{ fontWeight: 400, color: '#6B7280', textTransform: 'none' }}>(comma-separated)</span></label>
                        <input value={form.interested_courses} onChange={e => handleChange('interested_courses', e.target.value)}
                            style={inputStyle()} placeholder="English, Maths, Physics" />
                    </div>

                    {/* Notes */}
                    <div>
                        <label style={labelStyle}>Notes</label>
                        <textarea value={form.notes} onChange={e => handleChange('notes', e.target.value)}
                            rows={3}
                            style={{ ...inputStyle(), resize: 'vertical' as any, minHeight: 70 }}
                            placeholder="Additional notes about this lead..." />
                    </div>

                    {/* Error / Success Messages */}
                    {error && (
                        <div style={{
                            padding: '10px 14px', borderRadius: 10,
                            background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)',
                            color: '#F87171', fontSize: 13,
                        }}>{error}</div>
                    )}
                    {success && (
                        <div style={{
                            padding: '10px 14px', borderRadius: 10,
                            background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.2)',
                            color: '#34D399', fontSize: 13,
                        }}>✓ Lead updated successfully!</div>
                    )}
                </div>

                {/* Modal Footer */}
                <div style={{
                    padding: '16px 24px', borderTop: '1px solid rgba(255,255,255,0.06)',
                    display: 'flex', justifyContent: 'flex-end', gap: 10,
                    borderRadius: '0 0 20px 20px',
                }}>
                    <button onClick={onClose} style={{
                        padding: '10px 20px', borderRadius: 10, fontSize: 13, fontWeight: 600,
                        background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)',
                        color: '#9CA3AF', cursor: 'pointer', fontFamily: 'inherit',
                        transition: 'all 0.15s',
                    }}>Cancel</button>
                    <button onClick={handleSave} disabled={saving} style={{
                        padding: '10px 24px', borderRadius: 10, fontSize: 13, fontWeight: 700,
                        background: saving ? 'rgba(168,85,247,0.4)' : 'linear-gradient(135deg, #A855F7, #D946EF)',
                        border: 'none', color: '#fff', cursor: saving ? 'not-allowed' : 'pointer',
                        fontFamily: 'inherit', display: 'flex', alignItems: 'center', gap: 8,
                        boxShadow: saving ? 'none' : '0 4px 16px rgba(168,85,247,0.3)',
                        transition: 'all 0.15s',
                    }}>
                        {saving ? <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> : <Save size={14} />}
                        {saving ? 'Saving...' : 'Save Changes'}
                    </button>
                </div>
            </div>
        </div>
    )
}
