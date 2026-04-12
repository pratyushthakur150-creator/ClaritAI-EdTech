"use client"

import { useQuery } from '@tanstack/react-query'
import apiClient from '@/lib/api'
import { Filter, TrendingDown, ArrowRight, ArrowDown, Target, Users, Zap, AlertTriangle, CheckCircle } from 'lucide-react'

interface FunnelStage { label: string; value: number; color: string; pct: number }

const COLORS = ['#A855F7', '#C084FC', '#818CF8', '#60A5FA', '#22D3EE', '#34D399']

export default function FunnelPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['funnel'],
    queryFn: async () => { try { const res = await apiClient.get(`/api/v1/analytics/funnel`); return res.data } catch { return null } },
  })

  const funnelData = data?.stages || data?.funnel || null
  const defaultStages = [
    { label: 'Lead', value: 0, color: COLORS[0], pct: 100 },
    { label: 'Contacted', value: 0, color: COLORS[1], pct: 75 },
    { label: 'Qualified', value: 0, color: COLORS[2], pct: 55 },
    { label: 'Demo Attended', value: 0, color: COLORS[3], pct: 40 },
    { label: 'Enrolled', value: 0, color: COLORS[4], pct: 18 },
  ]

  const stages: FunnelStage[] = funnelData ? funnelData.map((s: any, i: number) => {
    const maxVal = funnelData[0]?.value || funnelData[0]?.count || 1
    const val = s.value || s.count || 0
    return {
      label: s.label || s.stage || s.name || `Stage ${i + 1}`,
      value: val,
      color: COLORS[i % COLORS.length],
      pct: Math.round((val / maxVal) * 100),
    }
  }) : defaultStages

  const convRate = stages[0]?.value > 0 ? ((stages[stages.length - 1].value / stages[0].value) * 100).toFixed(1) : '0.0'

  // Find biggest drop-off
  let biggestDrop = { from: '', to: '', dropPct: 0, index: 0 }
  for (let i = 1; i < stages.length; i++) {
    if (stages[i - 1].value > 0) {
      const drop = Math.round(((stages[i - 1].value - stages[i].value) / stages[i - 1].value) * 100)
      if (drop > biggestDrop.dropPct) {
        biggestDrop = { from: stages[i - 1].label, to: stages[i].label, dropPct: drop, index: i }
      }
    }
  }

  // Best conversion stage
  let bestConv = { from: '', to: '', convPct: 0 }
  for (let i = 1; i < stages.length; i++) {
    if (stages[i - 1].value > 0) {
      const conv = Math.round((stages[i].value / stages[i - 1].value) * 100)
      if (conv > bestConv.convPct) {
        bestConv = { from: stages[i - 1].label, to: stages[i].label, convPct: conv }
      }
    }
  }

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
        <h2 style={{ fontSize: 28, fontWeight: 700, color: '#fff', marginBottom: 4 }}>Conversion Funnel</h2>
        <p style={{ fontSize: 13, color: '#6B7280' }}>Visualize your lead-to-enrollment pipeline</p>
      </div>

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
        {[
          { label: 'Total Leads', value: stages[0]?.value || 0, icon: Users, color: '#A855F7', sub: 'Pipeline entry' },
          { label: 'Enrolled', value: stages[stages.length - 1]?.value || 0, icon: CheckCircle, color: '#10B981', sub: 'Final stage' },
          { label: 'Conversion', value: `${convRate}%`, icon: Target, color: '#3B82F6', sub: 'End-to-end' },
          { label: 'Biggest Drop', value: `${biggestDrop.dropPct}%`, icon: AlertTriangle, color: '#EF4444', sub: `${biggestDrop.from} → ${biggestDrop.to}` },
        ].map((m, i) => {
          const Icon = m.icon
          return (
            <div key={i} style={{ background: '#13121E', border: '1px solid #2A2840', borderRadius: 16, padding: 20, position: 'relative', overflow: 'hidden' }}>
              <div style={{ position: 'absolute', top: -16, right: -16, width: 60, height: 60, background: m.color, borderRadius: '50%', filter: 'blur(30px)', opacity: 0.12 }} />
              <div style={{ position: 'relative', zIndex: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <p style={{ fontSize: 11, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: 1, margin: 0 }}>{m.label}</p>
                  <p style={{ fontSize: 24, fontWeight: 700, color: '#fff', margin: '4px 0 0 0' }}>{m.value}</p>
                  <p style={{ fontSize: 11, color: '#4B5563', margin: '4px 0 0 0' }}>{m.sub}</p>
                </div>
                <div style={{ width: 40, height: 40, borderRadius: 12, background: m.color, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Icon size={20} color="#fff" />
                </div>
              </div>
            </div>
          )
        })}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 24 }}>
        {/* Main Funnel */}
        <div style={{ background: '#13121E', border: '1px solid #2A2840', borderRadius: 16, padding: 28 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }}>
            <h3 style={{ fontWeight: 600, color: '#fff', fontSize: 15, margin: 0 }}>Pipeline Stages</h3>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#6B7280' }}>
              <Filter size={14} /> Last 30 days
            </div>
          </div>

          {/* Visual Funnel Shape */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            {stages.map((stage, i) => {
              const barWidth = Math.max(12, stage.pct)
              const dropPct = i > 0 && stages[i - 1].value > 0
                ? Math.round(((stages[i - 1].value - stage.value) / stages[i - 1].value) * 100)
                : 0
              const convPct = i > 0 && stages[i - 1].value > 0
                ? Math.round((stage.value / stages[i - 1].value) * 100)
                : 100

              return (
                <div key={i}>
                  {/* Stage Row */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                    {/* Stage number */}
                    <div style={{
                      width: 28, height: 28, borderRadius: '50%', flexShrink: 0,
                      background: stage.color, display: 'flex', alignItems: 'center', justifyContent: 'center',
                      color: '#fff', fontSize: 12, fontWeight: 700,
                      boxShadow: `0 0 12px ${stage.color}40`,
                    }}>{i + 1}</div>

                    {/* Bar container */}
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                        <span style={{ fontSize: 13, fontWeight: 500, color: '#D1D5DB' }}>{stage.label}</span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span style={{ fontSize: 18, fontWeight: 700, color: '#fff' }}>{stage.value.toLocaleString()}</span>
                          <span style={{ fontSize: 11, color: '#6B7280' }}>({stage.pct}%)</span>
                        </div>
                      </div>
                      <div style={{ height: 12, background: 'rgba(31,41,55,0.5)', borderRadius: 6, overflow: 'hidden', border: '1px solid rgba(255,255,255,0.05)' }}>
                        <div style={{
                          height: '100%', borderRadius: 6,
                          width: `${barWidth}%`,
                          background: `linear-gradient(90deg, ${stage.color}, ${stage.color}88)`,
                          boxShadow: `0 0 16px ${stage.color}30`,
                          transition: 'width 0.8s ease',
                          position: 'relative',
                        }}>
                          <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(180deg, rgba(255,255,255,0.15) 0%, transparent 100%)', borderRadius: 6 }} />
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Connector with conversion info */}
                  {i < stages.length - 1 && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 16, padding: '6px 0', marginLeft: 14 }}>
                      <div style={{ width: 1, height: 20, background: 'rgba(255,255,255,0.08)' }} />
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <ArrowDown size={12} color="#6B7280" />
                        <span style={{ fontSize: 11, fontWeight: 600, color: '#34D399' }}>{convPct}% convert</span>
                        <span style={{ fontSize: 11, color: '#6B7280' }}>·</span>
                        <span style={{ fontSize: 11, color: '#F87171' }}>{dropPct}% drop</span>
                        <span style={{ fontSize: 11, color: '#6B7280' }}>(-{stages[i].value - stages[i + 1].value})</span>
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          {/* Overall Conversion */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12, marginTop: 24, paddingTop: 20, borderTop: '1px solid rgba(255,255,255,0.05)' }}>
            <Target size={18} color="#A855F7" />
            <span style={{ fontSize: 14, color: '#9CA3AF' }}>Overall Conversion:</span>
            <span style={{ fontSize: 26, fontWeight: 700, color: '#A855F7' }}>{convRate}%</span>
          </div>
        </div>

        {/* Right Panel: Insights */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Conversion Insights */}
          <div style={{ background: '#13121E', border: '1px solid #2A2840', borderRadius: 16, padding: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
              <Zap size={16} color="#FBBF24" />
              <h3 style={{ fontWeight: 600, color: '#fff', fontSize: 14, margin: 0 }}>Key Insights</h3>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {/* Biggest Drop */}
              <div style={{ background: 'rgba(239,68,68,0.05)', border: '1px solid rgba(239,68,68,0.1)', borderRadius: 12, padding: 14 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                  <AlertTriangle size={14} color="#F87171" />
                  <span style={{ fontSize: 11, fontWeight: 700, color: '#F87171', textTransform: 'uppercase' }}>Biggest Drop-off</span>
                </div>
                <p style={{ fontSize: 13, color: '#D1D5DB', margin: 0 }}>
                  <span style={{ fontWeight: 700, color: '#fff' }}>{biggestDrop.dropPct}%</span> lost from {biggestDrop.from} → {biggestDrop.to}
                </p>
                <p style={{ fontSize: 11, color: '#6B7280', margin: '4px 0 0 0' }}>
                  {(stages[biggestDrop.index - 1]?.value || 0) - (stages[biggestDrop.index]?.value || 0)} leads dropped here
                </p>
              </div>

              {/* Best Step */}
              <div style={{ background: 'rgba(16,185,129,0.05)', border: '1px solid rgba(16,185,129,0.1)', borderRadius: 12, padding: 14 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                  <CheckCircle size={14} color="#34D399" />
                  <span style={{ fontSize: 11, fontWeight: 700, color: '#34D399', textTransform: 'uppercase' }}>Best Conversion</span>
                </div>
                <p style={{ fontSize: 13, color: '#D1D5DB', margin: 0 }}>
                  <span style={{ fontWeight: 700, color: '#fff' }}>{bestConv.convPct}%</span> convert from {bestConv.from} → {bestConv.to}
                </p>
              </div>

              {/* Pipeline Health */}
              <div style={{ background: 'rgba(59,130,246,0.05)', border: '1px solid rgba(59,130,246,0.1)', borderRadius: 12, padding: 14 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                  <Target size={14} color="#60A5FA" />
                  <span style={{ fontSize: 11, fontWeight: 700, color: '#60A5FA', textTransform: 'uppercase' }}>Pipeline Health</span>
                </div>
                <p style={{ fontSize: 13, color: '#D1D5DB', margin: 0 }}>
                  {Number(convRate) >= 10 ? '✅ Healthy — above 10% benchmark' : '⚠️ Below 10% industry benchmark'}
                </p>
              </div>
            </div>
          </div>

          {/* Stage Breakdown Cards */}
          <div style={{ background: '#13121E', border: '1px solid #2A2840', borderRadius: 16, padding: 20 }}>
            <h3 style={{ fontWeight: 600, color: '#fff', fontSize: 14, margin: '0 0 16px 0' }}>Stage Breakdown</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {stages.map((stage, i) => {
                const nextConv = i < stages.length - 1 && stage.value > 0
                  ? Math.round((stages[i + 1].value / stage.value) * 100) : null
                return (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 0', borderBottom: i < stages.length - 1 ? '1px solid rgba(255,255,255,0.05)' : 'none' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={{ width: 8, height: 8, borderRadius: '50%', background: stage.color, boxShadow: `0 0 6px ${stage.color}60` }} />
                      <span style={{ fontSize: 12, color: '#9CA3AF' }}>{stage.label}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ fontSize: 15, fontWeight: 700, color: '#fff' }}>{stage.value}</span>
                      {nextConv !== null && (
                        <span style={{ fontSize: 10, color: '#6B7280', display: 'flex', alignItems: 'center', gap: 2 }}>
                          <ArrowRight size={10} /> {nextConv}%
                        </span>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Recommendations */}
          <div style={{ background: 'linear-gradient(135deg, rgba(168,85,247,0.08), rgba(217,70,239,0.04))', border: '1px solid rgba(168,85,247,0.15)', borderRadius: 16, padding: 20 }}>
            <h3 style={{ fontWeight: 600, color: '#D8B4FE', fontSize: 13, margin: '0 0 12px 0' }}>💡 AI Recommendations</h3>
            <ul style={{ margin: 0, padding: '0 0 0 16px', display: 'flex', flexDirection: 'column', gap: 8 }}>
              <li style={{ fontSize: 12, color: '#C4B5FD' }}>
                Focus on <span style={{ color: '#fff', fontWeight: 600 }}>{biggestDrop.from} → {biggestDrop.to}</span> stage — {biggestDrop.dropPct}% drop is your biggest bottleneck
              </li>
              <li style={{ fontSize: 12, color: '#C4B5FD' }}>
                {stages[stages.length - 1]?.value || 0} enrolled from {stages[0]?.value || 0} leads suggests {Number(convRate) > 8 ? 'a strong' : 'room to improve'} funnel
              </li>
              <li style={{ fontSize: 12, color: '#C4B5FD' }}>
                Consider automated follow-ups for the {(stages[0]?.value || 0) - (stages[1]?.value || 0)} leads who haven't been contacted
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
