// Leads API types (matches backend /api/v1/leads)

export type LeadSource =
  | 'WEBSITE'
  | 'CHATBOT'
  | 'REFERRAL'
  | 'SOCIAL_MEDIA'
  | 'ADVERTISING'
  | 'EMAIL_CAMPAIGN'
  | 'DIRECT'
  | 'OTHER';

export type LeadStatus =
  | 'NEW'
  | 'CONTACTED'
  | 'QUALIFIED'
  | 'DEMO_SCHEDULED'
  | 'DEMO_COMPLETED'
  | 'ENROLLED'
  | 'LOST'
  | 'NURTURING';

export type LeadUrgency = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface AssignedUser {
  id: string;
  name: string;
  email: string;
}

export interface Lead {
  id: string;
  name: string;
  phone: string;
  email: string | null;
  source: LeadSource | string;
  status: LeadStatus | string;
  intent: string;
  interested_courses: string[];
  urgency: LeadUrgency | string;
  created_at: string;
  updated_at: string;
  assigned_to: AssignedUser | null;
  chatbot_engagement_score: number | null;
  chatbot_context?: { session_id?: string;[key: string]: any };
  last_contact_at: string | null;
  next_action: string | null;
}

export interface LeadCreate {
  name: string;
  phone: string;
  email?: string;
  source: LeadSource;
  intent: string;
  interested_courses: string[];
  urgency: LeadUrgency;
  chatbot_context?: Record<string, unknown>;
  utm_params?: Record<string, string>;
}

export interface LeadUpdate {
  status?: LeadStatus;
  intent?: string;
  urgency?: LeadUrgency;
  assigned_to?: string;
  notes?: string;
}

export interface LeadListResponse {
  data: Lead[];
  pagination: {
    total: number;
    page: number;
    per_page: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
  filters_applied?: {
    status?: string;
    source?: string;
    assigned_to?: string;
    search?: string;
  } | null;
}
