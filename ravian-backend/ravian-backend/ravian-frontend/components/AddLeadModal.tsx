'use client';

import React, { useState } from 'react';
import type { LeadCreate, LeadSource, LeadUrgency } from '@/types/leads';
import { X, Loader2 } from 'lucide-react';

const SOURCE_OPTIONS: LeadSource[] = [
  'WEBSITE',
  'CHATBOT',
  'REFERRAL',
  'SOCIAL_MEDIA',
  'ADVERTISING',
  'EMAIL_CAMPAIGN',
  'DIRECT',
  'OTHER',
];

const URGENCY_OPTIONS: LeadUrgency[] = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];

interface AddLeadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export default function AddLeadModal({ isOpen, onClose, onSuccess }: AddLeadModalProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<LeadCreate>({
    name: '',
    phone: '',
    email: '',
    source: 'WEBSITE',
    intent: '',
    interested_courses: [''],
    urgency: 'MEDIUM',
  });

  const resetForm = () => {
    setForm({
      name: '',
      phone: '',
      email: '',
      source: 'WEBSITE',
      intent: '',
      interested_courses: [''],
      urgency: 'MEDIUM',
    });
    setError(null);
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const updateCourse = (index: number, value: string) => {
    const next = [...form.interested_courses];
    next[index] = value;
    setForm({ ...form, interested_courses: next });
  };

  const addCourse = () => {
    setForm({ ...form, interested_courses: [...form.interested_courses, ''] });
  };

  const removeCourse = (index: number) => {
    if (form.interested_courses.length <= 1) return;
    const next = form.interested_courses.filter((_, i) => i !== index);
    setForm({ ...form, interested_courses: next });
  };

  const validate = (): string | null => {
    if (!form.name.trim()) return 'Name is required.';
    if (!form.phone.trim()) return 'Phone is required.';
    const cleaned = form.phone.replace(/[\s\-\.\(\)]/g, '');
    if (!/^\+?\d{10,15}$/.test(cleaned)) return 'Invalid phone number format.';
    if (!form.intent.trim()) return 'Intent is required.';
    const courses = form.interested_courses.filter((c) => c.trim());
    if (courses.length === 0) return 'At least one course interest is required.';
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const { default: apiClient } = await import('@/lib/api');
      const payload: LeadCreate = {
        ...form,
        email: form.email?.trim() || undefined,
        interested_courses: form.interested_courses.filter((c) => c.trim()),
      };
      await apiClient.post('/api/v1/leads/', payload);
      handleClose();
      onSuccess();
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string } }; message?: string };
      setError(ax?.response?.data?.detail ?? ax?.message ?? 'Failed to create lead');
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
          <h2 className="text-lg font-semibold text-gray-900">Add New Lead</h2>
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
            <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Full name"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Phone *</label>
            <input
              type="tel"
              value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="+1-555-123-4567"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              value={form.email ?? ''}
              onChange={(e) => setForm({ ...form, email: e.target.value || undefined })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="email@example.com"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Source *</label>
            <select
              value={form.source}
              onChange={(e) => setForm({ ...form, source: e.target.value as LeadSource })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              {SOURCE_OPTIONS.map((s) => (
                <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Intent / Interest *</label>
            <input
              type="text"
              value={form.intent}
              onChange={(e) => setForm({ ...form, intent: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="e.g. Interested in data science bootcamp"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Course interest(s) *</label>
            {form.interested_courses.map((course, i) => (
              <div key={i} className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={course}
                  onChange={(e) => updateCourse(i, e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder="Course name"
                />
                <button
                  type="button"
                  onClick={() => removeCourse(i)}
                  className="px-2 py-1 text-gray-500 hover:bg-gray-100 rounded"
                  disabled={form.interested_courses.length <= 1}
                >
                  Remove
                </button>
              </div>
            ))}
            <button type="button" onClick={addCourse} className="text-sm text-indigo-600 hover:underline">
              + Add another course
            </button>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Urgency *</label>
            <select
              value={form.urgency}
              onChange={(e) => setForm({ ...form, urgency: e.target.value as LeadUrgency })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              {URGENCY_OPTIONS.map((u) => (
                <option key={u} value={u}>{u}</option>
              ))}
            </select>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={handleClose} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg">
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="btn-primary flex items-center gap-2"
            >
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              Add Lead
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
