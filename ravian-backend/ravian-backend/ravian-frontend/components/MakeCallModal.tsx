'use client';

import React, { useState, useEffect } from 'react';
import apiClient from '@/lib/api';
import type { Lead } from '@/types/leads';
import type { CallLogCreate } from '@/types/calls';
import { X, Loader2, Phone } from 'lucide-react';

interface MakeCallModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  initialLeadId?: string | null;
}

export default function MakeCallModal({ isOpen, onClose, onSuccess, initialLeadId }: MakeCallModalProps) {
  const [loading, setLoading] = useState(false);
  const [leadsLoading, setLeadsLoading] = useState(false);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<CallLogCreate>({
    lead_id: initialLeadId || '',
    call_direction: 'outbound',
    duration: undefined,
    phone_number: '',
    transcript: '',
    summary: '',
    sentiment: 'neutral',
    outcome: 'connected',
    notes: '',
    follow_up_required: false,
  });

  useEffect(() => {
    if (initialLeadId) {
      setForm(prev => ({ ...prev, lead_id: initialLeadId }));
    }
  }, [initialLeadId, isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    setLeadsLoading(true);
    apiClient
      .get<{ data: Lead[] }>('/api/v1/leads/', { params: { limit: 100 } })
      .then((res) => setLeads(res.data.data ?? []))
      .catch(() => setLeads([]))
      .finally(() => setLeadsLoading(false));
  }, [isOpen]);

  const resetForm = () => {
    setForm({
      lead_id: '',
      call_direction: 'outbound',
      duration: undefined,
      phone_number: '',
      transcript: '',
      summary: '',
      sentiment: 'neutral',
      outcome: 'connected',
      notes: '',
      follow_up_required: false,
    });
    setError(null);
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const selectedLead = leads.find((l) => l.id === form.lead_id);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.lead_id || !form.outcome) {
      setError('Please select a lead and outcome.');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await apiClient.post('/api/v1/calls/', {
        lead_id: form.lead_id,
        call_direction: form.call_direction,
        duration: form.duration ?? 0,
        phone_number: form.phone_number || selectedLead?.phone || undefined,
        transcript: form.transcript || undefined,
        summary: form.summary || undefined,
        sentiment: form.sentiment || undefined,
        outcome: form.outcome,
        notes: form.notes || undefined,
        follow_up_required: form.follow_up_required,
      });
      handleClose();
      onSuccess();
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string } }; message?: string };
      setError(ax?.response?.data?.detail ?? ax?.message ?? 'Failed to log call');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50" onClick={handleClose} aria-hidden="true" />
      <div className="relative bg-white rounded-lg shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Phone className="w-5 h-5" />
            Log a Call
          </h2>
          <button
            type="button"
            onClick={handleClose}
            className="p-1 rounded-lg hover:bg-gray-100 text-gray-500"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-red-50 text-red-700 text-sm">{error}</div>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Lead *</label>
            <select
              value={form.lead_id}
              onChange={(e) => {
                const lead = leads.find((l) => l.id === e.target.value);
                setForm({
                  ...form,
                  lead_id: e.target.value,
                  phone_number: lead?.phone ?? '',
                });
              }}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">Select lead</option>
              {leadsLoading ? (
                <option disabled>Loading...</option>
              ) : (
                leads.map((l) => (
                  <option key={l.id} value={l.id}>
                    {l.name} – {l.phone}
                  </option>
                ))
              )}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Direction</label>
            <select
              value={form.call_direction}
              onChange={(e) => setForm({ ...form, call_direction: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="inbound">Inbound</option>
              <option value="outbound">Outbound</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Duration (seconds)</label>
            <input
              type="number"
              min={0}
              value={form.duration ?? ''}
              onChange={(e) => setForm({ ...form, duration: e.target.value ? parseInt(e.target.value, 10) : undefined })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="120"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Outcome *</label>
            <select
              value={form.outcome}
              onChange={(e) => setForm({ ...form, outcome: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="connected">Connected</option>
              <option value="no_answer">No answer</option>
              <option value="voicemail">Voicemail</option>
              <option value="busy">Busy</option>
              <option value="callback">Callback requested</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Sentiment</label>
            <select
              value={form.sentiment ?? 'neutral'}
              onChange={(e) => setForm({ ...form, sentiment: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="positive">Positive</option>
              <option value="neutral">Neutral</option>
              <option value="negative">Negative</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Summary</label>
            <textarea
              value={form.summary ?? ''}
              onChange={(e) => setForm({ ...form, summary: e.target.value })}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Brief summary of the call"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
            <textarea
              value={form.notes ?? ''}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Additional notes"
            />
          </div>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="follow_up"
              checked={form.follow_up_required ?? false}
              onChange={(e) => setForm({ ...form, follow_up_required: e.target.checked })}
              className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
            />
            <label htmlFor="follow_up" className="text-sm text-gray-700">Follow-up required</label>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={handleClose} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg">
              Cancel
            </button>
            <button type="submit" disabled={loading} className="btn-primary flex items-center gap-2">
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              Log Call
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
