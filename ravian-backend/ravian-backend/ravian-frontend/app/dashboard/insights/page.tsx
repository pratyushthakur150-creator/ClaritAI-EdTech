"use client"

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import apiClient from '@/lib/api'
import { TrendingUp, Users, IndianRupee, BarChart3, Activity, ArrowUpRight, GraduationCap, PieChart } from 'lucide-react'

export default function InsightsPage() {
  const [period, setPeriod] = useState<'week' | 'month' | 'year'>('month')

  // Fetch from analytics/overview which has real chart data
  const { data: overviewData, isLoading: loadingOverview } = useQuery({
    queryKey: ['analytics-overview', period],
    queryFn: async () => {
      const days = period === 'week' ? 7 : period === 'month' ? 30 : 365
      try { const res = await apiClient.get(`/api/v1/analytics/overview`, { params: { days } }); return res.data } catch { return null }
    },
  })

  // Also fetch dashboard stats for more data
  const { data: dashData, isLoading: loadingDash } = useQuery({
    queryKey: ['dashboard-stats-insights'],
    queryFn: async () => { try { const res = await apiClient.get(`/api/v1/dashboard/stats`); return res.data } catch { return null } },
  })

  const isLoading = loadingOverview && loadingDash

  const totalLeads = overviewData?.total_leads || dashData?.total_leads || 0
  const totalEnrollments = overviewData?.conversions || dashData?.enrollments || 0
  const totalRevenue = overviewData?.revenue || dashData?.total_revenue || 0
  const activeStudents = overviewData?.active_students || 0
  const convRate = overviewData?.conversion_rate || dashData?.conversion_rate || 0

  const leadsOverTime = overviewData?.leads_over_time || []
  const leadSources = overviewData?.lead_sources || []
  const coursesPopularity = overviewData?.courses_popularity || []

  // Build leads by status from dashboard stats
  const leadsByStatus = dashData?.leads_by_status || {}
  const activityFeed: any[] = dashData?.activity_feed || []

  const kpis = [
    { label: 'Total Revenue', value: totalRevenue > 0 ? `₹${totalRevenue.toLocaleString('en-IN')}` : '₹0', icon: IndianRupee, color: '#A855F7' },
    { label: 'Enrollments', value: totalEnrollments, icon: GraduationCap, color: '#10B981' },
    { label: 'Conversion Rate', value: `${convRate}%`, icon: TrendingUp, color: '#3B82F6' },
    { label: 'Total Leads', value: totalLeads, icon: Users, color: '#F59E0B' },
  ]

  if (isLoading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
        <div style={{ width: 40, height: 40, border: '3px solid #A855F7', borderTop: '3px solid transparent', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
        <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
      </div>
    )
  }

  const maxLeadVal = Math.max(...leadsOverTime.map((l: any) => l.leads || 0), 1)

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 32 }}>
        <div>
          <h2 style={{ fontSize: 28, fontWeight: 700, color: '#fff', marginBottom: 4 }}>Insights & Analytics</h2>
          <p style={{ fontSize: 13, color: '#6B7280', margin: 0 }}>Performance metrics and engagement trends</p>
        </div>
        <div style={{ display: 'flex', background: 'rgba(0,0,0,0.4)', borderRadius: 8, padding: 3, border: '1px solid rgba(255,255,255,0.05)' }}>
          {(['week', 'month', 'year'] as const).map(p => (
            <button key={p} onClick={() => setPeriod(p)}
              style={{
                padding: '6px 14px', borderRadius: 6, fontSize: 11, fontWeight: 700,
                textTransform: 'uppercase', letterSpacing: 0.5, border: 'none', cursor: 'pointer',
                background: period === p ? '#A855F7' : 'transparent',
                color: period === p ? '#fff' : '#6B7280',
                boxShadow: period === p ? '0 2px 8px rgba(168,85,247,0.3)' : 'none',
                fontFamily: 'inherit',
              }}>{p}</button>
          ))}
        </div>
      </div>

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
        {kpis.map((kpi, i) => {
          const Icon = kpi.icon
          return (
            <div key={i} style={{ background: '#13121E', border: '1px solid #2A2840', borderRadius: 16, padding: 20, position: 'relative', overflow: 'hidden' }}>
              <div style={{ position: 'absolute', top: -16, right: -16, width: 60, height: 60, background: kpi.color, borderRadius: '50%', filter: 'blur(30px)', opacity: 0.12 }} />
              <div style={{ position: 'relative', zIndex: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <p style={{ fontSize: 11, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: 1, margin: 0 }}>{kpi.label}</p>
                  <p style={{ fontSize: 24, fontWeight: 700, color: '#fff', margin: '4px 0 0 0' }}>{kpi.value}</p>
                </div>
                <div style={{ width: 40, height: 40, borderRadius: 12, background: kpi.color, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Icon size={20} color="#fff" />
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginTop: 12 }}>
                <ArrowUpRight size={14} color="#4ADE80" />
                <span style={{ fontSize: 12, fontWeight: 500, color: '#4ADE80' }}>+12.5%</span>
                <span style={{ fontSize: 12, color: '#4B5563', marginLeft: 4 }}>vs last {period}</span>
              </div>
            </div>
          )
        })}
      </div>

      {/* Leads Over Time Chart */}
      <div style={{ background: '#13121E', border: '1px solid #2A2840', borderRadius: 16, padding: 24, marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
          <div style={{ width: 36, height: 36, borderRadius: 10, background: 'linear-gradient(135deg, #A855F7, #D946EF)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <BarChart3 size={18} color="#fff" />
          </div>
          <h3 style={{ fontWeight: 600, color: '#fff', fontSize: 15, margin: 0 }}>Leads Over Time</h3>
          <span style={{ fontSize: 12, color: '#6B7280', marginLeft: 'auto' }}>{leadsOverTime.length} data points</span>
        </div>
        {leadsOverTime.length > 0 ? (
          <div>
            <div style={{ display: 'flex', alignItems: 'flex-end', gap: 2, height: 160, paddingBottom: 4 }}>
              {leadsOverTime.map((point: any, i: number) => {
                const h = Math.max(4, (point.leads / maxLeadVal) * 140)
                return (
                  <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4, cursor: 'pointer', position: 'relative' }} title={`${point.name}: ${point.leads} leads`}>
                    <div style={{
                      width: '100%', maxWidth: 28, borderRadius: 4,
                      height: h,
                      background: point.leads > 0 ? 'linear-gradient(180deg, #A855F7, #D946EF88)' : 'rgba(31,41,55,0.5)',
                      boxShadow: point.leads > 0 ? '0 0 8px rgba(168,85,247,0.2)' : 'none',
                      transition: 'height 0.3s ease',
                    }} />
                  </div>
                )
              })}
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6, paddingTop: 6, borderTop: '1px solid rgba(255,255,255,0.05)' }}>
              <span style={{ fontSize: 10, color: '#6B7280' }}>{leadsOverTime[0]?.name}</span>
              {leadsOverTime.length > 2 && <span style={{ fontSize: 10, color: '#6B7280' }}>{leadsOverTime[Math.floor(leadsOverTime.length / 2)]?.name}</span>}
              <span style={{ fontSize: 10, color: '#6B7280' }}>{leadsOverTime[leadsOverTime.length - 1]?.name}</span>
            </div>
          </div>
        ) : (
          <div style={{ height: 160, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#6B7280', fontSize: 13 }}>No data for this period</div>
        )}
      </div>

      {/* Charts Row: Lead Sources + Courses Popularity */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 24 }}>
        {/* Lead Sources */}
        <div style={{ background: '#13121E', border: '1px solid #2A2840', borderRadius: 16, padding: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
            <div style={{ width: 36, height: 36, borderRadius: 10, background: 'linear-gradient(135deg, #3B82F6, #06B6D4)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <PieChart size={18} color="#fff" />
            </div>
            <h3 style={{ fontWeight: 600, color: '#fff', fontSize: 15, margin: 0 }}>Lead Sources</h3>
          </div>
          {leadSources.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {leadSources.map((src: any, i: number) => {
                const total = leadSources.reduce((s: number, l: any) => s + l.value, 0)
                const pct = total > 0 ? Math.round((src.value / total) * 100) : 0
                return (
                  <div key={i}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <div style={{ width: 8, height: 8, borderRadius: '50%', background: src.color || '#A855F7' }} />
                        <span style={{ fontSize: 12, color: '#D1D5DB' }}>{src.name}</span>
                      </div>
                      <span style={{ fontSize: 12, fontWeight: 600, color: '#fff' }}>{src.value} ({pct}%)</span>
                    </div>
                    <div style={{ height: 6, background: '#1F2937', borderRadius: 3, overflow: 'hidden' }}>
                      <div style={{ height: '100%', borderRadius: 3, background: src.color || '#A855F7', width: `${pct}%`, transition: 'width 0.5s' }} />
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <div style={{ height: 120, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#6B7280', fontSize: 13 }}>No source data</div>
          )}
        </div>

        {/* Courses Popularity */}
        <div style={{ background: '#13121E', border: '1px solid #2A2840', borderRadius: 16, padding: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
            <div style={{ width: 36, height: 36, borderRadius: 10, background: 'linear-gradient(135deg, #10B981, #14B8A6)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <GraduationCap size={18} color="#fff" />
            </div>
            <h3 style={{ fontWeight: 600, color: '#fff', fontSize: 15, margin: 0 }}>Popular Courses</h3>
          </div>
          {coursesPopularity.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {coursesPopularity.map((course: any, i: number) => {
                const maxStudents = Math.max(...coursesPopularity.map((c: any) => c.students), 1)
                const pct = Math.round((course.students / maxStudents) * 100)
                const colors = ['#10B981', '#3B82F6', '#A855F7', '#F59E0B', '#EF4444', '#6366F1', '#EC4899', '#14B8A6']
                return (
                  <div key={i}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ fontSize: 12, color: '#D1D5DB', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1, marginRight: 8 }}>{course.name}</span>
                      <span style={{ fontSize: 12, fontWeight: 600, color: '#fff', flexShrink: 0 }}>{course.students} students</span>
                    </div>
                    <div style={{ height: 6, background: '#1F2937', borderRadius: 3, overflow: 'hidden' }}>
                      <div style={{ height: '100%', borderRadius: 3, background: colors[i % colors.length], width: `${pct}%`, transition: 'width 0.5s' }} />
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <div style={{ height: 120, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#6B7280', fontSize: 13 }}>No course data</div>
          )}
        </div>
      </div>

      {/* Lead Pipeline + Activity Feed */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        {/* Lead Pipeline */}
        <div style={{ background: '#13121E', border: '1px solid #2A2840', borderRadius: 16, padding: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
            <div style={{ width: 36, height: 36, borderRadius: 10, background: 'linear-gradient(135deg, #F59E0B, #EF4444)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Activity size={18} color="#fff" />
            </div>
            <h3 style={{ fontWeight: 600, color: '#fff', fontSize: 15, margin: 0 }}>Lead Pipeline</h3>
          </div>
          {Object.entries(leadsByStatus).length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {Object.entries(leadsByStatus).map(([status, count], i) => {
                const maxVal = Math.max(...Object.values(leadsByStatus).map(Number), 1)
                const pct = Math.round((Number(count) / maxVal) * 100)
                const colors = ['#3B82F6', '#F59E0B', '#06B6D4', '#10B981', '#A855F7', '#EF4444', '#6366F1']
                return (
                  <div key={status}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ fontSize: 12, color: '#9CA3AF', textTransform: 'capitalize' }}>{status.replace(/_/g, ' ').toLowerCase()}</span>
                      <span style={{ fontSize: 13, fontWeight: 600, color: '#fff' }}>{String(count)}</span>
                    </div>
                    <div style={{ height: 6, background: '#1F2937', borderRadius: 3, overflow: 'hidden' }}>
                      <div style={{ height: '100%', borderRadius: 3, background: colors[i % colors.length], width: `${pct}%` }} />
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <div style={{ height: 120, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#6B7280', fontSize: 13 }}>No pipeline data</div>
          )}
        </div>

        {/* Activity Feed */}
        <div style={{ background: '#13121E', border: '1px solid #2A2840', borderRadius: 16, overflow: 'hidden' }}>
          <div style={{ padding: '16px 24px', borderBottom: '1px solid rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ width: 32, height: 32, borderRadius: 8, background: 'linear-gradient(135deg, #6366F1, #A855F7)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Activity size={16} color="#fff" />
            </div>
            <h3 style={{ fontWeight: 600, color: '#fff', fontSize: 14, margin: 0 }}>Recent Activity</h3>
          </div>
          <div style={{ maxHeight: 280, overflowY: 'auto' }}>
            {activityFeed.length > 0 ? (
              activityFeed.slice(0, 10).map((item: any, i: number) => (
                <div key={i} style={{ padding: '10px 24px', borderBottom: '1px solid rgba(255,255,255,0.03)', display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                  <div style={{ width: 28, height: 28, borderRadius: '50%', background: 'linear-gradient(135deg, #A855F7, #D946EF)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 11, fontWeight: 700, flexShrink: 0 }}>
                    {(item.name || item.lead_name || 'U').charAt(0)}
                  </div>
                  <div>
                    <p style={{ fontSize: 12, color: '#D1D5DB', margin: 0 }}>
                      <span style={{ fontWeight: 600, color: '#fff' }}>{item.name || item.lead_name || 'User'}</span>{' '}
                      {item.action || item.description || item.event_type || 'performed an action'}
                    </p>
                    <p style={{ fontSize: 11, color: '#6B7280', margin: '2px 0 0 0' }}>{item.time || item.timestamp || ''}</p>
                  </div>
                </div>
              ))
            ) : (
              <div style={{ padding: '32px 0', textAlign: 'center', color: '#6B7280', fontSize: 13 }}>No recent activity</div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
