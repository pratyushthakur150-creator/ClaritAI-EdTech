"use client"

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import apiClient from '@/lib/api'
import { Users, Phone, CalendarCheck, GraduationCap, TrendingUp, MessageCircle, Target } from 'lucide-react'

export default function DashboardPage() {
  const [activityTab, setActivityTab] = useState<'all' | 'updates'>('all')
  const [progressRange, setProgressRange] = useState<'week' | 'month' | 'max'>('max')

  const { data: metrics, isLoading } = useQuery({
    queryKey: ['dashboard-metrics'],
    queryFn: async () => {
      const res = await apiClient.get(`/api/v1/dashboard/stats`)
      return res.data
    },
  })

  // ── Extract data ──
  const userName = metrics?.user_name || 'User'
  const lastUpdate = metrics?.last_update || 'Loading...'
  const totalLeads = metrics?.total_leads ?? 0
  const demosScheduled = metrics?.demos_scheduled ?? 0
  const enrollments = metrics?.enrollments ?? 0
  const totalCalls = metrics?.total_calls ?? 0
  const totalRevenue = metrics?.total_revenue ?? 0
  const conversionRate = metrics?.conversion_rate ?? '0.0'
  const noShows = metrics?.no_shows ?? 0
  const avgCallTime = metrics?.avg_call_time ?? '0m 0s'
  const chatbotSessions = metrics?.chatbot_sessions ?? 0
  const leadsTrend = metrics?.leads_trend ?? 0
  const demosTrend = metrics?.demos_trend ?? 0
  const enrollmentsTrend = metrics?.enrollments_trend ?? 0
  const conversionTrend = metrics?.conversion_trend ?? 0
  const learningProgress = metrics?.learning_progress ?? { activities: 0, modules: 0, quizzes: 0 }
  const subjectTraffic = metrics?.subject_traffic ?? { total: 0, trend: 0, subjects: [] }
  const activityFeed: any[] = metrics?.activity_feed ?? []
  const leadsByStatus = metrics?.leads_by_status ?? {}

  const filteredActivities = activityTab === 'updates' ? activityFeed.filter((a: any) => a.type === 'update') : activityFeed
  const todayActivities = filteredActivities.filter((a: any) => a.section === 'today')
  const yesterdayActivities = filteredActivities.filter((a: any) => a.section === 'yesterday')

  const formatRevenue = (val: number) => {
    if (val >= 100000) return `₹${(val / 100000).toFixed(1)}L`
    if (val >= 1000) return `₹${(val / 1000).toFixed(1)}K`
    return `₹${val}`
  }

  const kpis = [
    { label: 'Total Leads', value: totalLeads, trend: leadsTrend, icon: Users, color: '#3B82F6' },
    { label: 'Demos Scheduled', value: demosScheduled, trend: demosTrend, icon: CalendarCheck, color: '#F59E0B' },
    { label: 'Enrollments', value: enrollments, trend: enrollmentsTrend, icon: GraduationCap, color: '#10B981' },
    { label: 'Conversion Rate', value: `${conversionRate}%`, trend: conversionTrend, icon: Target, color: '#A855F7' },
    { label: 'Total Calls', value: totalCalls, trend: 0, icon: Phone, color: '#EC4899' },
    { label: 'Chat Sessions', value: chatbotSessions, trend: 0, icon: MessageCircle, color: '#6366F1' },
  ]

  const statusColors: Record<string, string> = {
    NEW: '#3B82F6', CONTACTED: '#F59E0B', DEMO_SCHEDULED: '#06B6D4',
    QUALIFIED: '#10B981', ENROLLED: '#A855F7', LOST: '#EF4444',
    NURTURING: '#6366F1',
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
    <div style={{ opacity: 1 }}>
      {/* Welcome */}
      <div style={{ marginBottom: 32 }}>
        <h2 style={{ fontSize: 28, fontWeight: 700, color: '#fff', marginBottom: 4 }}>Welcome back, {userName}!</h2>
        <p style={{ fontSize: 13, color: '#6B7280' }}>Last update: {lastUpdate}</p>
      </div>

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 16, marginBottom: 24 }}>
        {kpis.map((kpi, i) => (
          <div key={i} style={{
            background: '#13121E', border: '1px solid #2A2840', borderRadius: 16, padding: 20,
            position: 'relative', overflow: 'hidden', transition: 'border-color 0.3s',
          }}>
            <div style={{ position: 'absolute', top: -20, right: -20, width: 60, height: 60, background: kpi.color, borderRadius: '50%', filter: 'blur(30px)', opacity: 0.15 }} />
            <div style={{ position: 'relative', zIndex: 1 }}>
              <div style={{ width: 36, height: 36, borderRadius: 10, background: kpi.color, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 12 }}>
                <kpi.icon size={18} color="#fff" />
              </div>
              <div style={{ fontSize: 28, fontWeight: 700, color: '#fff', marginBottom: 4 }}>
                {typeof kpi.value === 'number' ? kpi.value.toLocaleString() : kpi.value}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: 10, color: '#6B7280', textTransform: 'uppercase', letterSpacing: 1, fontWeight: 600 }}>{kpi.label}</span>
                {kpi.trend !== 0 && (
                  <span style={{
                    fontSize: 10, fontWeight: 600, padding: '2px 6px', borderRadius: 4,
                    color: kpi.trend > 0 ? '#4ADE80' : '#F87171',
                    background: kpi.trend > 0 ? 'rgba(74,222,128,0.1)' : 'rgba(248,113,113,0.1)',
                  }}>
                    {kpi.trend > 0 ? '↑' : '↓'}{Math.abs(kpi.trend)}%
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Second row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 24, marginBottom: 24 }}>
        {/* Revenue + Avg Call + No Shows */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Revenue */}
          <div style={{ background: '#13121E', border: '1px solid #2A2840', borderRadius: 16, padding: 24, position: 'relative', overflow: 'hidden' }}>
            <div style={{ position: 'absolute', top: -30, right: -30, width: 100, height: 100, background: '#A855F7', borderRadius: '50%', filter: 'blur(50px)', opacity: 0.1 }} />
            <div style={{ position: 'relative', zIndex: 1 }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 }}>Total Revenue</div>
              <div style={{ fontSize: 36, fontWeight: 700, color: '#fff', marginBottom: 8 }}>{formatRevenue(totalRevenue)}</div>
              <p style={{ fontSize: 12, color: '#9CA3AF' }}>From {enrollments} enrollments</p>
            </div>
          </div>
          {/* Avg Call */}
          <div style={{ background: '#13121E', border: '1px solid #2A2840', borderRadius: 16, padding: 24 }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 }}>Avg Call Duration</div>
            <div style={{ fontSize: 28, fontWeight: 700, color: '#fff' }}>{avgCallTime}</div>
            <p style={{ fontSize: 12, color: '#9CA3AF', marginTop: 4 }}>{totalCalls} calls total</p>
          </div>
          {/* No Shows */}
          <div style={{ background: '#13121E', border: '1px solid #2A2840', borderRadius: 16, padding: 24 }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 }}>Demo No-Shows</div>
            <div style={{ display: 'flex', alignItems: 'flex-end', gap: 12 }}>
              <span style={{ fontSize: 28, fontWeight: 700, color: '#fff' }}>{noShows}</span>
              <span style={{ fontSize: 12, color: '#9CA3AF', paddingBottom: 4 }}>of {demosScheduled} demos</span>
            </div>
          </div>
        </div>

        {/* Lead Pipeline */}
        <div style={{ background: '#13121E', border: '1px solid #2A2840', borderRadius: 16, padding: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
            <div style={{ width: 36, height: 36, borderRadius: 10, background: 'linear-gradient(135deg, #A855F7, #D946EF)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <TrendingUp size={18} color="#fff" />
            </div>
            <h3 style={{ fontWeight: 600, color: '#fff', fontSize: 16 }}>Lead Pipeline</h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {Object.entries(leadsByStatus).length > 0 ? (
              Object.entries(leadsByStatus).map(([status, count]: [string, any]) => {
                const pct = totalLeads > 0 ? Math.round((count / totalLeads) * 100) : 0
                const barColor = statusColors[status] || '#6B7280'
                return (
                  <div key={status}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                      <span style={{ fontSize: 12, color: '#9CA3AF', textTransform: 'capitalize' }}>{status.toLowerCase().replace(/_/g, ' ')}</span>
                      <span style={{ fontSize: 12, color: '#fff', fontWeight: 600 }}>{count} <span style={{ color: '#6B7280' }}>({pct}%)</span></span>
                    </div>
                    <div style={{ width: '100%', height: 8, background: '#1F2937', borderRadius: 4, overflow: 'hidden' }}>
                      <div style={{ height: '100%', borderRadius: 4, background: barColor, width: `${pct}%`, transition: 'width 0.7s ease' }} />
                    </div>
                  </div>
                )
              })
            ) : (
              <div style={{ textAlign: 'center', padding: '32px 0', color: '#6B7280', fontSize: 13 }}>No lead data. Run seed script.</div>
            )}
          </div>
          <div style={{ marginTop: 24, paddingTop: 16, borderTop: '1px solid rgba(255,255,255,0.05)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: 12, color: '#6B7280' }}>Total in pipeline</span>
            <span style={{ fontSize: 20, fontWeight: 700, color: '#fff' }}>{totalLeads}</span>
          </div>
        </div>

        {/* Activity Feed */}
        <div style={{ background: '#13121E', border: '1px solid #2A2840', borderRadius: 16, padding: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ width: 36, height: 36, borderRadius: 10, background: 'linear-gradient(135deg, #A855F7, #D946EF)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ fontSize: 18 }}>🔔</span>
              </div>
              <h3 style={{ fontWeight: 600, color: '#fff', fontSize: 14 }}>Recent Activity</h3>
            </div>
            <div style={{ display: 'flex', background: 'rgba(0,0,0,0.4)', borderRadius: 8, padding: 3, border: '1px solid rgba(255,255,255,0.05)' }}>
              {(['all', 'updates'] as const).map(tab => (
                <button key={tab} onClick={() => setActivityTab(tab)} style={{
                  padding: '5px 10px', borderRadius: 6, fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 1, border: 'none', cursor: 'pointer',
                  background: activityTab === tab ? '#A855F7' : 'transparent',
                  color: activityTab === tab ? '#fff' : '#6B7280',
                }}>{tab}</button>
              ))}
            </div>
          </div>
          <div style={{ maxHeight: 320, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 16 }}>
            {todayActivities.length > 0 && <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: 1, color: '#6B7280', fontWeight: 700 }}>Today</div>}
            {todayActivities.map((item: any, idx: number) => (
              <div key={idx} style={{ display: 'flex', gap: 12 }}>
                <div style={{ width: 36, height: 36, borderRadius: '50%', background: `linear-gradient(135deg, ${item.gradient?.includes('purple') ? '#A855F7,#EC4899' : item.gradient?.includes('blue') ? '#3B82F6,#06B6D4' : item.gradient?.includes('amber') ? '#F59E0B,#EF4444' : '#6B7280,#374151'})`, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 12, fontWeight: 700, flexShrink: 0 }}>{item.initial}</div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                    <span style={{ fontSize: 13, fontWeight: 600, color: '#fff' }}>{item.user}</span>
                    <span style={{ fontSize: 10, color: '#6B7280', flexShrink: 0 }}>{item.time}</span>
                  </div>
                  <p style={{ fontSize: 12, color: '#9CA3AF' }}>{item.action} <span style={{ color: '#fff', fontWeight: 500 }}>{item.target}</span> {item.context}</p>
                </div>
              </div>
            ))}
            {yesterdayActivities.length > 0 && (
              <>
                <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: 1, color: '#6B7280', fontWeight: 700, paddingTop: 12, borderTop: '1px dashed #374151' }}>Yesterday</div>
                {yesterdayActivities.map((item: any, idx: number) => (
                  <div key={idx} style={{ display: 'flex', gap: 12 }}>
                    <div style={{ width: 36, height: 36, borderRadius: '50%', background: '#1F2937', border: '1px solid #374151', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#9CA3AF', fontSize: 12, flexShrink: 0 }}>{item.initial}</div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                        <span style={{ fontSize: 13, fontWeight: 600, color: '#fff' }}>{item.user}</span>
                        <span style={{ fontSize: 10, color: '#6B7280', flexShrink: 0 }}>{item.time}</span>
                      </div>
                      <p style={{ fontSize: 12, color: '#9CA3AF' }}>{item.action} <span style={{ color: '#fff', fontWeight: 500 }}>{item.target}</span> {item.context}</p>
                    </div>
                  </div>
                ))}
              </>
            )}
            {filteredActivities.length === 0 && (
              <div style={{ textAlign: 'center', padding: '40px 0', color: '#6B7280', fontSize: 13 }}>No recent activity.</div>
            )}
          </div>
        </div>
      </div>

      {/* Third row */}
      <div style={{ display: 'grid', gridTemplateColumns: '5fr 7fr', gap: 24, paddingBottom: 24 }}>
        {/* Platform Overview */}
        <div style={{ background: '#13121E', border: '1px solid #2A2840', borderRadius: 16, padding: 24, position: 'relative', overflow: 'hidden' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ width: 36, height: 36, borderRadius: 10, background: 'linear-gradient(135deg, #A855F7, #D946EF)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ fontSize: 18 }}>📈</span>
              </div>
              <h3 style={{ fontWeight: 600, color: '#fff' }}>Platform Overview</h3>
            </div>
            <div style={{ display: 'flex', background: 'rgba(0,0,0,0.4)', borderRadius: 8, padding: 3, border: '1px solid rgba(255,255,255,0.05)' }}>
              {(['week', 'month', 'max'] as const).map(r => (
                <button key={r} onClick={() => setProgressRange(r)} style={{
                  padding: '4px 10px', borderRadius: 4, fontSize: 10, border: 'none', cursor: 'pointer',
                  background: progressRange === r ? '#374151' : 'transparent',
                  color: progressRange === r ? '#fff' : '#9CA3AF',
                }}>{r.charAt(0).toUpperCase() + r.slice(1)}</button>
              ))}
            </div>
          </div>
          {/* SVG Chart */}
          <div style={{ height: 180, width: '100%' }}>
            <svg width="100%" height="100%" preserveAspectRatio="none" viewBox="0 0 300 150">
              <defs>
                <linearGradient id="gradArea" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="0%" stopColor="#A855F7" stopOpacity="0.3" />
                  <stop offset="100%" stopColor="#A855F7" stopOpacity="0" />
                </linearGradient>
              </defs>
              <path d="M0 130 C 30 120, 50 125, 80 110 S 120 100, 150 90 S 200 85, 240 60 S 280 40, 300 30 V 150 H 0 Z" fill="url(#gradArea)" />
              <path d="M0 130 C 30 120, 50 125, 80 110 S 120 100, 150 90 S 200 85, 240 60 S 280 40, 300 30" fill="none" stroke="#D946EF" strokeWidth="2.5" />
            </svg>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16, marginTop: 24, paddingTop: 16, borderTop: '1px solid rgba(255,255,255,0.05)' }}>
            {[
              { label: 'Leads + Demos + Calls', value: learningProgress.activities },
              { label: 'Enrollments', value: learningProgress.modules },
              { label: 'Chat Sessions', value: learningProgress.quizzes },
            ].map((s, i) => (
              <div key={i} style={{ textAlign: 'center', borderLeft: i === 1 ? '1px solid rgba(255,255,255,0.05)' : 'none', borderRight: i === 1 ? '1px solid rgba(255,255,255,0.05)' : 'none' }}>
                <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: 1, color: '#6B7280', marginBottom: 4 }}>{s.label}</div>
                <div style={{ fontSize: 22, fontWeight: 700, color: '#fff' }}>{s.value?.toLocaleString?.() || 0}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Lead Sources */}
        <div style={{ background: '#13121E', border: '1px solid #2A2840', borderRadius: 16, padding: 24, position: 'relative', overflow: 'hidden' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
            <div style={{ width: 36, height: 36, borderRadius: 10, background: 'linear-gradient(135deg, #A855F7, #D946EF)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <span style={{ fontSize: 18 }}>📊</span>
            </div>
            <h3 style={{ fontWeight: 600, color: '#fff' }}>Lead Sources</h3>
          </div>
          <div style={{ display: 'flex', gap: 32, height: 240 }}>
            <div style={{ width: '33%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
              <div style={{ fontSize: 48, fontWeight: 700, color: '#fff', marginBottom: 12 }}>{subjectTraffic.total?.toLocaleString?.() || 0}</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#4ADE80', marginBottom: 24 }}>
                <span style={{ background: 'rgba(74,222,128,0.1)', borderRadius: '50%', padding: 2 }}>↑</span>
                +{subjectTraffic.trend}% vs last month
              </div>
              <p style={{ fontSize: 12, color: '#9CA3AF', lineHeight: 1.5, marginBottom: 16 }}>Lead acquisition by source shows where your potential students come from.</p>
              <div style={{ display: 'flex', gap: 16, fontSize: 10, color: '#6B7280', textTransform: 'uppercase', letterSpacing: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}><span style={{ width: 8, height: 8, borderRadius: '50%', background: '#D946EF' }} /> Top</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}><span style={{ width: 8, height: 8, borderRadius: '50%', background: '#374151' }} /> Other</div>
              </div>
            </div>
            <div style={{ flex: 1, display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', gap: 12, paddingBottom: 8 }}>
              {(subjectTraffic.subjects || []).length > 0 ? (
                (subjectTraffic.subjects || []).map((bar: any, i: number) => (
                  <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
                    <div style={{
                      width: '100%', borderRadius: '6px 6px 0 0',
                      height: Math.max(bar.value, 20),
                      background: bar.highlight
                        ? 'repeating-linear-gradient(45deg, #D946EF, #D946EF 2px, #A855F7 2px, #A855F7 4px)'
                        : 'rgba(31, 41, 55, 0.5)',
                      borderTop: bar.highlight ? '2px solid rgba(255,255,255,0.3)' : '1px solid rgba(255,255,255,0.05)',
                      boxShadow: bar.highlight ? '0 0 25px rgba(217,70,239,0.3)' : 'none',
                    }} />
                    <span style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 1, color: bar.highlight ? '#D946EF' : '#4B5563' }}>{bar.name}</span>
                  </div>
                ))
              ) : (
                <div style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#6B7280', fontSize: 13 }}>No source data</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
