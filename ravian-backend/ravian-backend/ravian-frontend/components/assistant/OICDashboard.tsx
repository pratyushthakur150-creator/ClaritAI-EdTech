'use client'

import React, { useEffect, useState } from 'react'
import { Phone, Clock, CheckCircle, BarChart3 } from 'lucide-react'
import apiClient from '@/lib/api'

interface CallSummary {
  total_calls: number
  completed_calls: number
  total_duration: number
}

export default function OICDashboard() {
  const [summary, setSummary] = useState<CallSummary | null>(null)

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const { data } = await apiClient.get<{ data: any[] }>('/api/v1/calls/', {
          params: { limit: 100 },
        })
        const list = Array.isArray(data?.data) ? data.data : []

        const totalCalls = list.length
        const completed = list.filter(
          (c: any) => c.outcome === 'connected' || c.status === 'completed',
        ).length
        const totalDuration = list.reduce(
          (acc: number, c: any) => acc + (typeof c.duration === 'number' ? c.duration : 0),
          0,
        )

        setSummary({
          total_calls: totalCalls,
          completed_calls: completed,
          total_duration: totalDuration,
        })
      } catch (e) {
        console.error('Failed to load OIC dashboard metrics', e)
      }
    }

    void fetchSummary()
  }, [])

  const total = summary?.total_calls ?? 0
  const completed = summary?.completed_calls ?? 0
  const avgSeconds = total ? Math.round((summary?.total_duration ?? 0) / total) : 0
  const avgMinutes = Math.floor(avgSeconds / 60)
  const avgRemSeconds = avgSeconds % 60
  const avgDurationLabel = total ? `${avgMinutes}m ${avgRemSeconds}s` : '0m 0s'
  const successRate = total ? Math.round((completed / total) * 100) : 0
  const engagementLabel = successRate >= 70 ? 'High' : successRate >= 40 ? 'Medium' : 'Low'

  const stats = [
    {
      label: 'Total Calls',
      value: String(total),
      icon: Phone,
      gradient: 'linear-gradient(135deg, #6366f1, #4f46e5)',
      progressColor: '#6366f1',
      progress: Math.min(total * 10, 100),
    },
    {
      label: 'Avg Duration',
      value: avgDurationLabel,
      icon: Clock,
      gradient: 'linear-gradient(135deg, #8b5cf6, #7c3aed)',
      progressColor: '#8b5cf6',
      progress: Math.min(avgSeconds * 2, 100),
    },
    {
      label: 'Success Rate',
      value: `${successRate}%`,
      icon: CheckCircle,
      gradient: 'linear-gradient(135deg, #10b981, #059669)',
      progressColor: '#10b981',
      progress: successRate,
    },
    {
      label: 'Engagement',
      value: engagementLabel,
      icon: BarChart3,
      gradient: 'linear-gradient(135deg, #f59e0b, #d97706)',
      progressColor: '#f59e0b',
      progress: successRate >= 70 ? 90 : successRate >= 40 ? 55 : 20,
    },
  ]

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {stats.map((stat, index) => (
        <div
          key={index}
          className="bg-white rounded-2xl border border-slate-200/80 p-4 transition-all duration-300 hover:shadow-lg hover:shadow-slate-200/50 hover:-translate-y-0.5 group cursor-default"
        >
          <div className="flex items-center gap-3 mb-3">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0 shadow-sm transition-transform duration-300 group-hover:scale-110"
              style={{ background: stat.gradient }}
            >
              <stat.icon className="w-[18px] h-[18px] text-white" />
            </div>
            <div className="min-w-0">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">{stat.label}</p>
              <p className="text-lg font-bold text-slate-900 leading-tight">{stat.value}</p>
            </div>
          </div>
          {/* Progress bar */}
          <div className="h-1 rounded-full bg-slate-100 overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-700 ease-out"
              style={{
                width: `${stat.progress}%`,
                background: stat.gradient,
              }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}
