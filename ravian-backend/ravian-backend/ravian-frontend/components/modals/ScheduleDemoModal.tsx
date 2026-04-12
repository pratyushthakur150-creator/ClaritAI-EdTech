'use client'

import { useState, useEffect } from 'react'
import { X, Loader2, Calendar, Video, ExternalLink } from 'lucide-react'
import apiClient from '@/lib/api'
import type { Lead } from '@/types/lead'

interface ScheduleDemoModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

interface DemoResult {
  meeting_link?: string
  google_event_id?: string
  scheduled_at?: string
}

export default function ScheduleDemoModal({ isOpen, onClose, onSuccess }: ScheduleDemoModalProps) {
  const [loading, setLoading] = useState(false)
  const [leadsLoading, setLeadsLoading] = useState(false)
  const [leads, setLeads] = useState<Lead[]>([])
  const [error, setError] = useState<string | null>(null)
  const [demoResult, setDemoResult] = useState<DemoResult | null>(null)
  const [formData, setFormData] = useState({
    lead_id: '',
    scheduled_at: '',
    notes: ''
  })

  useEffect(() => {
    if (!isOpen) return
    setLeadsLoading(true)
    apiClient.get<{ data: unknown[] }>('/api/v1/leads/', { params: { limit: 100 } })
      .then((res) => {
        const data = res.data.data ?? []
        setLeads((data as Record<string, unknown>[]).map((l) => ({
          id: String(l.id),
          name: String(l.name ?? ''),
          email: String(l.email ?? ''),
          phone: l.phone ? String(l.phone) : undefined,
          created_at: String(l.created_at ?? ''),
          updated_at: String(l.updated_at ?? ''),
          status: (l.status as Lead['status']) ?? 'new'
        })))
      })
      .catch(() => setLeads([]))
      .finally(() => setLeadsLoading(false))
  }, [isOpen])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.lead_id || !formData.scheduled_at) {
      setError('Please select a lead and date/time.')
      return
    }
    setError(null)
    setLoading(true)
    try {
      const res = await apiClient.post('/api/v1/demos/', {
        lead_id: formData.lead_id,
        scheduled_at: formData.scheduled_at,
        notes: formData.notes || undefined
      })
      const result = res.data as DemoResult
      setDemoResult(result)
      onSuccess()
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string } }; message?: string }
      setError(ax?.response?.data?.detail ?? ax?.message ?? 'Failed to schedule demo')
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    setFormData({ lead_id: '', scheduled_at: '', notes: '' })
    setError(null)
    setDemoResult(null)
    onClose()
  }

  if (!isOpen) return null

  // ── Success screen with Google Meet link ──
  if (demoResult) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg p-6 w-full max-w-md shadow-xl">
          <div className="text-center mb-4">
            <div className="w-14 h-14 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <Calendar className="w-7 h-7 text-green-600" />
            </div>
            <h2 className="text-xl font-bold text-gray-900">Demo Scheduled!</h2>
            <p className="text-sm text-gray-500 mt-1">
              {demoResult.scheduled_at
                ? new Date(demoResult.scheduled_at).toLocaleString()
                : 'Scheduled successfully'}
            </p>
          </div>

          {/* Google Meet link */}
          {demoResult.meeting_link && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
              <div className="flex items-center gap-2 mb-2">
                <Video className="w-5 h-5 text-blue-600" />
                <span className="text-sm font-semibold text-blue-800">Google Meet Link</span>
              </div>
              <a
                href={demoResult.meeting_link}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-700 text-sm font-medium break-all"
              >
                {demoResult.meeting_link}
                <ExternalLink className="w-3 h-3 flex-shrink-0" />
              </a>
            </div>
          )}

          {/* Google Calendar event created */}
          {demoResult.google_event_id && (
            <p className="text-xs text-gray-400 text-center mb-4">
              📅 Google Calendar event created
            </p>
          )}

          <button
            type="button"
            onClick={handleClose}
            className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 font-medium"
          >
            Done
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-6 w-full max-w-md shadow-xl">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-gray-900">Schedule Demo</h2>
          <button type="button" onClick={handleClose} className="p-1 rounded hover:bg-gray-100" aria-label="Close">
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-red-50 text-red-700 text-sm">{error}</div>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Lead *</label>
            <select
              value={formData.lead_id}
              onChange={e => setFormData({ ...formData, lead_id: e.target.value })}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Select lead</option>
              {leadsLoading ? (
                <option disabled>Loading...</option>
              ) : (
                leads.map(l => (
                  <option key={l.id} value={l.id}>{l.name} – {l.email}</option>
                ))
              )}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Date & Time *</label>
            <input
              type="datetime-local"
              value={formData.scheduled_at}
              onChange={e => setFormData({ ...formData, scheduled_at: e.target.value })}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
            <textarea
              value={formData.notes}
              onChange={e => setFormData({ ...formData, notes: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
              rows={3}
              placeholder="Agenda or notes..."
            />
          </div>
          <div className="flex gap-2 pt-2">
            <button type="button" onClick={handleClose} className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
              Cancel
            </button>
            <button type="submit" disabled={loading} className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2">
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              Schedule Demo
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
