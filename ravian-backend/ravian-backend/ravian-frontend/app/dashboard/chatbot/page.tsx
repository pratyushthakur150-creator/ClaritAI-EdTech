"use client"

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import apiClient from '@/lib/api'
import { Search, MessageSquare, Clock, Users, Send, ChevronRight, ArrowUpRight, Zap } from 'lucide-react'

interface ChatSession {
  id: string
  visitorId: string
  startTime: string
  duration: number
  messages: number
  leadCaptured: boolean
  status: string
  engagementScore: number
}

export default function ChatbotPage() {
  const [searchQuery, setSearchQuery] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['chatbot-sessions'],
    queryFn: async () => {
      const res = await apiClient.get(`/api/v1/chatbot/sessions`)
      return res.data
    },
  })

  // Backend returns { data: [...], total: N }
  const rawSessions = data?.data || data?.sessions || []
  const sessions: ChatSession[] = rawSessions.map((s: any) => ({
    id: s.id || '',
    visitorId: s.visitor_id || s.session_id || 'Unknown',
    startTime: s.start_time || s.created_at || '',
    duration: s.duration || s.duration_seconds || 0,
    messages: s.messages || s.message_count || 0,
    leadCaptured: s.lead_captured || false,
    status: s.status || 'active',
    engagementScore: s.engagement_score || 0,
  }))

  const filtered = sessions.filter(s =>
    s.visitorId.toLowerCase().includes(searchQuery.toLowerCase()) ||
    s.status.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const totalMessages = sessions.reduce((sum, s) => sum + s.messages, 0)
  const leadsFromChat = sessions.filter(s => s.leadCaptured).length
  const activeSessions = sessions.filter(s => s.status === 'active').length
  const avgDuration = sessions.length > 0
    ? Math.round(sessions.reduce((sum, s) => sum + s.duration, 0) / sessions.length)
    : 0
  const avgDurStr = avgDuration > 0 ? `${Math.floor(avgDuration / 60)}m ${avgDuration % 60}s` : '0m'

  const formatTime = (iso: string) => {
    if (!iso) return '-'
    try {
      const d = new Date(iso)
      const now = new Date()
      const diffH = Math.round((now.getTime() - d.getTime()) / 3600000)
      if (diffH < 1) return 'Just now'
      if (diffH < 24) return `${diffH}h ago`
      if (diffH < 48) return 'Yesterday'
      return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
    } catch { return '-' }
  }

  const statusStyle = (status: string) => {
    switch (status) {
      case 'active': return { bg: 'rgba(16,185,129,0.1)', color: '#34D399', border: 'rgba(16,185,129,0.2)' }
      case 'completed': return { bg: 'rgba(168,85,247,0.1)', color: '#A855F7', border: 'rgba(168,85,247,0.2)' }
      default: return { bg: 'rgba(107,114,128,0.1)', color: '#9CA3AF', border: 'rgba(107,114,128,0.2)' }
    }
  }

  const metrics = [
    { label: 'Total Sessions', value: sessions.length, icon: MessageSquare, color: '#A855F7' },
    { label: 'Active Now', value: activeSessions, icon: Users, color: '#10B981' },
    { label: 'Leads Captured', value: leadsFromChat, icon: Zap, color: '#F59E0B' },
    { label: 'Avg Duration', value: avgDurStr, icon: Clock, color: '#3B82F6' },
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
        <h2 style={{ fontSize: 28, fontWeight: 700, color: '#fff', marginBottom: 4 }}>Chatbot Sessions</h2>
        <p style={{ fontSize: 13, color: '#6B7280' }}>Monitor and manage chatbot conversations</p>
      </div>

      {/* Metric Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
        {metrics.map((m, i) => {
          const Icon = m.icon
          return (
            <div key={i} style={{
              background: '#13121E', border: '1px solid #2A2840', borderRadius: 16, padding: 20,
              position: 'relative', overflow: 'hidden',
            }}>
              <div style={{ position: 'absolute', top: -16, right: -16, width: 60, height: 60, background: m.color, borderRadius: '50%', filter: 'blur(30px)', opacity: 0.12 }} />
              <div style={{ position: 'relative', zIndex: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <p style={{ fontSize: 11, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: 1 }}>{m.label}</p>
                  <p style={{ fontSize: 24, fontWeight: 700, color: '#fff', marginTop: 4 }}>{typeof m.value === 'number' ? m.value.toLocaleString() : m.value}</p>
                </div>
                <div style={{ width: 40, height: 40, borderRadius: 12, background: m.color, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Icon size={20} color="#fff" />
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginTop: 12 }}>
                <ArrowUpRight size={14} color="#4ADE80" />
                <span style={{ fontSize: 12, fontWeight: 500, color: '#4ADE80' }}>+15%</span>
                <span style={{ fontSize: 12, color: '#4B5563', marginLeft: 4 }}>vs last week</span>
              </div>
            </div>
          )
        })}
      </div>

      {/* Sessions Table */}
      <div style={{ background: '#13121E', border: '1px solid #2A2840', borderRadius: 16, overflow: 'hidden' }}>
        <div style={{ padding: '16px 24px', borderBottom: '1px solid rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
          <div style={{ position: 'relative', flex: 1, maxWidth: 320 }}>
            <Search size={16} color="#6B7280" style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)' }} />
            <input
              type="text"
              placeholder="Search sessions..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              style={{
                width: '100%', background: '#0B0B12', border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: 8, padding: '8px 16px 8px 36px', fontSize: 13, color: '#D1D5DB',
                outline: 'none', fontFamily: 'inherit',
              }}
            />
          </div>
          <p style={{ fontSize: 12, color: '#6B7280' }}>{filtered.length} sessions</p>
        </div>

        {/* Header */}
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr 40px', padding: '10px 24px', borderBottom: '1px solid rgba(255,255,255,0.05)', background: 'rgba(255,255,255,0.02)' }}>
          {['Session', 'Status', 'Messages', 'Duration', 'Lead', ''].map((h, i) => (
            <span key={i} style={{ fontSize: 10, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: 1 }}>{h}</span>
          ))}
        </div>

        {/* Rows */}
        <div>
          {filtered.length === 0 ? (
            <div style={{ padding: '48px 0', textAlign: 'center', color: '#6B7280', fontSize: 14 }}>
              {sessions.length === 0 ? 'No chatbot sessions found. Run the seed script to populate data.' : 'No matching sessions.'}
            </div>
          ) : (
            filtered.map(session => {
              const st = statusStyle(session.status)
              return (
                <div key={session.id} style={{
                  display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr 40px',
                  padding: '14px 24px', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.03)',
                  cursor: 'pointer', transition: 'background 0.15s',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div style={{
                      width: 36, height: 36, borderRadius: '50%',
                      background: 'linear-gradient(135deg, #A855F7, #D946EF)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      color: '#fff', fontSize: 13, fontWeight: 700, flexShrink: 0,
                    }}>
                      {session.visitorId.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <p style={{ fontSize: 13, fontWeight: 600, color: '#E5E7EB', margin: 0 }}>
                        {session.visitorId.length > 20 ? session.visitorId.slice(0, 8) + '...' : session.visitorId}
                      </p>
                      <p style={{ fontSize: 11, color: '#6B7280', margin: '2px 0 0 0' }}>{formatTime(session.startTime)}</p>
                    </div>
                  </div>

                  <div>
                    <span style={{
                      padding: '3px 10px', borderRadius: 12, fontSize: 11, fontWeight: 600,
                      background: st.bg, color: st.color, border: `1px solid ${st.border}`,
                    }}>{session.status}</span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    <MessageSquare size={14} color="#6B7280" />
                    <span style={{ fontSize: 13, color: '#D1D5DB', fontWeight: 500 }}>{session.messages}</span>
                  </div>

                  <div style={{ fontSize: 13, color: '#9CA3AF' }}>
                    {session.duration > 0 ? `${Math.floor(session.duration / 60)}m ${session.duration % 60}s` : '-'}
                  </div>

                  <div>
                    {session.leadCaptured ? (
                      <span style={{ padding: '3px 10px', borderRadius: 12, fontSize: 11, fontWeight: 600, background: 'rgba(16,185,129,0.1)', color: '#34D399', border: '1px solid rgba(16,185,129,0.2)' }}>✓ Captured</span>
                    ) : (
                      <span style={{ fontSize: 12, color: '#6B7280' }}>—</span>
                    )}
                  </div>

                  <ChevronRight size={16} color="#4B5563" />
                </div>
              )
            })
          )}
        </div>
      </div>
    </div>
  )
}
