'use client'

import React, { useState, useEffect, useCallback } from 'react'
import apiClient from '@/lib/api'
import { X, Loader2 } from 'lucide-react'

interface Lead {
  id: string
  name: string
  phone?: string
  status?: string
}

interface Course {
  id: string
  name: string
  price?: string
}

interface Props {
  open: boolean
  onClose: () => void
  onSuccess: () => void
}

export default function EnrollStudentModal({ open, onClose, onSuccess }: Props) {
  const [leads, setLeads] = useState<Lead[]>([])
  const [courses, setCourses] = useState<Course[]>([])
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [leadId, setLeadId] = useState('')
  const [courseId, setCourseId] = useState('')
  const [batchId, setBatchId] = useState('')
  const [totalAmount, setTotalAmount] = useState('')
  const [amountPaid, setAmountPaid] = useState('0')
  const [paymentStatus, setPaymentStatus] = useState<'PENDING' | 'PARTIAL' | 'PAID'>('PENDING')

  const fetchOptions = useCallback(async () => {
    setLoading(true)
    try {
      const [leadsRes, coursesRes] = await Promise.all([
        apiClient.get<{ data?: unknown[] }>('/api/v1/leads/'),
        apiClient.get<{ data?: unknown[] }>('/api/v1/teaching/courses')
      ])

      const leadList = Array.isArray(leadsRes.data)
        ? leadsRes.data
        : Array.isArray((leadsRes.data as { data?: unknown[] })?.data)
          ? (leadsRes.data as { data: unknown[] }).data
          : []
      setLeads((leadList as Record<string, unknown>[]).map((l) => ({
        id: String(l.id),
        name: String(l.name ?? ''),
        phone: l.phone ? String(l.phone) : undefined,
        status: l.status ? String(l.status) : undefined,
      })))

      const courseList = Array.isArray(coursesRes.data)
        ? coursesRes.data
        : Array.isArray((coursesRes.data as { data?: unknown[] })?.data)
          ? (coursesRes.data as { data: unknown[] }).data
          : []
      setCourses((courseList as Record<string, unknown>[]).map((c) => ({
        id: String(c.id),
        name: String(c.name ?? ''),
        price: c.price ? String(c.price) : undefined,
      })))
    } catch {
      setError('Failed to load leads or courses')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (open) {
      fetchOptions()
      setError(null)
      setLeadId('')
      setCourseId('')
      setBatchId('')
      setTotalAmount('')
      setAmountPaid('0')
      setPaymentStatus('PENDING')
    }
  }, [open, fetchOptions])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!leadId || !courseId || !batchId || !totalAmount) {
      setError('Please fill all required fields')
      return
    }

    const total = parseFloat(totalAmount)
    const paid = parseFloat(amountPaid || '0')

    if (isNaN(total) || total <= 0) {
      setError('Total amount must be a positive number')
      return
    }
    if (isNaN(paid) || paid < 0) {
      setError('Amount paid must be non-negative')
      return
    }
    if (paid > total) {
      setError('Amount paid cannot exceed total amount')
      return
    }

    setSubmitting(true)
    try {
      await apiClient.post('/api/v1/enrollments/', {
        lead_id: leadId,
        course_id: courseId,
        batch_id: batchId,
        total_amount: total,
        amount_paid: paid,
        payment_status: paymentStatus,
      })
      onSuccess()
      onClose()
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string } }; message?: string }
      setError(ax?.response?.data?.detail ?? ax?.message ?? 'Failed to create enrollment')
    } finally {
      setSubmitting(false)
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Enroll Student</h2>
          <button type="button" onClick={onClose} className="p-1 rounded-lg hover:bg-gray-100 text-gray-500">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">{error}</div>
          )}

          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
            </div>
          ) : (
            <>
              {/* Lead */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Lead *</label>
                <select
                  value={leadId}
                  onChange={(e) => setLeadId(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                >
                  <option value="">Select a lead</option>
                  {leads.map((l) => (
                    <option key={l.id} value={l.id}>
                      {l.name}{l.phone ? ` (${l.phone})` : ''}
                    </option>
                  ))}
                </select>
              </div>

              {/* Course */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Course *</label>
                <select
                  value={courseId}
                  onChange={(e) => {
                    setCourseId(e.target.value)
                    const sel = courses.find((c) => c.id === e.target.value)
                    if (sel?.price) setTotalAmount(sel.price)
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                >
                  <option value="">Select a course</option>
                  {courses.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}{c.price ? ` — ₹${c.price}` : ''}
                    </option>
                  ))}
                </select>
              </div>

              {/* Batch ID */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Batch ID *</label>
                <input
                  type="text"
                  value={batchId}
                  onChange={(e) => setBatchId(e.target.value)}
                  placeholder="Enter batch UUID"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>

              {/* Total Amount */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Total Amount *</label>
                <input
                  type="number"
                  value={totalAmount}
                  onChange={(e) => setTotalAmount(e.target.value)}
                  placeholder="0.00"
                  min="0.01"
                  step="0.01"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>

              {/* Amount Paid */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Amount Paid</label>
                <input
                  type="number"
                  value={amountPaid}
                  onChange={(e) => setAmountPaid(e.target.value)}
                  placeholder="0.00"
                  min="0"
                  step="0.01"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              {/* Payment Status */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Payment Status</label>
                <select
                  value={paymentStatus}
                  onChange={(e) => setPaymentStatus(e.target.value as 'PENDING' | 'PARTIAL' | 'PAID')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="PENDING">Pending</option>
                  <option value="PARTIAL">Partial</option>
                  <option value="PAID">Paid</option>
                </select>
              </div>
            </>
          )}

          {/* Footer */}
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || loading}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting && <Loader2 className="w-4 h-4 animate-spin" />}
              {submitting ? 'Enrolling...' : 'Enroll Student'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
