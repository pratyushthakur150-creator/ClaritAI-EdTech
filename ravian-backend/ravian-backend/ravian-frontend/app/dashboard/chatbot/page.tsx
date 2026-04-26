"use client"

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import apiClient from '@/lib/api'
import { Search, MessageSquare, Clock, Users, Send, ChevronRight, ArrowUpRight, Zap, X, User, Phone, Mail, Bot, Loader2 } from 'lucide-react'

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
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null)

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
                <div
                  key={session.id}
                  onClick={() => setSelectedSessionId(session.id)}
                  style={{
                    display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr 40px',
                    padding: '14px 24px', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.03)',
                    cursor: 'pointer', transition: 'background 0.15s',
                  }}
                  onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = 'rgba(168,85,247,0.04)' }}
                  onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = 'transparent' }}
                >
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

      {/* Session Detail Drawer */}
      {selectedSessionId && (
        <SessionDetailDrawer
          sessionId={selectedSessionId}
          onClose={() => setSelectedSessionId(null)}
        />
      )}

      <style>{`
        @keyframes spin { to { transform: rotate(360deg) } }
        @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
      `}</style>
    </div>
  )
}


/* ─────────────────── Session Detail Drawer ─────────────────── */

function SessionDetailDrawer({ sessionId, onClose }: { sessionId: string; onClose: () => void }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['chatbot-session', sessionId],
    queryFn: async () => {
      const res = await apiClient.get(`/api/v1/chatbot/sessions/${sessionId}`)
      return res.data
    },
    enabled: !!sessionId,
  })

  const formatTime = (iso: string) => {
    if (!iso) return '-'
    try {
      const d = new Date(iso)
      return d.toLocaleString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
    } catch { return '-' }
  }

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 90 }}
      />

      {/* Drawer */}
      <div style={{
        position: 'fixed', top: 0, right: 0, bottom: 0, width: 520,
        background: '#13121E', borderLeft: '1px solid rgba(168,85,247,0.15)',
        zIndex: 100, display: 'flex', flexDirection: 'column',
        animation: 'slideIn 0.25s ease-out',
        boxShadow: '-8px 0 40px rgba(0,0,0,0.4)',
      }}>
        {/* Header */}
        <div style={{
          padding: '20px 24px', borderBottom: '1px solid rgba(255,255,255,0.06)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          background: 'linear-gradient(135deg, rgba(168,85,247,0.08), rgba(217,70,239,0.05))',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{
              width: 40, height: 40, borderRadius: 12,
              background: 'linear-gradient(135deg, #A855F7, #D946EF)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <MessageSquare size={18} color="#fff" />
            </div>
            <div>
              <p style={{ fontSize: 15, fontWeight: 700, color: '#fff', margin: 0 }}>Session Details</p>
              <p style={{ fontSize: 11, color: '#8B5CF6', margin: '2px 0 0 0' }}>
                {data?.session_id ? (data.session_id.length > 25 ? data.session_id.slice(0, 25) + '...' : data.session_id) : 'Loading...'}
              </p>
            </div>
          </div>
          <button onClick={onClose} style={{
            width: 32, height: 32, borderRadius: 8, border: 'none', cursor: 'pointer',
            background: 'rgba(255,255,255,0.06)', display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <X size={16} color="#9CA3AF" />
          </button>
        </div>

        {/* Content */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '16px 0' }}>
          {isLoading ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 60 }}>
              <Loader2 size={28} color="#A855F7" style={{ animation: 'spin 1s linear infinite' }} />
            </div>
          ) : error ? (
            <div style={{ padding: '40px 24px', textAlign: 'center', color: '#F87171', fontSize: 13 }}>
              Failed to load session details
            </div>
          ) : data ? (
            <>
              {/* Session Metadata */}
              <div style={{ padding: '0 24px 16px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                {[
                  { label: 'Started', value: formatTime(data.start_time) },
                  { label: 'Messages', value: data.message_count || 0 },
                  { label: 'Duration', value: data.duration > 0 ? `${Math.floor(data.duration / 60)}m ${data.duration % 60}s` : '—' },
                  { label: 'Engagement', value: `${data.engagement_score || 0}%` },
                ].map((m, i) => (
                  <div key={i} style={{
                    padding: '10px 14px', borderRadius: 10,
                    background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)',
                  }}>
                    <p style={{ fontSize: 10, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: 0.8, margin: 0 }}>{m.label}</p>
                    <p style={{ fontSize: 14, fontWeight: 600, color: '#E5E7EB', margin: '4px 0 0 0' }}>{m.value}</p>
                  </div>
                ))}
              </div>

              {/* Lead Info Card */}
              {data.lead && (
                <div style={{ margin: '0 24px 16px', padding: 16, borderRadius: 12, background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.15)' }}>
                  <p style={{ fontSize: 10, fontWeight: 700, color: '#34D399', textTransform: 'uppercase', letterSpacing: 1, margin: '0 0 10px 0' }}>✓ Lead Captured</p>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {data.lead.name && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <User size={13} color="#6B7280" />
                        <span style={{ fontSize: 13, color: '#E5E7EB', fontWeight: 500 }}>{data.lead.name}</span>
                      </div>
                    )}
                    {data.lead.phone && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Phone size={13} color="#6B7280" />
                        <span style={{ fontSize: 13, color: '#D1D5DB' }}>{data.lead.phone}</span>
                      </div>
                    )}
                    {data.lead.email && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Mail size={13} color="#6B7280" />
                        <span style={{ fontSize: 13, color: '#D1D5DB' }}>{data.lead.email}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Intent */}
              {data.intent_detected && (
                <div style={{ margin: '0 24px 16px', padding: '10px 14px', borderRadius: 10, background: 'rgba(168,85,247,0.06)', border: '1px solid rgba(168,85,247,0.12)' }}>
                  <p style={{ fontSize: 10, fontWeight: 700, color: '#A855F7', textTransform: 'uppercase', letterSpacing: 0.8, margin: 0 }}>Intent Detected</p>
                  <p style={{ fontSize: 13, color: '#D1D5DB', margin: '4px 0 0 0' }}>{data.intent_detected}</p>
                </div>
              )}

              {/* Conversation Header */}
              <div style={{ padding: '0 24px', marginBottom: 12 }}>
                <p style={{ fontSize: 11, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: 1, margin: 0 }}>
                  Conversation ({data.messages?.length || 0} messages)
                </p>
              </div>

              {/* Chat Messages */}
              <div style={{ padding: '0 24px', display: 'flex', flexDirection: 'column', gap: 10 }}>
                {(!data.messages || data.messages.length === 0) ? (
                  <p style={{ color: '#6B7280', fontSize: 13, textAlign: 'center', padding: 24 }}>No messages in this session</p>
                ) : (
                  data.messages.map((msg: any, i: number) => {
                    const isBot = (msg.sender || msg.role) === 'bot' || (msg.sender || msg.role) === 'assistant'
                    const text = msg.message || msg.content || ''
                    return (
                      <div key={i} style={{
                        display: 'flex', flexDirection: 'column',
                        alignItems: isBot ? 'flex-start' : 'flex-end',
                      }}>
                        <div style={{
                          display: 'flex', alignItems: 'flex-end', gap: 8,
                          flexDirection: isBot ? 'row' : 'row-reverse',
                        }}>
                          <div style={{
                            width: 26, height: 26, borderRadius: '50%', flexShrink: 0,
                            background: isBot
                              ? 'linear-gradient(135deg, #A855F7, #D946EF)'
                              : 'rgba(59,130,246,0.2)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                          }}>
                            {isBot
                              ? <Bot size={13} color="#fff" />
                              : <User size={13} color="#60A5FA" />}
                          </div>
                          <div style={{
                            maxWidth: '80%', padding: '10px 14px', borderRadius: 14,
                            background: isBot
                              ? 'rgba(168,85,247,0.08)'
                              : 'rgba(59,130,246,0.1)',
                            border: `1px solid ${isBot ? 'rgba(168,85,247,0.12)' : 'rgba(59,130,246,0.15)'}`,
                          }}>
                            <p style={{
                              fontSize: 13, color: '#E5E7EB', margin: 0,
                              lineHeight: 1.5, whiteSpace: 'pre-wrap', wordBreak: 'break-word',
                            }}>
                              {text}
                            </p>
                          </div>
                        </div>
                        <p style={{
                          fontSize: 10, color: '#4B5563', margin: '3px 36px 0',
                        }}>
                          {isBot ? 'Sia' : 'Visitor'}
                          {msg.timestamp ? ` · ${new Date(msg.timestamp).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}` : ''}
                        </p>
                      </div>
                    )
                  })
                )}
              </div>

              {/* Bottom padding */}
              <div style={{ height: 24 }} />
            </>
          ) : null}
        </div>
      </div>
    </>
  )
}
