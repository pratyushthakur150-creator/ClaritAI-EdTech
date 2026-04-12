"use client"

import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import apiClient from '@/lib/api'
import { Mic, MicOff, PhoneCall, PhoneOff, Volume2, Clock, Users, TrendingUp, BarChart3 } from 'lucide-react'

interface CallRecord {
  id: string; leadName: string; phone: string; duration: number
  status: string; date: string; summary: string; sentiment: string; direction: string
}

const STATUS_LABELS: Record<string, string> = {
  completed: 'Completed', 'in-progress': 'In Progress', in_progress: 'In Progress',
  scheduled: 'Scheduled', missed: 'Missed', queued: 'Queued', failed: 'Failed',
}
const STATUS_COLORS: Record<string, { bg: string; color: string; border: string }> = {
  completed: { bg: 'rgba(16,185,129,0.1)', color: '#34D399', border: 'rgba(16,185,129,0.2)' },
  'in-progress': { bg: 'rgba(59,130,246,0.1)', color: '#60A5FA', border: 'rgba(59,130,246,0.2)' },
  in_progress: { bg: 'rgba(59,130,246,0.1)', color: '#60A5FA', border: 'rgba(59,130,246,0.2)' },
  scheduled: { bg: 'rgba(245,158,11,0.1)', color: '#FBBF24', border: 'rgba(245,158,11,0.2)' },
  missed: { bg: 'rgba(239,68,68,0.1)', color: '#F87171', border: 'rgba(239,68,68,0.2)' },
  queued: { bg: 'rgba(168,85,247,0.1)', color: '#A855F7', border: 'rgba(168,85,247,0.2)' },
  failed: { bg: 'rgba(239,68,68,0.1)', color: '#F87171', border: 'rgba(239,68,68,0.2)' },
}

export default function VoiceAgentPage() {
  const [isCallActive, setIsCallActive] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [callTimer, setCallTimer] = useState(0)

  const { data, isLoading } = useQuery({
    queryKey: ['voice-calls'],
    queryFn: async () => {
      try {
        const res = await apiClient.get(`/api/v1/calls`)
        return res.data
      } catch { return null }
    },
  })

  const rawCalls = data?.calls || data?.data || []
  const calls: CallRecord[] = rawCalls.map((c: any) => ({
    id: c.id?.toString() || '',
    leadName: c.lead_name || c.lead?.name || 'Unknown',
    phone: c.phone_number || c.lead?.phone || '',
    duration: c.duration_seconds || c.duration || 0,
    status: (c.status || c.outcome || 'completed').toLowerCase(),
    date: c.created_at || c.started_at || '',
    summary: c.summary || c.notes || c.transcript?.slice(0, 80) || '',
    sentiment: c.sentiment || 'neutral',
    direction: c.direction || 'outbound',
  }))

  // Timer for active call
  useEffect(() => {
    let t: NodeJS.Timeout
    if (isCallActive) { t = setInterval(() => setCallTimer(v => v + 1), 1000) }
    return () => clearInterval(t)
  }, [isCallActive])

  const fmt = (s: number) => `${Math.floor(s / 60).toString().padStart(2, '0')}:${(s % 60).toString().padStart(2, '0')}`

  const fmtDuration = (secs: number) => {
    if (!secs || secs === 0) return '-'
    return `${Math.floor(secs / 60)}m ${secs % 60}s`
  }

  const fmtDate = (d: string) => {
    if (!d) return '-'
    try {
      const dt = new Date(d)
      const now = new Date()
      const diffH = Math.round((now.getTime() - dt.getTime()) / 3600000)
      if (diffH < 1) return 'Just now'
      if (diffH < 24) return `${diffH}h ago`
      if (diffH < 48) return 'Yesterday'
      return dt.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
    } catch { return '-' }
  }

  const completedCalls = calls.filter(c => c.status === 'completed')
  const avgDuration = completedCalls.length > 0
    ? Math.round(completedCalls.reduce((s, c) => s + c.duration, 0) / completedCalls.length)
    : 0
  const successRate = calls.length > 0
    ? Math.round((completedCalls.length / calls.length) * 100)
    : 0
  const scheduledCount = calls.filter(c => c.status === 'scheduled' || c.status === 'queued').length

  const metrics = [
    { label: 'Total Calls', value: calls.length, icon: PhoneCall, color: '#A855F7' },
    { label: 'Avg Duration', value: fmtDuration(avgDuration), icon: Clock, color: '#3B82F6' },
    { label: 'Success Rate', value: `${successRate}%`, icon: TrendingUp, color: '#10B981' },
    { label: 'Scheduled', value: scheduledCount, icon: Users, color: '#F59E0B' },
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
        <h2 style={{ fontSize: 28, fontWeight: 700, color: '#fff', marginBottom: 4 }}>CRM Voice Agent</h2>
        <p style={{ fontSize: 13, color: '#6B7280' }}>AI-powered voice calls for lead engagement</p>
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

      {/* Main Content: Call Controls + Recent Calls */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 24 }}>
        {/* Call Controls */}
        <div style={{ background: '#13121E', border: '1px solid #2A2840', borderRadius: 16, padding: 32, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 20 }}>
          <div style={{
            width: 80, height: 80, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: isCallActive ? 'linear-gradient(135deg, #10B981, #059669)' : 'linear-gradient(135deg, #A855F7, #D946EF)',
            boxShadow: isCallActive ? '0 0 30px rgba(16,185,129,0.3)' : '0 0 30px rgba(168,85,247,0.2)',
            animation: isCallActive ? 'pulse 2s ease-in-out infinite' : 'none',
          }}>
            {isCallActive ? <Volume2 size={32} color="#fff" /> : <PhoneCall size={32} color="#fff" />}
          </div>

          {isCallActive && (
            <p style={{ fontSize: 28, fontWeight: 700, color: '#fff', fontFamily: 'monospace', margin: 0 }}>{fmt(callTimer)}</p>
          )}

          <p style={{ fontSize: 13, color: '#6B7280', margin: 0 }}>
            {isCallActive ? 'Call in progress...' : 'Ready to make a call'}
          </p>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {isCallActive && (
              <button onClick={() => setIsMuted(!isMuted)} style={{
                padding: 12, borderRadius: '50%', border: 'none', cursor: 'pointer',
                background: isMuted ? 'rgba(239,68,68,0.1)' : 'rgba(255,255,255,0.05)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                {isMuted ? <MicOff size={20} color="#F87171" /> : <Mic size={20} color="#9CA3AF" />}
              </button>
            )}
            <button
              onClick={() => { setIsCallActive(!isCallActive); if (isCallActive) setCallTimer(0) }}
              style={{
                padding: '12px 24px', borderRadius: 12, border: 'none', cursor: 'pointer',
                fontWeight: 600, fontSize: 14, color: '#fff', fontFamily: 'inherit',
                display: 'flex', alignItems: 'center', gap: 8,
                background: isCallActive ? '#EF4444' : 'linear-gradient(135deg, #A855F7, #D946EF)',
                boxShadow: isCallActive ? '0 4px 12px rgba(239,68,68,0.3)' : '0 4px 12px rgba(168,85,247,0.3)',
              }}>
              {isCallActive ? <><PhoneOff size={16} /> End Call</> : <><PhoneCall size={16} /> Start Call</>}
            </button>
          </div>

          {/* Quick Stats */}
          <div style={{ width: '100%', marginTop: 16, borderTop: '1px solid #2A2840', paddingTop: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
              <span style={{ fontSize: 11, color: '#6B7280', textTransform: 'uppercase', fontWeight: 600 }}>Completed</span>
              <span style={{ fontSize: 13, fontWeight: 600, color: '#34D399' }}>{completedCalls.length}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
              <span style={{ fontSize: 11, color: '#6B7280', textTransform: 'uppercase', fontWeight: 600 }}>Missed</span>
              <span style={{ fontSize: 13, fontWeight: 600, color: '#F87171' }}>{calls.filter(c => c.status === 'missed').length}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: 11, color: '#6B7280', textTransform: 'uppercase', fontWeight: 600 }}>Outbound</span>
              <span style={{ fontSize: 13, fontWeight: 600, color: '#60A5FA' }}>{calls.filter(c => c.direction === 'outbound').length}</span>
            </div>
          </div>
        </div>

        {/* Recent Calls */}
        <div style={{ background: '#13121E', border: '1px solid #2A2840', borderRadius: 16, overflow: 'hidden' }}>
          <div style={{ padding: '16px 24px', borderBottom: '1px solid rgba(255,255,255,0.05)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontWeight: 600, color: '#fff', fontSize: 15, margin: 0 }}>Recent Call Activity</h3>
            <span style={{ fontSize: 12, color: '#6B7280' }}>{calls.length} calls</span>
          </div>

          {/* Table Header */}
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr', padding: '10px 24px', borderBottom: '1px solid rgba(255,255,255,0.05)', background: 'rgba(255,255,255,0.02)' }}>
            {['Lead', 'Duration', 'Status', 'Sentiment', 'When'].map((h, i) => (
              <span key={i} style={{ fontSize: 10, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: 1 }}>{h}</span>
            ))}
          </div>

          <div style={{ maxHeight: 400, overflowY: 'auto' }}>
            {calls.length === 0 ? (
              <div style={{ padding: '48px 0', textAlign: 'center', color: '#6B7280', fontSize: 14 }}>No calls recorded yet.</div>
            ) : (
              calls.slice(0, 20).map(call => {
                const sc = STATUS_COLORS[call.status] || STATUS_COLORS.completed
                const sentimentColor = call.sentiment === 'positive' ? '#34D399' : call.sentiment === 'negative' ? '#F87171' : '#9CA3AF'
                return (
                  <div key={call.id} style={{
                    display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr',
                    padding: '14px 24px', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.03)',
                    cursor: 'pointer', transition: 'background 0.15s',
                  }}>
                    {/* Lead */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'linear-gradient(135deg, #A855F7, #D946EF)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 12, fontWeight: 700, flexShrink: 0 }}>
                        {call.leadName.charAt(0)}
                      </div>
                      <div style={{ minWidth: 0 }}>
                        <p style={{ fontSize: 13, fontWeight: 600, color: '#E5E7EB', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{call.leadName}</p>
                        <p style={{ fontSize: 10, color: '#6B7280', margin: '2px 0 0 0' }}>{call.phone || call.direction}</p>
                      </div>
                    </div>

                    {/* Duration */}
                    <span style={{ fontSize: 12, color: '#9CA3AF', fontFamily: 'monospace' }}>{fmtDuration(call.duration)}</span>

                    {/* Status */}
                    <div>
                      <span style={{
                        padding: '3px 10px', borderRadius: 12, fontSize: 10, fontWeight: 600,
                        background: sc.bg, color: sc.color, border: `1px solid ${sc.border}`,
                      }}>{STATUS_LABELS[call.status] || call.status}</span>
                    </div>

                    {/* Sentiment */}
                    <span style={{ fontSize: 12, color: sentimentColor, fontWeight: 500, textTransform: 'capitalize' }}>{call.sentiment}</span>

                    {/* When */}
                    <span style={{ fontSize: 12, color: '#6B7280' }}>{fmtDate(call.date)}</span>
                  </div>
                )
              })
            )}
          </div>
        </div>
      </div>

      <style>{`@keyframes pulse { 0%, 100% { box-shadow: 0 0 20px rgba(16,185,129,0.2) } 50% { box-shadow: 0 0 40px rgba(16,185,129,0.4) } }`}</style>
    </div>
  )
}
