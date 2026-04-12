'use client'

import { useState, useEffect } from 'react'
import { X, Loader2 } from 'lucide-react'
import apiClient from '@/lib/api'
import type { Lead } from '@/types/lead'

interface LogCallModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

export default function LogCallModal({ isOpen, onClose, onSuccess }: LogCallModalProps) {
  const [loading, setLoading] = useState(false)
  const [leadsLoading, setLeadsLoading] = useState(false)
  const [leads, setLeads] = useState<Lead[]>([])
  const [error, setError] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    lead_id: '',
    contact_name: '',
    phone: '',
    duration: 0,
    status: 'completed' as 'completed' | 'missed' | 'scheduled',
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
    if (!formData.lead_id) {
      setError('Please select a contact.')
      return
    }
    setError(null)
    setLoading(true)
    try {
      await apiClient.post('/api/v1/calls/', {
        lead_id: formData.lead_id,
        duration: formData.duration || 0,
        outcome: formData.status === 'completed' ? 'CONNECTED' : formData.status === 'missed' ? 'NO_ANSWER' : 'SCHEDULED_CALLBACK',
        notes: formData.notes || undefined,
        call_direction: 'OUTBOUND',
        sentiment: 'NEUTRAL'
      })
      setFormData({ lead_id: '', contact_name: '', phone: '', duration: 0, status: 'completed', notes: '' })
      onSuccess()
      onClose()
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string } }; message?: string }
      setError(ax?.response?.data?.detail ?? ax?.message ?? 'Failed to log call')
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    setFormData({ lead_id: '', contact_name: '', phone: '', duration: 0, status: 'completed', notes: '' })
    setError(null)
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-6 w-full max-w-md shadow-xl">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-gray-900">Log New Call</h2>
          <button type="button" onClick={handleClose} className="p-1 rounded hover:bg-gray-100" aria-label="Close">
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-red-50 text-red-700 text-sm">{error}</div>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Contact *</label>
            <select
              value={formData.lead_id}
              onChange={e => {
                const lead = leads.find(l => l.id === e.target.value)
                setFormData({
                  ...formData,
                  lead_id: e.target.value,
                  contact_name: lead?.name ?? '',
                  phone: lead?.phone ?? ''
                })
              }}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Select contact</option>
              {leadsLoading ? (
                <option disabled>Loading...</option>
              ) : (
                leads.map(l => (
                  <option key={l.id} value={l.id}>{l.name} – {l.phone ?? l.email}</option>
                ))
              )}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Duration (seconds)</label>
            <input
              type="number"
              min={0}
              value={formData.duration || ''}
              onChange={e => setFormData({ ...formData, duration: parseInt(e.target.value, 10) || 0 })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="120"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select
              value={formData.status}
              onChange={e => setFormData({ ...formData, status: e.target.value as 'completed' | 'missed' | 'scheduled' })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="completed">Completed</option>
              <option value="missed">Missed</option>
              <option value="scheduled">Scheduled</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
            <textarea
              value={formData.notes}
              onChange={e => setFormData({ ...formData, notes: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
              rows={3}
              placeholder="Call notes..."
            />
          </div>
          <div className="flex gap-2 pt-2">
            <button type="button" onClick={handleClose} className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
              Cancel
            </button>
            <button type="submit" disabled={loading} className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2">
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              Log Call
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

