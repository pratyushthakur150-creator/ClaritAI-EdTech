'use client'

import React, { useEffect, useState } from 'react'
import { PhoneIncoming, PhoneOutgoing, PhoneMissed, Clock, History } from 'lucide-react'
import apiClient from '@/lib/api'

interface HistoryItem {
  id: string
  type: 'inbound' | 'outbound'
  status: 'connected' | 'no_answer' | 'missed'
  durationSeconds: number
  timestamp: string
}

export default function CallHistory() {
  const [history, setHistory] = useState<HistoryItem[]>([])

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const { data } = await apiClient.get<{ data: any[] }>('/api/v1/calls/', {
          params: { limit: 20 },
        })
        const list = Array.isArray(data?.data) ? data.data : []

        const mapped: HistoryItem[] = list.map((c: any) => {
          const status =
            c.outcome === 'connected' || c.status === 'completed'
              ? 'connected'
              : c.outcome === 'no_answer'
                ? 'no_answer'
                : 'missed'

          const type: 'inbound' | 'outbound' =
            c.direction === 'inbound' ? 'inbound' : 'outbound'

          return {
            id: String(c.id),
            type,
            status,
            durationSeconds: typeof c.duration === 'number' ? c.duration : 0,
            timestamp: String(c.created_at ?? c.date ?? new Date().toISOString()),
          }
        })

        setHistory(mapped)
      } catch (e) {
        console.error('Failed to load call history', e)
      }
    }

    void fetchHistory()
  }, [])

  const formatDuration = (seconds: number) => {
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${m}m ${s.toString().padStart(2, '0')}s`
  }

  const timeAgo = (timestamp: string) => {
    const now = Date.now()
    const then = new Date(timestamp).getTime()
    const diff = Math.max(0, now - then)
    const minutes = Math.floor(diff / 60000)
    if (minutes < 1) return 'Just now'
    if (minutes < 60) return `${minutes}m ago`
    const hours = Math.floor(minutes / 60)
    if (hours < 24) return `${hours}h ago`
    const days = Math.floor(hours / 24)
    return `${days}d ago`
  }

  const statusConfig = {
    connected: { label: 'Connected', dot: 'bg-emerald-400', text: 'text-emerald-600', bg: 'bg-emerald-50' },
    no_answer: { label: 'No Answer', dot: 'bg-slate-300', text: 'text-slate-500', bg: 'bg-slate-50' },
    missed: { label: 'Missed Call', dot: 'bg-red-400', text: 'text-red-500', bg: 'bg-red-50' },
  }

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 overflow-hidden flex flex-col">
      {/* Header with gradient and count badge */}
      <div className="px-5 py-3.5 border-b border-slate-100 flex items-center gap-2 justify-between"
        style={{ background: 'linear-gradient(135deg, rgba(99,102,241,0.04), rgba(139,92,246,0.04))' }}>
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-lg flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}>
            <History size={12} className="text-white" />
          </div>
          <h3 className="text-sm font-semibold text-slate-800">Call History</h3>
        </div>
        {history.length > 0 && (
          <span className="text-[10px] font-bold bg-indigo-100 text-indigo-600 px-2 py-0.5 rounded-full">
            {history.length}
          </span>
        )}
      </div>

      <div className="overflow-y-auto flex-1 max-h-[280px]">
        {history.length === 0 ? (
          <div className="px-5 py-10 text-center">
            <div className="w-12 h-12 rounded-2xl bg-slate-100 flex items-center justify-center mx-auto mb-3">
              <PhoneOutgoing size={20} className="text-slate-300" />
            </div>
            <p className="text-xs font-medium text-slate-400">No recent calls</p>
            <p className="text-[10px] text-slate-300 mt-0.5">Calls will appear here after your first session</p>
          </div>
        ) : (
          history.map((call, idx) => {
            const cfg = statusConfig[call.status]
            return (
              <div
                key={call.id}
                className="flex items-center justify-between px-5 py-3 transition-all duration-200 hover:bg-slate-50/80 cursor-default group"
                style={{
                  borderBottom: idx < history.length - 1 ? '1px solid rgba(241,245,249,0.8)' : undefined,
                }}
              >
                <div className="flex items-center gap-3">
                  {/* Status icon with colored bg */}
                  <div className={`w-8 h-8 rounded-xl ${cfg.bg} flex items-center justify-center shrink-0 transition-transform duration-200 group-hover:scale-110`}>
                    {call.type === 'inbound' ? (
                      <PhoneIncoming size={13} className={cfg.text} />
                    ) : call.status === 'missed' ? (
                      <PhoneMissed size={13} className={cfg.text} />
                    ) : (
                      <PhoneOutgoing size={13} className={cfg.text} />
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-1.5">
                      {/* Status dot */}
                      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
                      <p className="text-sm font-medium text-slate-700">{cfg.label}</p>
                    </div>
                    <p className="text-[10px] text-slate-400 mt-0.5">{timeAgo(call.timestamp)}</p>
                  </div>
                </div>

                <div className="flex items-center gap-1 text-slate-400 opacity-70 group-hover:opacity-100 transition-opacity">
                  <Clock size={10} />
                  <span className="text-[10px] font-mono font-medium">{formatDuration(call.durationSeconds)}</span>
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
