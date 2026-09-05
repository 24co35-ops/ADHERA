export type UserRole = 'patient' | 'provider' | 'admin';

export interface User {
  id: string;
  email: string;
  role: UserRole;
  full_name?: string;
  timezone?: string;
  is_active?: boolean;
}

export interface Profile {
  id: string;
  role: UserRole;
  full_name: string;
  email?: string;
  date_of_birth?: string | null;
  blood_group?: string | null;
  allergies?: string[] | null;
  medical_conditions?: string[] | null;
  emergency_contacts?: EmergencyContact[] | null;
  license_number?: string | null;
  specialization?: string | null;
  timezone: string;
  is_active: boolean;
  created_at?: string;
  age?: number | null;
}

export interface EmergencyContact {
  name: string;
  phone: string;
  email?: string;
  relationship?: string;
}

export interface Medicine {
  id: string;
  user_id: string;
  name: string;
  dosage: string;
  route: 'oral' | 'injection' | 'topical' | 'inhalation' | 'drops' | 'other';
  frequency: string;
  start_date: string;
  end_date?: string | null;
  instructions?: string | null;
  is_active: boolean;
  created_at?: string;
  reminders?: Reminder[];
}

export interface Reminder {
  id: string;
  medicine_id: string;
  user_id: string;
  dose_label: string;
  dose_time_utc: string;
  recurrence_type: 'daily' | 'weekday' | 'alternate' | 'prn';
  recurrence_params?: number[];
  advance_notification_minutes: number;
  is_active: boolean;
  medicines?: Medicine;
}

export interface UpcomingDose {
  id: string;
  scheduled_utc: string;
  status: 'pending' | 'taken' | 'missed';
  reminders: Reminder;
}

export interface AdherenceLog {
  id: string;
  user_id: string;
  reminder_id: string;
  scheduled_utc: string;
  status: 'taken' | 'missed' | 'skipped';
  outcome_utc?: string;
  correction_note?: string;
  reminders?: Reminder;
}

export interface Feedback {
  id: string;
  user_id: string;
  medicine_id: string;
  severity: 1 | 2 | 3 | 4;
  description: string;
  occurred_at?: string;
  created_at: string;
  medicines?: {
    name: string;
  };
}

export interface PatientFlag {
  id: string;
  user_id: string;
  flag_type: 'dose_drift' | 'weekend_drop' | 'side_effect_drop' | 'silent_inactivity';
  severity: 'low' | 'moderate' | 'high' | 'critical';
  details: Record<string, any>;
  created_at: string;
  resolved_at?: string | null;
}

export interface Assignment {
  id: string;
  patient_id: string;
  provider_id: string;
  status: 'active' | 'pending' | 'rejected' | 'cancelled';
  assigned_on: string;
  profiles?: Profile;
  patient?: Profile;
  provider?: Profile;
}

export interface MyProviderResponse {
  assigned: boolean;
  data: Assignment | null;
}

export interface DashboardStats {
  weekly_adherence: number;
  monthly_adherence: number;
  weekly_warning: boolean;
  weekly_percentage: number;
  streak: number;
  missed_this_month: number;
  today_taken: number;
  today_total: number;
  overall_adherence_percentage?: number;
  active_patients_count?: number;
  doses_taken_today?: number;
  doses_missed_today?: number;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  error?: {
    code: string;
    message: string;
    field?: string;
  };
}
