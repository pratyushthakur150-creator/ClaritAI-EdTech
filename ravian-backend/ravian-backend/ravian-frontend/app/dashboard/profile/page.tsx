'use client';

import { useState, useEffect } from 'react';
import { User, Mail, Shield, Building2, Clock, Calendar, Edit3, Save, X } from 'lucide-react';
import { toast } from 'sonner';
import apiClient from '@/lib/api';

interface UserProfile {
  user_id: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  role: string;
  tenant_id: string;
  tenant_name: string | null;
  is_active: boolean;
  last_login: string | null;
  created_at: string | null;
}

export default function ProfilePage() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      const { data } = await apiClient.get('/api/v1/auth/me');
      setProfile(data);
      setFirstName(data.first_name || '');
      setLastName(data.last_name || '');
    } catch (err) {
      console.error('Failed to fetch profile:', err);
      // Fallback: try localStorage
      try {
        const stored = localStorage.getItem('user');
        if (stored) {
          const user = JSON.parse(stored);
          setProfile({
            user_id: user.user_id || user.id || '',
            email: user.email || '',
            first_name: user.first_name || null,
            last_name: user.last_name || null,
            role: user.role || 'VIEWER',
            tenant_id: user.tenant_id || '',
            tenant_name: null,
            is_active: true,
            last_login: null,
            created_at: null,
          });
          setFirstName(user.first_name || '');
          setLastName(user.last_name || '');
        }
      } catch {}
    } finally {
      setLoading(false);
    }
  };

  const getRoleBadge = (role: string) => {
    switch (role?.toUpperCase()) {
      case 'ADMIN':
        return <span className="badge badge-brand">Administrator</span>;
      case 'MENTOR':
        return <span className="badge badge-success">Mentor</span>;
      case 'VIEWER':
        return <span className="badge badge-neutral">Viewer</span>;
      default:
        return <span className="badge badge-neutral">{role}</span>;
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Never';
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  const getInitials = () => {
    const f = profile?.first_name?.[0] || '';
    const l = profile?.last_name?.[0] || '';
    return (f + l).toUpperCase() || 'U';
  };

  if (loading) {
    return (
      <div className="p-6 max-w-4xl space-y-6">
        <div className="animate-fade-in-up">
          <div className="skeleton h-8 w-48 mb-2"></div>
          <div className="skeleton skeleton-text w-64"></div>
        </div>
        <div className="card">
          <div className="card-body space-y-6">
            <div className="flex items-center gap-6">
              <div className="skeleton skeleton-circle w-20 h-20"></div>
              <div className="space-y-2 flex-1">
                <div className="skeleton h-6 w-40"></div>
                <div className="skeleton skeleton-text w-56"></div>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[1, 2, 3, 4].map(i => (
                <div key={i} className="skeleton h-16 rounded-xl"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="p-6 max-w-4xl">
        <div className="card">
          <div className="card-body text-center py-12">
            <User className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <h2 className="text-lg font-semibold text-slate-700">Could not load profile</h2>
            <p className="text-sm text-slate-400 mt-1">Please try refreshing the page.</p>
            <button onClick={fetchProfile} className="btn-primary mt-4 mx-auto">
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl space-y-6">
      {/* Header */}
      <div className="animate-fade-in-up">
        <h1 className="text-2xl font-bold text-slate-900">My Profile</h1>
        <p className="text-slate-500 mt-0.5">View and manage your account information</p>
      </div>

      {/* Profile Card */}
      <div className="card animate-fade-in-up" style={{ animationDelay: '0.05s' }}>
        <div className="card-body">
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6">
            {/* Avatar */}
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center shadow-lg shadow-brand-500/20">
              <span className="text-white text-2xl font-bold">{getInitials()}</span>
            </div>

            {/* Name & Role */}
            <div className="flex-1">
              <h2 className="text-xl font-bold text-slate-900">
                {profile.first_name || ''} {profile.last_name || ''}
                {!profile.first_name && !profile.last_name && (
                  <span className="text-slate-400">No name set</span>
                )}
              </h2>
              <p className="text-slate-500 mt-0.5">{profile.email}</p>
              <div className="mt-2 flex items-center gap-2">
                {getRoleBadge(profile.role)}
                {profile.is_active ? (
                  <span className="badge badge-success">Active</span>
                ) : (
                  <span className="badge badge-danger">Inactive</span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Details Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
        {/* Email */}
        <div className="card">
          <div className="card-body">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center">
                <Mail className="w-5 h-5 text-blue-600" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Email Address</p>
                <p className="text-sm font-medium text-slate-900 mt-0.5 truncate">{profile.email}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Role */}
        <div className="card">
          <div className="card-body">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-50 flex items-center justify-center">
                <Shield className="w-5 h-5 text-indigo-600" />
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Role</p>
                <p className="text-sm font-medium text-slate-900 mt-0.5 capitalize">{profile.role?.toLowerCase()}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Organization */}
        <div className="card">
          <div className="card-body">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-50 flex items-center justify-center">
                <Building2 className="w-5 h-5 text-emerald-600" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Organization</p>
                <p className="text-sm font-medium text-slate-900 mt-0.5 truncate">
                  {profile.tenant_name || 'Default Organization'}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Last Login */}
        <div className="card">
          <div className="card-body">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-amber-50 flex items-center justify-center">
                <Clock className="w-5 h-5 text-amber-600" />
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Last Login</p>
                <p className="text-sm font-medium text-slate-900 mt-0.5">{formatDate(profile.last_login)}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Account Info */}
      <div className="card animate-fade-in-up" style={{ animationDelay: '0.15s' }}>
        <div className="card-header">
          <h2 className="text-base font-semibold text-slate-900">Account Information</h2>
        </div>
        <div className="card-body">
          <div className="space-y-4">
            <div className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0">
              <div className="flex items-center gap-2 text-sm text-slate-500">
                <Calendar className="w-4 h-4" />
                Account Created
              </div>
              <span className="text-sm font-medium text-slate-900">{formatDate(profile.created_at)}</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0">
              <div className="flex items-center gap-2 text-sm text-slate-500">
                <Shield className="w-4 h-4" />
                Tenant ID
              </div>
              <code className="text-xs text-slate-500 bg-slate-50 px-2 py-1 rounded-lg font-mono">{profile.tenant_id}</code>
            </div>
            <div className="flex items-center justify-between py-2">
              <div className="flex items-center gap-2 text-sm text-slate-500">
                <User className="w-4 h-4" />
                User ID
              </div>
              <code className="text-xs text-slate-500 bg-slate-50 px-2 py-1 rounded-lg font-mono">{profile.user_id}</code>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
