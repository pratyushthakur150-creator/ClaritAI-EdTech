"use client"

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import apiClient from '@/lib/api'
import { Phone, PhoneIncoming, PhoneOutgoing, PhoneMissed, Clock, Search, MoreHorizontal, TrendingUp, ChevronLeft, ChevronRight } from 'lucide-react'

interface Call {
  id: string; leadName: string; phone: string; type: string
  duration: string; durationSec: number; date: string; outcome: string; sentiment: string
}

const OUTCOME_COLORS: Record<string, { bg: string; color: string; border: string }> = {
  connected: { bg: 'rgba(16,185,129,0.1)', color: '#34D399', border: 'rgba(16,185,129,0.2)' },
  completed: { bg: 'rgba(16,185,129,0.1)', color: '#34D399', border: 'rgba(16,185,129,0.2)' },
  interested: { bg: 'rgba(59,130,246,0.1)', color: '#60A5FA', border: 'rgba(59,130,246,0.2)' },
  'no answer': { bg: 'rgba(239,68,68,0.1)', color: '#F87171', border: 'rgba(239,68,68,0.2)' },
  no_answer: { bg: 'rgba(239,68,68,0.1)', color: '#F87171', border: 'rgba(239,68,68,0.2)' },
  callback: { bg: 'rgba(245,158,11,0.1)', color: '#FBBF24', border: 'rgba(245,158,11,0.2)' },
  voicemail: { bg: 'rgba(107,114,128,0.1)', color: '#9CA3AF', border: 'rgba(107,114,128,0.2)' },
}

export default function CallsPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const perPage = 10

  const { data, isLoading } = useQuery({
    queryKey: ['calls'],
    queryFn: async () => { try { const res = await apiClient.get(`/api/v1/calls`); return res.data } catch { return null } },
  })

  const rawCalls = data?.calls || data?.data || []
  const calls: Call[] = rawCalls.map((c: any) => {
    const durSec = typeof c.duration === 'number' ? c.duration : (c.duration_seconds || 0)
    const durStr = durSec > 0 ? `${Math.floor(durSec / 60)}:${String(durSec % 60).padStart(2, '0')}` : '-'
    return {
      id: c.id?.toString() || '',
      leadName: c.lead_name || c.lead?.name || 'Unknown',
      phone: c.phone_number || c.phone || c.lead?.phone || '',
      type: (c.call_direction || c.direction || 'outbound').toLowerCase(),
      duration: durStr,
      durationSec: durSec,
      date: c.created_at || '',
      outcome: (c.outcome || c.status || '-').toLowerCase(),
      sentiment: (c.sentiment || 'neutral').toLowerCase(),
    }
  })

  const filtered = calls.filter(c => c.leadName.toLowerCase().includes(searchQuery.toLowerCase()))
  const totalPages = Math.ceil(filtered.length / perPage)
  const paginated = filtered.slice((currentPage - 1) * perPage, currentPage * perPage)

  const validDurations = rawCalls.filter((c: any) => (typeof c.duration === 'number' ? c.duration : c.duration_seconds || 0) > 0)
  const avgDur = validDurations.length > 0
    ? Math.round(validDurations.reduce((s: number, c: any) => s + (typeof c.duration === 'number' ? c.duration : c.duration_seconds || 0), 0) / validDurations.length)
    : 0
  const successCount = calls.filter(c => c.outcome === 'connected' || c.outcome === 'completed' || c.outcome === 'interested').length

  const fmtDate = (d: string) => {
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

  const typeIconMap: Record<string, any> = { inbound: PhoneIncoming, outbound: PhoneOutgoing, missed: PhoneMissed }
  const typeColorMap: Record<string, string> = { inbound: '#34D399', outbound: '#60A5FA', missed: '#F87171' }

  const metrics = [
    { label: 'Total Calls', value: calls.length, icon: Phone, color: '#A855F7' },
    { label: 'Avg Duration', value: avgDur > 0 ? `${Math.floor(avgDur / 60)}m ${avgDur % 60}s` : '-', icon: Clock, color: '#3B82F6' },
    { label: 'Successful', value: successCount, icon: TrendingUp, color: '#10B981' },
    { label: 'Missed', value: calls.filter(c => c.type === 'missed' || c.outcome === 'no answer' || c.outcome === 'no_answer').length, icon: PhoneMissed, color: '#EF4444' },
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
        <h2 style={{ fontSize: 28, fontWeight: 700, color: '#fff', marginBottom: 4 }}>Calls</h2>
        <p style={{ fontSize: 13, color: '#6B7280' }}>Track and manage all call activity</p>
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

      {/* Calls Table */}
      <div style={{ background: '#13121E', border: '1px solid #2A2840', borderRadius: 16, overflow: 'hidden' }}>
        <div style={{ padding: '16px 24px', borderBottom: '1px solid rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
          <div style={{ position: 'relative', flex: 1, maxWidth: 320 }}>
            <Search size={16} color="#6B7280" style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)' }} />
            <input type="text" placeholder="Search calls..." value={searchQuery}
              onChange={e => { setSearchQuery(e.target.value); setCurrentPage(1) }}
              style={{ width: '100%', background: '#0B0B12', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, padding: '8px 16px 8px 36px', fontSize: 13, color: '#D1D5DB', outline: 'none', fontFamily: 'inherit' }}
            />
          </div>
          <p style={{ fontSize: 12, color: '#6B7280', margin: 0 }}>{filtered.length} calls</p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '50px 2fr 1fr 1fr 1fr 1.2fr 40px', padding: '10px 24px', borderBottom: '1px solid rgba(255,255,255,0.05)', background: 'rgba(255,255,255,0.02)' }}>
          {['', 'Lead', 'Duration', 'Outcome', 'Sentiment', 'Date', ''].map((h, i) => (
            <span key={i} style={{ fontSize: 10, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: 1 }}>{h}</span>
          ))}
        </div>

        <div>
          {paginated.length === 0 ? (
            <div style={{ padding: '48px 0', textAlign: 'center', color: '#6B7280', fontSize: 14 }}>No calls found.</div>
          ) : (
            paginated.map(call => {
              const TypeIcon = typeIconMap[call.type] || Phone
              const typeColor = typeColorMap[call.type] || '#9CA3AF'
              const oc = OUTCOME_COLORS[call.outcome] || { bg: 'rgba(107,114,128,0.1)', color: '#9CA3AF', border: 'rgba(107,114,128,0.2)' }
              const sentimentColor = call.sentiment === 'positive' ? '#34D399' : call.sentiment === 'negative' ? '#F87171' : '#9CA3AF'
              return (
                <div key={call.id} style={{
                  display: 'grid', gridTemplateColumns: '50px 2fr 1fr 1fr 1fr 1.2fr 40px',
                  padding: '14px 24px', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.03)',
                  cursor: 'pointer', transition: 'background 0.15s',
                }}>
                  <TypeIcon size={16} color={typeColor} />
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'linear-gradient(135deg, #A855F7, #D946EF)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 12, fontWeight: 700, flexShrink: 0 }}>
                      {call.leadName.charAt(0)}
                    </div>
                    <div style={{ minWidth: 0 }}>
                      <p style={{ fontSize: 13, fontWeight: 600, color: '#E5E7EB', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{call.leadName}</p>
                      <p style={{ fontSize: 10, color: '#6B7280', margin: '2px 0 0 0' }}>{call.phone}</p>
                    </div>
                  </div>
                  <span style={{ fontSize: 12, color: '#9CA3AF', fontFamily: 'monospace' }}>{call.duration}</span>
                  <div>
                    <span style={{ padding: '3px 10px', borderRadius: 12, fontSize: 10, fontWeight: 600, background: oc.bg, color: oc.color, border: `1px solid ${oc.border}`, textTransform: 'capitalize' }}>
                      {call.outcome.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <span style={{ fontSize: 12, color: sentimentColor, fontWeight: 500, textTransform: 'capitalize' }}>{call.sentiment}</span>
                  <span style={{ fontSize: 12, color: '#6B7280' }}>{fmtDate(call.date)}</span>
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
            <p style={{ fontSize: 12, color: '#6B7280', margin: 0 }}>Page {currentPage} of {totalPages} · {filtered.length} calls</p>
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
