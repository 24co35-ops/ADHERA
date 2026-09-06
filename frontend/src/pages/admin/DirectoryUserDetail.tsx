import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api, adheraFetch } from '../../lib/api';
import { GlassCard } from '../../components/GlassCard';
import { ToastMessage, ToastContainer } from '../../components/Toast';
import { Modal } from '../../components/Modal';
import {
  ArrowLeft,
  UserCheck,
  Stethoscope,
  Pill,
  Activity,
  MessageSquareWarning,
  UserPlus,
  Shield,
  Download,
  Calendar,
  Clock,
  Mail,
  Phone,
  HeartPulse,
  AlertCircle,
  CheckCircle2,
  XCircle,
  HelpCircle,
  UserX,
  FileSpreadsheet,
} from 'lucide-react';
import {
  DirectoryUserDetail as DirectoryUserDetailType,
  Medicine,
  Feedback,
  AuditLogEntry,
} from '../../types';

type TabType = 'profile' | 'medications' | 'adherence' | 'feedback' | 'assignments' | 'audit';

export const DirectoryUserDetail: React.FC = () => {
  const { userId } = useParams<{ userId: string }>();
  const navigate = useNavigate();

  const [user, setUser] = useState<DirectoryUserDetailType | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabType>('profile');
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  // Tab Data States
  const [medications, setMedications] = useState<Medicine[]>([]);
  const [medsLoading, setMedsLoading] = useState(false);

  const [adherenceRecords, setAdherenceRecords] = useState<any[]>([]);
  const [adherenceTotal, setAdherenceTotal] = useState(0);
  const [adherencePage, setAdherencePage] = useState(1);
  const [adherenceLimit] = useState(15);
  const [adherenceLoading, setAdherenceLoading] = useState(false);

  const [feedbackList, setFeedbackList] = useState<Feedback[]>([]);
  const [feedbackLoading, setFeedbackLoading] = useState(false);

  const [assignmentsList, setAssignmentsList] = useState<any[]>([]);
  const [assignmentsLoading, setAssignmentsLoading] = useState(false);

  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
  const [auditLoading, setAuditLoading] = useState(false);

  // Status Change Modal State
  const [statusModalOpen, setStatusModalOpen] = useState(false);
  const [statusReason, setStatusReason] = useState('');
  const [statusUpdating, setStatusUpdating] = useState(false);

  const addToast = (type: 'success' | 'warning' | 'error' | 'info', message: string) => {
    setToasts((prev) => [...prev, { id: Math.random().toString(36).substring(2, 9), type, message }]);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  // Load Primary User Profile
  const loadUserDetail = useCallback(async () => {
    if (!userId) return;
    try {
      setLoading(true);
      const res = await api.get<DirectoryUserDetailType>(`/admin/directory/${userId}`);
      if (res.success && res.data) {
        setUser(res.data);
      }
    } catch (err: any) {
      addToast('error', err.message || 'Failed to load user profile');
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    loadUserDetail();
  }, [loadUserDetail]);

  // Lazy tab data loaders
  const loadMedications = useCallback(async () => {
    if (!userId) return;
    try {
      setMedsLoading(true);
      const res = await api.get<Medicine[]>(`/admin/directory/${userId}/medicines`);
      if (res.success && res.data) {
        setMedications(res.data);
      }
    } catch (err: any) {
      addToast('error', err.message || 'Failed to load medications');
    } finally {
      setMedsLoading(false);
    }
  }, [userId]);

  const loadAdherence = useCallback(async () => {
    if (!userId) return;
    try {
      setAdherenceLoading(true);
      const res = await api.get<{ items: any[]; total: number }>(
        `/admin/directory/${userId}/adherence?page=${adherencePage}&limit=${adherenceLimit}`
      );
      if (res.success && res.data) {
        setAdherenceRecords(res.data.items || []);
        setAdherenceTotal(res.data.total || 0);
      }
    } catch (err: any) {
      addToast('error', err.message || 'Failed to load adherence records');
    } finally {
      setAdherenceLoading(false);
    }
  }, [userId, adherencePage, adherenceLimit]);

  const loadFeedback = useCallback(async () => {
    if (!userId) return;
    try {
      setFeedbackLoading(true);
      const res = await api.get<Feedback[]>(`/admin/directory/${userId}/feedback`);
      if (res.success && res.data) {
        setFeedbackList(res.data);
      }
    } catch (err: any) {
      addToast('error', err.message || 'Failed to load feedback');
    } finally {
      setFeedbackLoading(false);
    }
  }, [userId]);

  const loadAssignments = useCallback(async () => {
    if (!userId) return;
    try {
      setAssignmentsLoading(true);
      const res = await api.get<any[]>(`/admin/directory/${userId}/assignments`);
      if (res.success && res.data) {
        setAssignmentsList(res.data);
      }
    } catch (err: any) {
      addToast('error', err.message || 'Failed to load assignment history');
    } finally {
      setAssignmentsLoading(false);
    }
  }, [userId]);

  const loadAuditLogs = useCallback(async () => {
    if (!userId) return;
    try {
      setAuditLoading(true);
      const res = await api.get<AuditLogEntry[]>(`/admin/directory/${userId}/audit?limit=50`);
      if (res.success && res.data) {
        setAuditLogs(res.data);
      }
    } catch (err: any) {
      addToast('error', err.message || 'Failed to load audit logs');
    } finally {
      setAuditLoading(false);
    }
  }, [userId]);

  // Trigger data fetch on tab switch
  useEffect(() => {
    if (activeTab === 'medications' && medications.length === 0) loadMedications();
    if (activeTab === 'adherence') loadAdherence();
    if (activeTab === 'feedback' && feedbackList.length === 0) loadFeedback();
    if (activeTab === 'assignments' && assignmentsList.length === 0) loadAssignments();
    if (activeTab === 'audit' && auditLogs.length === 0) loadAuditLogs();
  }, [activeTab, loadMedications, loadAdherence, loadFeedback, loadAssignments, loadAuditLogs, medications.length, feedbackList.length, assignmentsList.length, auditLogs.length]);

  // Status Change Handler
  const handleConfirmStatusChange = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user || !userId) return;
    const trimmedReason = statusReason.trim();
    if (!trimmedReason) {
      addToast('warning', 'Please provide a reason for modifying user status');
      return;
    }

    try {
      setStatusUpdating(true);
      const nextStatus = !user.is_active;
      const res = await api.patch(`/admin/directory/${userId}/status`, {
        is_active: nextStatus,
        reason: trimmedReason,
      });

      if (res.success) {
        addToast('success', `User status changed to ${nextStatus ? 'Active' : 'Suspended'}`);
        setStatusModalOpen(false);
        setStatusReason('');
        loadUserDetail();
      }
    } catch (err: any) {
      addToast('error', err.message || 'Failed to update user status');
    } finally {
      setStatusUpdating(false);
    }
  };

  // CSV Export Handler
  const handleExportCSV = async () => {
    if (!userId) return;
    try {
      const response = await adheraFetch(`/admin/directory/${userId}/adherence/export`);
      if (!response.ok) throw new Error('Failed to export adherence CSV');
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `adherence_${userId}.csv`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);
      addToast('success', 'Adherence history CSV downloaded');
    } catch (err: any) {
      addToast('error', err.message || 'Export failed');
    }
  };

  const formatDate = (isoStr?: string | null) => {
    if (!isoStr) return '—';
    try {
      const d = new Date(isoStr);
      return isNaN(d.getTime()) ? '—' : d.toLocaleString(undefined, { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    } catch {
      return '—';
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-6 animate-pulse">
        <div className="h-6 w-36 bg-white/10 rounded" />
        <div className="h-44 bg-white/5 rounded-3xl" />
        <div className="h-96 bg-white/5 rounded-3xl" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center space-y-4">
        <UserX className="w-16 h-16 mx-auto text-on-surface-variant opacity-40" />
        <h2 className="text-xl font-bold text-white">Identity Not Found</h2>
        <p className="text-sm text-on-surface-variant">The requested user profile does not exist or has been removed.</p>
        <button
          onClick={() => navigate('/admin/directory')}
          className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-primary text-surface font-bold text-xs shadow-glow hover:bg-primary-container"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Return to Directory</span>
        </button>
      </div>
    );
  }

  const isPatient = user.role === 'patient';
  const initials = (user.full_name || 'U')
    .split(' ')
    .map((n) => n[0])
    .join('')
    .substring(0, 2)
    .toUpperCase();

  const tabs: { id: TabType; label: string; icon: React.FC<{ className?: string }> }[] = [
    { id: 'profile', label: 'Profile & Account', icon: Shield },
    { id: 'medications', label: 'Medications', icon: Pill },
    { id: 'adherence', label: 'Adherence History', icon: Activity },
    { id: 'feedback', label: 'Side Effects', icon: MessageSquareWarning },
    { id: 'assignments', label: 'Assignments', icon: UserPlus },
    { id: 'audit', label: 'Audit Trail', icon: FileSpreadsheet },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <ToastContainer toasts={toasts} onDismiss={removeToast} />

      {/* Top Navigation */}
      <button
        onClick={() => navigate('/admin/directory')}
        className="inline-flex items-center space-x-2 text-xs font-semibold text-on-surface-variant hover:text-white transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Identity Directory</span>
      </button>

      {/* Header Profile Summary GlassCard */}
      <GlassCard className="p-6 sm:p-8">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          {/* Identity Info */}
          <div className="flex items-start sm:items-center space-x-4 sm:space-x-5">
            <div
              className={`w-16 h-16 sm:w-20 sm:h-20 rounded-2xl flex items-center justify-center font-extrabold text-xl sm:text-2xl shrink-0 ${
                isPatient
                  ? 'bg-primary/20 text-primary border border-primary/40 shadow-glow'
                  : 'bg-secondary/20 text-secondary border border-secondary/40'
              }`}
            >
              {initials}
            </div>
            <div className="space-y-1.5 min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight truncate">
                  {user.full_name || 'Unnamed User'}
                </h1>
                <span
                  className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${
                    isPatient
                      ? 'bg-primary/10 text-primary border-primary/30'
                      : 'bg-secondary/10 text-secondary border-secondary/30'
                  }`}
                >
                  {isPatient ? <UserCheck className="w-3 h-3" /> : <Stethoscope className="w-3 h-3" />}
                  <span className="capitalize">{user.role}</span>
                </span>
                <span
                  className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${
                    user.is_active
                      ? 'bg-status-success/10 text-status-success border-status-success/30'
                      : 'bg-status-danger/10 text-status-danger border-status-danger/30'
                  }`}
                >
                  <span className={`w-1.5 h-1.5 rounded-full ${user.is_active ? 'bg-status-success' : 'bg-status-danger'}`} />
                  <span>{user.is_active ? 'Active' : 'Suspended'}</span>
                </span>
              </div>

              <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-on-surface-variant">
                <span className="flex items-center gap-1">
                  <Mail className="w-3.5 h-3.5 text-on-surface-variant" />
                  {user.email || 'No email attached'}
                </span>
                {user.contact_number && (
                  <span className="flex items-center gap-1">
                    <Phone className="w-3.5 h-3.5 text-on-surface-variant" />
                    {user.contact_number}
                  </span>
                )}
                <span className="flex items-center gap-1 font-mono text-[11px] text-white/40">
                  ID: {user.id}
                </span>
              </div>
            </div>
          </div>

          {/* Quick Action Button */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                setStatusReason('');
                setStatusModalOpen(true);
              }}
              className={`btn-press px-4 py-2.5 rounded-xl font-bold text-xs border transition-all ${
                user.is_active
                  ? 'bg-status-danger/10 text-status-danger hover:bg-status-danger/20 border-status-danger/30'
                  : 'bg-status-success/10 text-status-success hover:bg-status-success/20 border-status-success/30'
              }`}
            >
              {user.is_active ? 'Suspend Account' : 'Reactivate Account'}
            </button>
          </div>
        </div>

        {/* Highlight Stats Row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mt-6 pt-6 border-t border-white/10 text-xs">
          {isPatient ? (
            <>
              <div className="bg-white/[0.02] p-3 rounded-xl border border-white/5">
                <span className="text-on-surface-variant block text-[11px]">Age / Blood Group</span>
                <span className="font-bold text-white text-sm mt-0.5 block">
                  {user.age ? `${user.age} yrs` : 'N/A'} • {user.blood_group || 'Unknown'}
                </span>
              </div>
              <div className="bg-white/[0.02] p-3 rounded-xl border border-white/5">
                <span className="text-on-surface-variant block text-[11px]">Active Prescriptions</span>
                <span className="font-bold text-primary text-sm mt-0.5 block">
                  {user.active_medicines_count ?? 0} medicines
                </span>
              </div>
              <div className="bg-white/[0.02] p-3 rounded-xl border border-white/5">
                <span className="text-on-surface-variant block text-[11px]">Overall Adherence</span>
                <span className="font-bold text-status-success text-sm mt-0.5 block">
                  {user.overall_adherence_rate ?? 0}%
                </span>
              </div>
              <div className="bg-white/[0.02] p-3 rounded-xl border border-white/5">
                <span className="text-on-surface-variant block text-[11px]">Assigned Doctor</span>
                <span className="font-bold text-white text-sm mt-0.5 block truncate">
                  {user.assigned_provider ? `Dr. ${user.assigned_provider.full_name}` : 'Unassigned'}
                </span>
              </div>
            </>
          ) : (
            <>
              <div className="bg-white/[0.02] p-3 rounded-xl border border-white/5">
                <span className="text-on-surface-variant block text-[11px]">Specialization</span>
                <span className="font-bold text-white text-sm mt-0.5 block">
                  {user.specialization || 'General Practice'}
                </span>
              </div>
              <div className="bg-white/[0.02] p-3 rounded-xl border border-white/5">
                <span className="text-on-surface-variant block text-[11px]">License Number</span>
                <span className="font-bold text-secondary text-sm mt-0.5 block font-mono">
                  {user.license_number || 'N/A'}
                </span>
              </div>
              <div className="bg-white/[0.02] p-3 rounded-xl border border-white/5">
                <span className="text-on-surface-variant block text-[11px]">Assigned Patients</span>
                <span className="font-bold text-primary text-sm mt-0.5 block">
                  {user.assigned_patients?.length ?? 0} active
                </span>
              </div>
              <div className="bg-white/[0.02] p-3 rounded-xl border border-white/5">
                <span className="text-on-surface-variant block text-[11px]">Last Activity</span>
                <span className="font-bold text-white text-sm mt-0.5 block">
                  {formatDate(user.last_activity)}
                </span>
              </div>
            </>
          )}
        </div>
      </GlassCard>

      {/* Tabs Bar */}
      <div className="flex border-b border-white/10 gap-2 overflow-x-auto pb-1 scrollbar-none">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all whitespace-nowrap ${
                isActive
                  ? 'bg-primary/15 text-primary border border-primary/30 shadow-glow'
                  : 'text-on-surface-variant hover:text-white hover:bg-white/5'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* TAB CONTENT: Profile & Account */}
      {activeTab === 'profile' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <GlassCard className="p-6 space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Shield className="w-4 h-4 text-primary" />
              <span>Biographical & Account Info</span>
            </h3>

            <div className="space-y-3 text-xs divide-y divide-white/5">
              <div className="flex justify-between pt-2">
                <span className="text-on-surface-variant">Full Legal Name</span>
                <span className="text-white font-medium">{user.full_name || '—'}</span>
              </div>
              <div className="flex justify-between pt-2">
                <span className="text-on-surface-variant">Email Address</span>
                <span className="text-white font-medium">{user.email || '—'}</span>
              </div>
              <div className="flex justify-between pt-2">
                <span className="text-on-surface-variant">Date of Birth</span>
                <span className="text-white font-medium">{user.date_of_birth || '—'}</span>
              </div>
              <div className="flex justify-between pt-2">
                <span className="text-on-surface-variant">Blood Group</span>
                <span className="text-white font-medium">{user.blood_group || '—'}</span>
              </div>
              <div className="flex justify-between pt-2">
                <span className="text-on-surface-variant">Timezone</span>
                <span className="text-white font-medium">{user.timezone || 'UTC'}</span>
              </div>
              <div className="flex justify-between pt-2">
                <span className="text-on-surface-variant">Registered On</span>
                <span className="text-white font-medium">{formatDate(user.created_at)}</span>
              </div>
              <div className="flex justify-between pt-2">
                <span className="text-on-surface-variant">Last Active</span>
                <span className="text-white font-medium">{formatDate(user.last_activity)}</span>
              </div>
            </div>
          </GlassCard>

          <GlassCard className="p-6 space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <HeartPulse className="w-4 h-4 text-tertiary" />
              <span>Medical & Emergency Records</span>
            </h3>

            <div className="space-y-4 text-xs">
              <div>
                <span className="text-on-surface-variant block mb-1.5 font-medium">Known Allergies</span>
                {user.allergies && user.allergies.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {user.allergies.map((a, i) => (
                      <span key={i} className="px-2.5 py-1 rounded-lg bg-status-danger/10 text-status-danger border border-status-danger/20 font-medium">
                        {a}
                      </span>
                    ))}
                  </div>
                ) : (
                  <span className="text-white/40 italic">No allergies recorded</span>
                )}
              </div>

              <div>
                <span className="text-on-surface-variant block mb-1.5 font-medium">Medical Conditions</span>
                {user.medical_conditions && user.medical_conditions.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {user.medical_conditions.map((c, i) => (
                      <span key={i} className="px-2.5 py-1 rounded-lg bg-white/10 text-white border border-white/10 font-medium">
                        {c}
                      </span>
                    ))}
                  </div>
                ) : (
                  <span className="text-white/40 italic">No medical conditions recorded</span>
                )}
              </div>

              <div>
                <span className="text-on-surface-variant block mb-1.5 font-medium">Emergency Contact</span>
                {user.emergency_contact ? (
                  <div className="p-3 rounded-xl bg-white/[0.03] border border-white/10 space-y-1.5 text-xs">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-white">{user.emergency_contact.full_name || '—'}</span>
                      {user.emergency_contact.is_verified && (
                        <span className="px-1.5 py-0.5 rounded-full bg-status-success/10 text-status-success border border-status-success/30 text-[10px] font-semibold">Verified</span>
                      )}
                    </div>
                    {user.emergency_contact.relationship && (
                      <div className="text-on-surface-variant">Relationship: <span className="text-white">{user.emergency_contact.relationship}</span></div>
                    )}
                    {user.emergency_contact.phone && (
                      <div className="flex items-center gap-1 text-on-surface-variant">
                        <Phone className="w-3 h-3" />
                        <span className="text-white">{user.emergency_contact.phone}</span>
                      </div>
                    )}
                    {user.emergency_contact.email && (
                      <div className="flex items-center gap-1 text-on-surface-variant">
                        <Mail className="w-3 h-3" />
                        <span className="text-white">{user.emergency_contact.email}</span>
                      </div>
                    )}
                  </div>
                ) : (
                  <span className="text-white/40 italic">No emergency contact on file</span>
                )}
              </div>
            </div>
          </GlassCard>
        </div>
      )}

      {/* TAB CONTENT: Medications */}
      {activeTab === 'medications' && (
        <GlassCard className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Pill className="w-4 h-4 text-primary" />
              <span>Prescription & Medication Regimens ({medications.length})</span>
            </h3>
          </div>

          {medsLoading ? (
            <div className="space-y-3 animate-pulse">
              <div className="h-16 bg-white/5 rounded-xl" />
              <div className="h-16 bg-white/5 rounded-xl" />
            </div>
          ) : medications.length === 0 ? (
            <div className="text-center py-10 text-on-surface-variant">
              <Pill className="w-8 h-8 mx-auto mb-2 opacity-30" />
              <p className="text-sm font-semibold text-white">No prescriptions found</p>
              <p className="text-xs text-on-surface-variant mt-1">This user does not have any active or past medications.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {medications.map((m) => (
                <div key={m.id} className="p-4 rounded-xl bg-white/[0.02] border border-white/5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-white text-sm">{m.name}</span>
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                        m.is_active ? 'bg-status-success/10 text-status-success border-status-success/30' : 'bg-white/5 text-white/40 border-white/10'
                      }`}>
                        {m.is_active ? 'Active' : 'Archived'}
                      </span>
                    </div>
                    <div className="text-xs text-on-surface-variant flex flex-wrap gap-x-4 gap-y-1">
                      <span>Dosage: <strong className="text-white">{m.dosage}</strong></span>
                      <span>Frequency: <strong className="text-white">{m.frequency}</strong></span>
                      <span>Route: <strong className="text-white capitalize">{m.route}</strong></span>
                    </div>
                    {m.instructions && (
                      <p className="text-xs text-white/70 italic mt-1">{m.instructions}</p>
                    )}
                  </div>
                  <div className="text-xs text-on-surface-variant text-right shrink-0">
                    <div>Started: {m.start_date || '—'}</div>
                    {m.end_date && <div>Ends: {m.end_date}</div>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </GlassCard>
      )}

      {/* TAB CONTENT: Adherence History */}
      {activeTab === 'adherence' && (
        <GlassCard className="p-6 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-white/10">
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Activity className="w-4 h-4 text-status-success" />
                <span>Adherence Telemetry Log ({adherenceTotal} records)</span>
              </h3>
              <p className="text-xs text-on-surface-variant mt-0.5">Chronological dosage event tracking and adherence compliance.</p>
            </div>

            <button
              onClick={handleExportCSV}
              className="btn-press inline-flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-primary border border-primary/30 text-xs font-semibold self-start sm:self-auto"
            >
              <Download className="w-4 h-4" />
              <span>Export Adherence (CSV)</span>
            </button>
          </div>

          {adherenceLoading ? (
            <div className="space-y-3 animate-pulse">
              <div className="h-12 bg-white/5 rounded-xl" />
              <div className="h-12 bg-white/5 rounded-xl" />
              <div className="h-12 bg-white/5 rounded-xl" />
            </div>
          ) : adherenceRecords.length === 0 ? (
            <div className="text-center py-10 text-on-surface-variant">
              <Activity className="w-8 h-8 mx-auto mb-2 opacity-30" />
              <p className="text-sm font-semibold text-white">No adherence logs</p>
              <p className="text-xs text-on-surface-variant mt-1">No dosage confirmation records have been submitted yet.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-white/10 text-on-surface-variant uppercase text-[10px] tracking-wider">
                    <th className="py-2.5 px-3">Date / Scheduled</th>
                    <th className="py-2.5 px-3">Prescription</th>
                    <th className="py-2.5 px-3">Dose Slot</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3">Logged At</th>
                    <th className="py-2.5 px-3">Notes</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {adherenceRecords.map((r, i) => {
                    const isTaken = r.status === 'taken';
                    const isMissed = r.status === 'missed';
                    return (
                      <tr key={r.id || i} className="hover:bg-white/[0.02]">
                        <td className="py-3 px-3 text-white font-medium whitespace-nowrap">
                          {r.date || formatDate(r.scheduled_time || r.scheduled_utc)}
                        </td>
                        <td className="py-3 px-3 text-white">
                          {r.medicine_name || 'Prescription Dose'}
                        </td>
                        <td className="py-3 px-3 text-on-surface-variant">
                          {r.dose_label || '—'}
                        </td>
                        <td className="py-3 px-3">
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                            isTaken
                              ? 'bg-status-success/10 text-status-success border-status-success/30'
                              : isMissed
                              ? 'bg-status-danger/10 text-status-danger border-status-danger/30'
                              : 'bg-status-warning/10 text-status-warning border-status-warning/30'
                          }`}>
                            {isTaken ? <CheckCircle2 className="w-3 h-3" /> : isMissed ? <XCircle className="w-3 h-3" /> : <HelpCircle className="w-3 h-3 text-status-warning" />}
                            <span className="capitalize">{r.status}</span>
                          </span>
                        </td>
                        <td className="py-3 px-3 text-on-surface-variant whitespace-nowrap">
                          {formatDate(r.logged_at || r.outcome_utc || r.created_at)}
                        </td>
                        <td className="py-3 px-3 text-on-surface-variant max-w-[160px] truncate" title={r.notes || ''}>
                          {r.notes || '—'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>

              {/* Adherence Pagination */}
              {adherenceTotal > adherenceLimit && (
                <div className="flex items-center justify-between pt-4 border-t border-white/10 text-xs text-on-surface-variant">
                  <span>Showing page {adherencePage} of {Math.ceil(adherenceTotal / adherenceLimit)}</span>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setAdherencePage((p) => Math.max(1, p - 1))}
                      disabled={adherencePage <= 1}
                      className="px-3 py-1 rounded bg-white/5 hover:bg-white/10 disabled:opacity-30 text-white"
                    >
                      Prev
                    </button>
                    <button
                      onClick={() => setAdherencePage((p) => p + 1)}
                      disabled={adherencePage >= Math.ceil(adherenceTotal / adherenceLimit)}
                      className="px-3 py-1 rounded bg-white/5 hover:bg-white/10 disabled:opacity-30 text-white"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </GlassCard>
      )}

      {/* TAB CONTENT: Side Effects */}
      {activeTab === 'feedback' && (
        <GlassCard className="p-6">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 mb-4">
            <MessageSquareWarning className="w-4 h-4 text-status-warning" />
            <span>Side Effect Reports & Feedback ({feedbackList.length})</span>
          </h3>

          {feedbackLoading ? (
            <div className="space-y-3 animate-pulse">
              <div className="h-16 bg-white/5 rounded-xl" />
              <div className="h-16 bg-white/5 rounded-xl" />
            </div>
          ) : feedbackList.length === 0 ? (
            <div className="text-center py-10 text-on-surface-variant">
              <MessageSquareWarning className="w-8 h-8 mx-auto mb-2 opacity-30" />
              <p className="text-sm font-semibold text-white">No adverse reactions reported</p>
              <p className="text-xs text-on-surface-variant mt-1">This user has not filed any side-effect feedback.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {feedbackList.map((f) => {
                const severityColors: Record<number, string> = {
                  1: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
                  2: 'bg-status-warning/10 text-status-warning border-status-warning/30',
                  3: 'bg-orange-500/10 text-orange-400 border-orange-500/30',
                  4: 'bg-status-danger/10 text-status-danger border-status-danger/30 font-bold',
                };
                return (
                  <div key={f.id} className="p-4 rounded-xl bg-white/[0.02] border border-white/5 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className={`px-2.5 py-0.5 rounded-full text-[11px] border ${severityColors[f.severity] || severityColors[1]}`}>
                        Severity Grade {f.severity}
                      </span>
                      <span className="text-xs text-on-surface-variant">{formatDate(f.created_at)}</span>
                    </div>
                    <p className="text-xs sm:text-sm text-white">{f.description}</p>
                    {f.medicines?.name && (
                      <span className="text-[11px] text-primary block">Related Medicine: {f.medicines.name}</span>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </GlassCard>
      )}

      {/* TAB CONTENT: Assignments */}
      {activeTab === 'assignments' && (
        <GlassCard className="p-6">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 mb-4">
            <UserPlus className="w-4 h-4 text-secondary" />
            <span>Care Provider Assignment History ({assignmentsList.length})</span>
          </h3>

          {assignmentsLoading ? (
            <div className="space-y-3 animate-pulse">
              <div className="h-16 bg-white/5 rounded-xl" />
            </div>
          ) : assignmentsList.length === 0 ? (
            <div className="text-center py-10 text-on-surface-variant">
              <UserPlus className="w-8 h-8 mx-auto mb-2 opacity-30" />
              <p className="text-sm font-semibold text-white">No assignment records</p>
              <p className="text-xs text-on-surface-variant mt-1">No doctor-patient relationships recorded for this profile.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {assignmentsList.map((a) => (
                <div key={a.id} className="p-4 rounded-xl bg-white/[0.02] border border-white/5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-white">
                        Patient: {a.patient_name || 'Patient'} ➔ Provider: Dr. {a.provider_name || 'Provider'}
                      </span>
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-white/10 text-white uppercase">
                        {a.status}
                      </span>
                    </div>
                    <div className="text-on-surface-variant">
                      Initiated by: <strong className="text-white/80">{a.assigned_by ? 'Administrator' : 'Direct Request'}</strong>
                    </div>
                  </div>
                  <div className="text-on-surface-variant text-right">
                    {formatDate(a.assigned_on || a.created_at)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </GlassCard>
      )}

      {/* TAB CONTENT: Audit Trail */}
      {activeTab === 'audit' && (
        <GlassCard className="p-6">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 mb-4">
            <FileSpreadsheet className="w-4 h-4 text-primary" />
            <span>Identity Security Audit Trail ({auditLogs.length} events)</span>
          </h3>

          {auditLoading ? (
            <div className="space-y-3 animate-pulse">
              <div className="h-12 bg-white/5 rounded-xl" />
              <div className="h-12 bg-white/5 rounded-xl" />
            </div>
          ) : auditLogs.length === 0 ? (
            <div className="text-center py-10 text-on-surface-variant">
              <Shield className="w-8 h-8 mx-auto mb-2 opacity-30" />
              <p className="text-sm font-semibold text-white">No audit records found</p>
              <p className="text-xs text-on-surface-variant mt-1">No administrative or user actions have been logged for this identity.</p>
            </div>
          ) : (
            <div className="space-y-2.5">
              {auditLogs.map((log) => (
                <div key={log.id} className="p-3 rounded-xl bg-white/[0.02] border border-white/5 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                  <div>
                    <span className="font-mono font-bold text-primary mr-2">[{log.action_code}]</span>
                    {log.details && (
                      <span className="text-on-surface-variant font-mono text-[11px]">
                        {JSON.stringify(log.details)}
                      </span>
                    )}
                  </div>
                  <div className="text-on-surface-variant text-right shrink-0">
                    {formatDate(log.created_at)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </GlassCard>
      )}

      {/* Modal: Status Modification with Mandatory Reason */}
      <Modal
        isOpen={statusModalOpen}
        onClose={() => setStatusModalOpen(false)}
        title={user.is_active ? 'Confirm Account Suspension' : 'Confirm Account Reactivation'}
        maxWidth="md"
      >
        <form onSubmit={handleConfirmStatusChange} className="space-y-4">
          <div className="p-3 rounded-xl bg-status-warning/10 border border-status-warning/20 text-xs text-status-warning flex items-start gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>
              {user.is_active
                ? 'Suspending this account will immediately revoke all access tokens and prevent the user from logging in or using the app.'
                : 'Reactivating this account will allow the user to log in and resume adherence tracking.'}
            </span>
          </div>

          <div>
            <label className="block text-xs font-semibold text-white mb-1">
              Administrative Reason <span className="text-status-danger">*</span>
            </label>
            <textarea
              required
              rows={3}
              value={statusReason}
              onChange={(e) => setStatusReason(e.target.value)}
              placeholder="e.g., Requested by patient, credential verification audit, security hold..."
              className="w-full px-3.5 py-2.5 bg-black/40 border border-white/10 rounded-xl text-xs sm:text-sm text-white placeholder-on-surface-variant focus:outline-none focus:border-primary/50 transition-colors"
            />
          </div>

          <div className="flex justify-end gap-3 pt-2 border-t border-white/10">
            <button
              type="button"
              onClick={() => setStatusModalOpen(false)}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-on-surface-variant hover:text-white hover:bg-white/5 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={statusUpdating || !statusReason.trim()}
              className={`btn-press px-4 py-2 rounded-xl text-xs font-bold text-white disabled:opacity-40 transition-colors ${
                user.is_active ? 'bg-status-danger hover:bg-status-danger/80' : 'bg-status-success hover:bg-status-success/80'
              }`}
            >
              {statusUpdating ? 'Updating...' : user.is_active ? 'Confirm Suspension' : 'Confirm Reactivation'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
export default DirectoryUserDetail;
