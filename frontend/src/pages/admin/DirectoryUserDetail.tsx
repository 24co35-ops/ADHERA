import React, { useState, useEffect, useCallback, useMemo } from 'react';
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
  AlertTriangle,
  CheckCircle2,
  XCircle,
  HelpCircle,
  UserX,
  FileSpreadsheet,
  Copy,
  Check,
  RefreshCw,
  Info,
  TrendingUp,
  ExternalLink,
  Droplets,
  Globe,
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
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<TabType>('profile');
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const [copiedId, setCopiedId] = useState(false);

  // Tab Data States
  const [medications, setMedications] = useState<Medicine[]>([]);
  const [medsLoading, setMedsLoading] = useState(false);

  const [adherenceRecords, setAdherenceRecords] = useState<any[]>([]);
  const [adherenceTotal, setAdherenceTotal] = useState(0);
  const [adherencePage, setAdherencePage] = useState(1);
  const [adherenceStatusFilter, setAdherenceStatusFilter] = useState('');
  const [adherenceLimit] = useState(15);
  const [adherenceLoading, setAdherenceLoading] = useState(false);
  const [exportingCSV, setExportingCSV] = useState(false);

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

  const handleCopyId = () => {
    if (!user?.id) return;
    navigator.clipboard.writeText(user.id);
    setCopiedId(true);
    addToast('info', 'User ID copied to clipboard');
    setTimeout(() => setCopiedId(false), 2000);
  };

  // Load Primary User Profile
  const loadUserDetail = useCallback(async (isSilent = false) => {
    if (!userId) return;
    try {
      if (!isSilent) setLoading(true);
      const res = await api.get<DirectoryUserDetailType>(`/admin/directory/${userId}`);
      if (res.success && res.data) {
        setUser(res.data);
      }
    } catch (err: any) {
      addToast('error', err.message || 'Failed to load user profile');
    } finally {
      if (!isSilent) setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    loadUserDetail();
  }, [loadUserDetail]);

  // Tab data loaders
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
      const filterParam = adherenceStatusFilter ? `&status=${encodeURIComponent(adherenceStatusFilter)}` : '';
      const res = await api.get<{ items: any[]; total: number }>(
        `/admin/directory/${userId}/adherence?page=${adherencePage}&limit=${adherenceLimit}${filterParam}`
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
  }, [userId, adherencePage, adherenceLimit, adherenceStatusFilter]);

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

  // Trigger data fetch on tab switch or filter changes
  useEffect(() => {
    if (activeTab === 'medications') loadMedications();
    if (activeTab === 'adherence') loadAdherence();
    if (activeTab === 'feedback') loadFeedback();
    if (activeTab === 'assignments') loadAssignments();
    if (activeTab === 'audit') loadAuditLogs();
  }, [activeTab, loadMedications, loadAdherence, loadFeedback, loadAssignments, loadAuditLogs]);

  const handleRefreshAll = async () => {
    setRefreshing(true);
    await Promise.all([
      loadUserDetail(true),
      loadMedications(),
      loadAdherence(),
      loadFeedback(),
      loadAssignments(),
      loadAuditLogs(),
    ]);
    setRefreshing(false);
    addToast('success', 'User intelligence and telemetry refreshed');
  };

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
        loadUserDetail(true);
        loadAuditLogs();
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
      setExportingCSV(true);
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
    } finally {
      setExportingCSV(false);
    }
  };

  const formatDate = (isoStr?: string | null) => {
    if (!isoStr) return '—';
    try {
      const d = new Date(isoStr);
      return isNaN(d.getTime())
        ? '—'
        : d.toLocaleString(undefined, {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
          });
    } catch {
      return '—';
    }
  };

  const formatShortDate = (isoStr?: string | null) => {
    if (!isoStr) return '—';
    try {
      const d = new Date(isoStr);
      return isNaN(d.getTime())
        ? '—'
        : d.toLocaleDateString(undefined, {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
          });
    } catch {
      return '—';
    }
  };

  // Computed stats for tabs
  const activeMedsCount = useMemo(() => medications.filter((m) => m.is_active).length, [medications]);
  const inactiveMedsCount = useMemo(() => medications.filter((m) => !m.is_active).length, [medications]);

  const severeFeedbackCount = useMemo(
    () => feedbackList.filter((f) => f.severity >= 3).length,
    [feedbackList]
  );

  const adherenceStats = useMemo(() => {
    const taken = adherenceRecords.filter((r) => r.status === 'taken').length;
    const missed = adherenceRecords.filter((r) => r.status === 'missed').length;
    const rate = adherenceRecords.length > 0 ? Math.round((taken / adherenceRecords.length) * 100) : 0;
    return { taken, missed, rate, total: adherenceRecords.length };
  }, [adherenceRecords]);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 animate-pulse">
        <div className="h-6 w-36 bg-white/10 rounded-lg" />
        <div className="h-56 bg-white/[0.03] border border-white/10 rounded-3xl" />
        <div className="h-14 bg-white/[0.02] border border-white/5 rounded-2xl" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="h-80 bg-white/[0.03] border border-white/10 rounded-3xl" />
          <div className="h-80 bg-white/[0.03] border border-white/10 rounded-3xl" />
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center space-y-4">
        <div className="w-16 h-16 mx-auto rounded-2xl bg-white/5 flex items-center justify-center text-on-surface-variant">
          <UserX className="w-8 h-8 opacity-40" />
        </div>
        <h2 className="text-xl font-bold text-white">Identity Record Not Found</h2>
        <p className="text-sm text-on-surface-variant max-w-md mx-auto">
          The requested profile does not exist in the directory or has been removed from the platform.
        </p>
        <button
          onClick={() => navigate('/admin/directory')}
          className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-primary text-surface font-bold text-xs shadow-glow hover:bg-primary-container transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Return to Identity Directory</span>
        </button>
      </div>
    );
  }

  const isPatient = user.role === 'patient';
  const isProvider = user.role === 'provider';
  const isAdmin = user.role === 'admin';

  const initials = (user.full_name || 'User')
    .split(' ')
    .filter(Boolean)
    .map((n) => n[0])
    .join('')
    .substring(0, 2)
    .toUpperCase() || 'U';

  const tabs: { id: TabType; label: string; count?: number; highlight?: boolean; icon: React.FC<{ className?: string }> }[] = [
    { id: 'profile', label: 'Profile & Account', icon: Shield },
    { id: 'medications', label: 'Medications', count: medications.length || undefined, icon: Pill },
    { id: 'adherence', label: 'Adherence History', count: adherenceTotal || undefined, icon: Activity },
    {
      id: 'feedback',
      label: 'Side Effects',
      count: feedbackList.length || undefined,
      highlight: severeFeedbackCount > 0,
      icon: MessageSquareWarning,
    },
    { id: 'assignments', label: 'Assignments', count: assignmentsList.length || undefined, icon: UserPlus },
    { id: 'audit', label: 'Audit Trail', count: auditLogs.length || undefined, icon: FileSpreadsheet },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <ToastContainer toasts={toasts} onDismiss={removeToast} />

      {/* Top Breadcrumb Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/admin/directory')}
          className="inline-flex items-center space-x-2 text-xs font-semibold text-on-surface-variant hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Identity Directory</span>
        </button>

        <button
          onClick={handleRefreshAll}
          disabled={refreshing}
          className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-on-surface-variant hover:text-white text-xs font-medium border border-white/5 transition-colors disabled:opacity-50"
          title="Refresh user data"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-primary' : ''}`} />
          <span>{refreshing ? 'Refreshing...' : 'Refresh'}</span>
        </button>
      </div>

      {/* ─── HEADER CARD (Always Visible) ─────────────────────────────────── */}
      <GlassCard className="p-6 sm:p-8 border-white/10 relative overflow-hidden">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          {/* Identity & Status */}
          <div className="flex items-start sm:items-center space-x-4 sm:space-x-5">
            <div
              className={`w-16 h-16 sm:w-20 sm:h-20 rounded-2xl flex items-center justify-center font-extrabold text-xl sm:text-2xl shrink-0 border ${
                isPatient
                  ? 'bg-primary/15 text-primary border-primary/40 shadow-glow'
                  : isProvider
                  ? 'bg-secondary/15 text-secondary border-secondary/40'
                  : 'bg-amber-500/15 text-amber-400 border-amber-500/40'
              }`}
            >
              {initials}
            </div>

            <div className="space-y-1.5 min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight truncate">
                  {user.full_name || 'Unnamed Identity'}
                </h1>

                {/* Role Badge */}
                <span
                  className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${
                    isPatient
                      ? 'bg-primary/10 text-primary border-primary/30'
                      : isProvider
                      ? 'bg-secondary/10 text-secondary border-secondary/30'
                      : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                  }`}
                >
                  {isPatient ? (
                    <UserCheck className="w-3 h-3" />
                  ) : isProvider ? (
                    <Stethoscope className="w-3 h-3" />
                  ) : (
                    <Shield className="w-3 h-3" />
                  )}
                  <span className="capitalize">{user.role}</span>
                </span>

                {/* Active / Suspended Badge */}
                <span
                  className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${
                    user.is_active
                      ? 'bg-status-success/10 text-status-success border-status-success/30'
                      : 'bg-status-danger/10 text-status-danger border-status-danger/30'
                  }`}
                >
                  <span
                    className={`w-2 h-2 rounded-full ${
                      user.is_active ? 'bg-status-success animate-pulse' : 'bg-status-danger'
                    }`}
                  />
                  <span>{user.is_active ? 'Active' : 'Suspended'}</span>
                </span>
              </div>

              {/* Meta Info Row */}
              <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-on-surface-variant">
                <span className="flex items-center gap-1">
                  <Mail className="w-3.5 h-3.5 text-on-surface-variant" />
                  <span>{user.email || 'No email attached'}</span>
                </span>

                {user.contact_number ? (
                  <span className="flex items-center gap-1">
                    <Phone className="w-3.5 h-3.5 text-on-surface-variant" />
                    <span>{user.contact_number}</span>
                  </span>
                ) : (
                  <span className="flex items-center gap-1 italic opacity-60">
                    <Phone className="w-3.5 h-3.5" />
                    <span>No phone</span>
                  </span>
                )}

                <button
                  onClick={handleCopyId}
                  className="flex items-center gap-1 font-mono text-[11px] text-white/50 hover:text-white transition-colors bg-white/[0.03] px-2 py-0.5 rounded border border-white/5"
                  title="Click to copy ID"
                >
                  <span>ID: {user.id.substring(0, 8)}...</span>
                  {copiedId ? <Check className="w-3 h-3 text-status-success" /> : <Copy className="w-3 h-3" />}
                </button>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                setStatusReason('');
                setStatusModalOpen(true);
              }}
              className={`btn-press px-4 py-2.5 rounded-xl font-bold text-xs border transition-all shadow-sm ${
                user.is_active
                  ? 'bg-status-danger/10 text-status-danger hover:bg-status-danger/20 border-status-danger/30'
                  : 'bg-status-success/10 text-status-success hover:bg-status-success/20 border-status-success/30'
              }`}
            >
              {user.is_active ? 'Suspend Account' : 'Reactivate Account'}
            </button>
          </div>
        </div>

        {/* Highlight Summary Stats Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mt-6 pt-6 border-t border-white/10 text-xs">
          {isPatient ? (
            <>
              {/* Stat 1: Age & Blood Group */}
              <div className="bg-white/[0.02] p-3 rounded-xl border border-white/5 flex flex-col justify-between">
                <span className="text-on-surface-variant text-[11px] font-medium flex items-center gap-1">
                  <Droplets className="w-3.5 h-3.5 text-red-400" />
                  <span>Age & Blood Group</span>
                </span>
                <span className="font-bold text-white text-sm mt-1">
                  {user.age ? `${user.age} yrs` : 'Age: Not recorded'} • {user.blood_group || 'Blood: —'}
                </span>
              </div>

              {/* Stat 2: Active Prescriptions */}
              <div className="bg-white/[0.02] p-3 rounded-xl border border-white/5 flex flex-col justify-between">
                <span className="text-on-surface-variant text-[11px] font-medium flex items-center gap-1">
                  <Pill className="w-3.5 h-3.5 text-primary" />
                  <span>Active Prescriptions</span>
                </span>
                <span className="font-bold text-primary text-sm mt-1">
                  {user.active_medicines_count ?? 0} active{' '}
                  <span className="text-white/40 text-[11px] font-normal">
                    ({medications.length || user.active_medicines_count || 0} total)
                  </span>
                </span>
              </div>

              {/* Stat 3: Overall Adherence */}
              <div className="bg-white/[0.02] p-3 rounded-xl border border-white/5 flex flex-col justify-between">
                <span className="text-on-surface-variant text-[11px] font-medium flex items-center gap-1">
                  <TrendingUp className="w-3.5 h-3.5 text-status-success" />
                  <span>Overall Adherence</span>
                </span>
                <span
                  className={`font-bold text-sm mt-1 ${
                    user.overall_adherence_rate !== undefined && user.overall_adherence_rate >= 80
                      ? 'text-status-success'
                      : user.overall_adherence_rate !== undefined && user.overall_adherence_rate >= 60
                      ? 'text-status-warning'
                      : 'text-status-danger'
                  }`}
                >
                  {user.overall_adherence_rate !== undefined ? `${user.overall_adherence_rate}%` : 'No logs yet'}
                </span>
              </div>

              {/* Stat 4: Assigned Provider */}
              <div className="bg-white/[0.02] p-3 rounded-xl border border-white/5 flex flex-col justify-between">
                <span className="text-on-surface-variant text-[11px] font-medium flex items-center gap-1">
                  <Stethoscope className="w-3.5 h-3.5 text-secondary" />
                  <span>Assigned Doctor</span>
                </span>
                <span className="font-bold text-white text-sm mt-1 truncate">
                  {user.assigned_provider ? (
                    `Dr. ${user.assigned_provider.full_name}`
                  ) : (
                    <span className="text-amber-400 font-semibold">Unassigned</span>
                  )}
                </span>
              </div>
            </>
          ) : (
            <>
              {/* Provider Stat 1: Specialization */}
              <div className="bg-white/[0.02] p-3 rounded-xl border border-white/5 flex flex-col justify-between">
                <span className="text-on-surface-variant text-[11px] font-medium">Specialization</span>
                <span className="font-bold text-white text-sm mt-1">
                  {user.specialization || 'General Practice'}
                </span>
              </div>

              {/* Provider Stat 2: License Number */}
              <div className="bg-white/[0.02] p-3 rounded-xl border border-white/5 flex flex-col justify-between">
                <span className="text-on-surface-variant text-[11px] font-medium">Medical License</span>
                <span className="font-bold text-secondary text-sm mt-1 font-mono">
                  {user.license_number || 'Not recorded'}
                </span>
              </div>

              {/* Provider Stat 3: Assigned Patients */}
              <div className="bg-white/[0.02] p-3 rounded-xl border border-white/5 flex flex-col justify-between">
                <span className="text-on-surface-variant text-[11px] font-medium">Active Patient Roster</span>
                <span className="font-bold text-primary text-sm mt-1">
                  {user.assigned_patients?.length ?? 0} patients assigned
                </span>
              </div>

              {/* Provider Stat 4: Last Activity */}
              <div className="bg-white/[0.02] p-3 rounded-xl border border-white/5 flex flex-col justify-between">
                <span className="text-on-surface-variant text-[11px] font-medium">Last Active</span>
                <span className="font-bold text-white text-sm mt-1 truncate">
                  {formatDate(user.last_activity)}
                </span>
              </div>
            </>
          )}
        </div>
      </GlassCard>

      {/* ─── TABS NAVIGATION BAR ─────────────────────────────────────────── */}
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
              {tab.count !== undefined && (
                <span
                  className={`px-1.5 py-0.2 rounded-full text-[10px] font-bold ${
                    tab.highlight
                      ? 'bg-status-danger/20 text-status-danger border border-status-danger/30'
                      : isActive
                      ? 'bg-primary/20 text-primary'
                      : 'bg-white/10 text-on-surface-variant'
                  }`}
                >
                  {tab.count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* ─── TAB 1: Profile & Account ─────────────────────────────────────── */}
      {activeTab === 'profile' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Card A: Biographical & Account Info */}
          <GlassCard className="p-6 space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 border-b border-white/10 pb-3">
              <Shield className="w-4 h-4 text-primary" />
              <span>Biographical & Identity Information</span>
            </h3>

            <div className="space-y-3 text-xs divide-y divide-white/5">
              <div className="flex justify-between items-center pt-2">
                <span className="text-on-surface-variant">Full Legal Name</span>
                <span className="text-white font-medium">{user.full_name || 'Not recorded'}</span>
              </div>
              <div className="flex justify-between items-center pt-2">
                <span className="text-on-surface-variant">Email Address</span>
                <span className="text-white font-medium">{user.email || 'Not recorded'}</span>
              </div>
              <div className="flex justify-between items-center pt-2">
                <span className="text-on-surface-variant">Contact Phone</span>
                <span className="text-white font-medium">{user.contact_number || 'Not recorded'}</span>
              </div>
              <div className="flex justify-between items-center pt-2">
                <span className="text-on-surface-variant">Date of Birth & Age</span>
                <span className="text-white font-medium">
                  {user.date_of_birth
                    ? `${user.date_of_birth} ${user.age ? `(${user.age} yrs)` : ''}`
                    : 'Not recorded'}
                </span>
              </div>
              <div className="flex justify-between items-center pt-2">
                <span className="text-on-surface-variant">Blood Group</span>
                <span className="text-white font-medium">
                  {user.blood_group ? (
                    <span className="px-2 py-0.5 rounded bg-red-500/10 text-red-400 font-bold border border-red-500/20">
                      {user.blood_group}
                    </span>
                  ) : (
                    'Not recorded'
                  )}
                </span>
              </div>
              <div className="flex justify-between items-center pt-2">
                <span className="text-on-surface-variant">Timezone</span>
                <span className="text-white font-medium flex items-center gap-1">
                  <Globe className="w-3.5 h-3.5 text-on-surface-variant" />
                  <span>{user.timezone || 'UTC'}</span>
                </span>
              </div>
              <div className="flex justify-between items-center pt-2">
                <span className="text-on-surface-variant">Registered On</span>
                <span className="text-white font-medium">{formatDate(user.created_at)}</span>
              </div>
              <div className="flex justify-between items-center pt-2">
                <span className="text-on-surface-variant">Last Active</span>
                <span className="text-white font-medium">{formatDate(user.last_activity)}</span>
              </div>
            </div>
          </GlassCard>

          {/* Card B: Clinical Profile & Emergency Records (Patient) or Credentials (Provider) */}
          <GlassCard className="p-6 space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 border-b border-white/10 pb-3">
              <HeartPulse className="w-4 h-4 text-tertiary" />
              <span>{isPatient ? 'Clinical Profile & Emergency Records' : 'Professional Credentials & Roster'}</span>
            </h3>

            {isPatient ? (
              <div className="space-y-4 text-xs">
                {/* Allergies */}
                <div>
                  <span className="text-on-surface-variant block mb-1.5 font-semibold text-[11px] uppercase tracking-wider">
                    Known Allergies
                  </span>
                  {user.allergies && user.allergies.length > 0 ? (
                    <div className="flex flex-wrap gap-1.5">
                      {user.allergies.map((a, i) => (
                        <span
                          key={i}
                          className="px-2.5 py-1 rounded-lg bg-status-danger/10 text-status-danger border border-status-danger/20 font-medium"
                        >
                          {a}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <div className="p-2.5 rounded-xl bg-white/[0.02] border border-white/5 text-white/50 italic flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 text-white/30 shrink-0" />
                      <span>No known drug or food allergies recorded</span>
                    </div>
                  )}
                </div>

                {/* Medical Conditions */}
                <div>
                  <span className="text-on-surface-variant block mb-1.5 font-semibold text-[11px] uppercase tracking-wider">
                    Medical Conditions & History
                  </span>
                  {user.medical_conditions && user.medical_conditions.length > 0 ? (
                    <div className="flex flex-wrap gap-1.5">
                      {user.medical_conditions.map((c, i) => (
                        <span
                          key={i}
                          className="px-2.5 py-1 rounded-lg bg-secondary/10 text-secondary border border-secondary/20 font-medium"
                        >
                          {c}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <div className="p-2.5 rounded-xl bg-white/[0.02] border border-white/5 text-white/50 italic flex items-center gap-2">
                      <Info className="w-4 h-4 text-white/30 shrink-0" />
                      <span>No primary medical conditions documented</span>
                    </div>
                  )}
                </div>

                {/* Emergency Contact */}
                <div>
                  <span className="text-on-surface-variant block mb-1.5 font-semibold text-[11px] uppercase tracking-wider">
                    Emergency Contact
                  </span>
                  {user.emergency_contact && user.emergency_contact.full_name ? (
                    <div className="p-3.5 rounded-xl bg-white/[0.03] border border-white/10 space-y-2 text-xs">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-white text-sm">
                            {user.emergency_contact.full_name}
                          </span>
                          {user.emergency_contact.relationship && (
                            <span className="px-2 py-0.5 rounded bg-white/10 text-white/80 text-[10px] font-semibold">
                              {user.emergency_contact.relationship}
                            </span>
                          )}
                        </div>
                        {user.emergency_contact.is_verified ? (
                          <span className="px-2 py-0.5 rounded-full bg-status-success/10 text-status-success border border-status-success/30 text-[10px] font-semibold flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3" />
                            <span>Verified</span>
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded-full bg-white/5 text-white/40 border border-white/10 text-[10px]">
                            Unverified
                          </span>
                        )}
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1 text-on-surface-variant">
                        {user.emergency_contact.phone ? (
                          <div className="flex items-center gap-1.5 text-white">
                            <Phone className="w-3.5 h-3.5 text-primary" />
                            <span>{user.emergency_contact.phone}</span>
                          </div>
                        ) : (
                          <div className="flex items-center gap-1.5 text-white/40 italic">
                            <Phone className="w-3.5 h-3.5" />
                            <span>No phone provided</span>
                          </div>
                        )}

                        {user.emergency_contact.email ? (
                          <div className="flex items-center gap-1.5 text-white truncate">
                            <Mail className="w-3.5 h-3.5 text-secondary" />
                            <span className="truncate">{user.emergency_contact.email}</span>
                          </div>
                        ) : (
                          <div className="flex items-center gap-1.5 text-white/40 italic">
                            <Mail className="w-3.5 h-3.5" />
                            <span>No email provided</span>
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5 text-white/50 italic flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-amber-400/50 shrink-0" />
                      <span>No emergency contact registered for this patient</span>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              /* Provider Credentials View */
              <div className="space-y-4 text-xs">
                <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5 space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-on-surface-variant">Medical License</span>
                    <span className="text-secondary font-mono font-bold">{user.license_number || 'Not recorded'}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-on-surface-variant">Clinical Specialty</span>
                    <span className="text-white font-medium">{user.specialization || 'General Practice'}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-on-surface-variant">Practitioner Status</span>
                    <span className="text-status-success font-semibold flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Verified Provider</span>
                    </span>
                  </div>
                </div>

                <div>
                  <span className="text-on-surface-variant block mb-1.5 font-semibold text-[11px] uppercase tracking-wider">
                    Assigned Patients Roster ({user.assigned_patients?.length ?? 0})
                  </span>
                  {user.assigned_patients && user.assigned_patients.length > 0 ? (
                    <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                      {user.assigned_patients.map((p) => (
                        <div
                          key={p.id}
                          onClick={() => navigate(`/admin/directory/${p.id}`)}
                          className="p-2.5 rounded-xl bg-white/[0.03] hover:bg-white/10 border border-white/5 flex items-center justify-between cursor-pointer transition-colors"
                        >
                          <span className="font-semibold text-white">{p.full_name}</span>
                          <span className="text-primary text-[11px] flex items-center gap-1">
                            <span>View Profile</span>
                            <ExternalLink className="w-3 h-3" />
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5 text-white/50 italic">
                      No active patients currently assigned.
                    </div>
                  )}
                </div>
              </div>
            )}
          </GlassCard>
        </div>
      )}

      {/* ─── TAB 2: Medications ───────────────────────────────────────────── */}
      {activeTab === 'medications' && (
        <GlassCard className="p-6 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-white/10">
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Pill className="w-4 h-4 text-primary" />
                <span>Prescription & Medication Regimens</span>
              </h3>
              <p className="text-xs text-on-surface-variant mt-0.5">
                Active prescriptions, dosage parameters, and scheduled frequencies.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <span className="px-2.5 py-1 rounded-lg bg-status-success/10 text-status-success border border-status-success/30 text-xs font-semibold">
                {activeMedsCount} Active
              </span>
              <span className="px-2.5 py-1 rounded-lg bg-white/5 text-on-surface-variant border border-white/10 text-xs font-semibold">
                {inactiveMedsCount} Inactive / Past
              </span>
            </div>
          </div>

          {medsLoading ? (
            <div className="space-y-3 animate-pulse">
              <div className="h-20 bg-white/[0.03] rounded-xl border border-white/5" />
              <div className="h-20 bg-white/[0.03] rounded-xl border border-white/5" />
            </div>
          ) : medications.length === 0 ? (
            <div className="text-center py-12 text-on-surface-variant">
              <div className="w-12 h-12 mx-auto rounded-2xl bg-white/5 flex items-center justify-center mb-3">
                <Pill className="w-6 h-6 opacity-30 text-primary" />
              </div>
              <p className="text-sm font-bold text-white">No medications registered</p>
              <p className="text-xs text-on-surface-variant mt-1">
                This patient currently has no active or historical prescriptions.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {medications.map((m) => {
                const dosageDisplay =
                  m.dosage_amount !== undefined && m.dosage_unit
                    ? `${m.dosage_amount} ${m.dosage_unit}`
                    : m.dosage || '—';
                const frequencyDisplay = m.frequency_type || m.frequency || 'Daily';

                return (
                  <div
                    key={m.id}
                    className="p-4 rounded-2xl bg-white/[0.02] hover:bg-white/[0.04] border border-white/5 transition-colors space-y-2.5 text-xs"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div className="flex items-center gap-2.5">
                        <span className="font-bold text-white text-sm">{m.name}</span>
                        <span
                          className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
                            m.is_active
                              ? 'bg-status-success/10 text-status-success border-status-success/30'
                              : 'bg-white/5 text-white/40 border-white/10'
                          }`}
                        >
                          {m.is_active ? 'Active Prescription' : 'Archived / Ended'}
                        </span>
                      </div>

                      <div className="text-on-surface-variant text-xs">
                        <span>Started: <strong className="text-white">{formatShortDate(m.start_date)}</strong></span>
                        {m.end_date ? (
                          <span className="ml-3">Ends: <strong className="text-white">{formatShortDate(m.end_date)}</strong></span>
                        ) : (
                          <span className="ml-3 text-primary font-medium">Ongoing</span>
                        )}
                      </div>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 pt-1 text-on-surface-variant">
                      <div className="bg-white/[0.02] p-2 rounded-lg border border-white/5">
                        <span className="text-[10px] block text-on-surface-variant">Dosage</span>
                        <span className="font-semibold text-white">{dosageDisplay}</span>
                      </div>
                      <div className="bg-white/[0.02] p-2 rounded-lg border border-white/5">
                        <span className="text-[10px] block text-on-surface-variant">Frequency</span>
                        <span className="font-semibold text-white capitalize">{frequencyDisplay}</span>
                      </div>
                      <div className="bg-white/[0.02] p-2 rounded-lg border border-white/5">
                        <span className="text-[10px] block text-on-surface-variant">Route</span>
                        <span className="font-semibold text-white capitalize">{m.route || 'Oral'}</span>
                      </div>
                    </div>

                    {m.instructions && (
                      <div className="p-2.5 rounded-xl bg-primary/5 border border-primary/15 text-primary text-xs flex items-start gap-2">
                        <Info className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                        <span>{m.instructions}</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </GlassCard>
      )}

      {/* ─── TAB 3: Adherence History ─────────────────────────────────────── */}
      {activeTab === 'adherence' && (
        <GlassCard className="p-6 space-y-5">
          {/* Header & Export */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-white/10">
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Activity className="w-4 h-4 text-status-success" />
                <span>Adherence Telemetry Log ({adherenceTotal} total records)</span>
              </h3>
              <p className="text-xs text-on-surface-variant mt-0.5">
                Detailed dosage confirmation logs, timestamps, and compliance rates.
              </p>
            </div>

            <button
              onClick={handleExportCSV}
              disabled={exportingCSV || adherenceTotal === 0}
              className="btn-press inline-flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-primary border border-primary/30 text-xs font-semibold self-start sm:self-auto disabled:opacity-40 transition-colors"
            >
              <Download className={`w-4 h-4 ${exportingCSV ? 'animate-bounce' : ''}`} />
              <span>{exportingCSV ? 'Exporting...' : 'Export Adherence (CSV)'}</span>
            </button>
          </div>

          {/* Quick Metrics & Filter Bar */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div className="bg-white/[0.02] p-3 rounded-xl border border-white/5">
              <span className="text-on-surface-variant block text-[11px]">Total Scheduled</span>
              <span className="font-bold text-white text-base mt-0.5 block">{adherenceTotal} doses</span>
            </div>
            <div className="bg-white/[0.02] p-3 rounded-xl border border-white/5">
              <span className="text-on-surface-variant block text-[11px]">Page Taken Count</span>
              <span className="font-bold text-status-success text-base mt-0.5 block">
                {adherenceStats.taken} doses
              </span>
            </div>
            <div className="bg-white/[0.02] p-3 rounded-xl border border-white/5">
              <span className="text-on-surface-variant block text-[11px]">Page Missed Count</span>
              <span className="font-bold text-status-danger text-base mt-0.5 block">
                {adherenceStats.missed} doses
              </span>
            </div>
            <div className="bg-white/[0.02] p-3 rounded-xl border border-white/5">
              <span className="text-on-surface-variant block text-[11px]">Status Filter</span>
              <select
                value={adherenceStatusFilter}
                onChange={(e) => {
                  setAdherenceStatusFilter(e.target.value);
                  setAdherencePage(1);
                }}
                className="mt-1 w-full bg-black/40 border border-white/10 rounded-lg px-2 py-1 text-xs text-white focus:outline-none focus:border-primary/50"
              >
                <option value="">All Statuses</option>
                <option value="taken">Taken Only</option>
                <option value="missed">Missed Only</option>
                <option value="skipped">Skipped Only</option>
              </select>
            </div>
          </div>

          {/* Table / List */}
          {adherenceLoading ? (
            <div className="space-y-3 animate-pulse">
              <div className="h-12 bg-white/5 rounded-xl" />
              <div className="h-12 bg-white/5 rounded-xl" />
              <div className="h-12 bg-white/5 rounded-xl" />
            </div>
          ) : adherenceRecords.length === 0 ? (
            <div className="text-center py-12 text-on-surface-variant">
              <div className="w-12 h-12 mx-auto rounded-2xl bg-white/5 flex items-center justify-center mb-3">
                <Activity className="w-6 h-6 opacity-30 text-status-success" />
              </div>
              <p className="text-sm font-bold text-white">No adherence records found</p>
              <p className="text-xs text-on-surface-variant mt-1">
                {adherenceStatusFilter
                  ? `No doses matching status '${adherenceStatusFilter}'.`
                  : 'No dosage confirmation logs have been submitted yet.'}
              </p>
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
                    <th className="py-2.5 px-3">Notes & Reason</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {adherenceRecords.map((r, i) => {
                    const isTaken = r.status === 'taken';
                    const isMissed = r.status === 'missed';
                    return (
                      <tr key={r.id || i} className="hover:bg-white/[0.02] transition-colors">
                        <td className="py-3 px-3 text-white font-medium whitespace-nowrap">
                          {r.date || formatDate(r.scheduled_time || r.scheduled_utc)}
                        </td>
                        <td className="py-3 px-3 text-white font-semibold">
                          {r.medicine_name || 'Prescription Dose'}
                        </td>
                        <td className="py-3 px-3 text-on-surface-variant">
                          {r.dose_label || '—'}
                        </td>
                        <td className="py-3 px-3">
                          <span
                            className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
                              isTaken
                                ? 'bg-status-success/10 text-status-success border-status-success/30'
                                : isMissed
                                ? 'bg-status-danger/10 text-status-danger border-status-danger/30'
                                : 'bg-status-warning/10 text-status-warning border-status-warning/30'
                            }`}
                          >
                            {isTaken ? (
                              <CheckCircle2 className="w-3 h-3" />
                            ) : isMissed ? (
                              <XCircle className="w-3 h-3" />
                            ) : (
                              <HelpCircle className="w-3 h-3 text-status-warning" />
                            )}
                            <span className="capitalize">{r.status}</span>
                          </span>
                        </td>
                        <td className="py-3 px-3 text-on-surface-variant whitespace-nowrap">
                          {formatDate(r.logged_at || r.outcome_utc || r.created_at)}
                        </td>
                        <td className="py-3 px-3 text-on-surface-variant max-w-[180px] truncate" title={r.notes || ''}>
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
                  <span>
                    Showing page {adherencePage} of {Math.ceil(adherenceTotal / adherenceLimit)}
                  </span>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setAdherencePage((p) => Math.max(1, p - 1))}
                      disabled={adherencePage <= 1}
                      className="px-3 py-1 rounded-lg bg-white/5 hover:bg-white/10 disabled:opacity-30 text-white font-medium transition-colors"
                    >
                      Previous
                    </button>
                    <button
                      onClick={() => setAdherencePage((p) => p + 1)}
                      disabled={adherencePage >= Math.ceil(adherenceTotal / adherenceLimit)}
                      className="px-3 py-1 rounded-lg bg-white/5 hover:bg-white/10 disabled:opacity-30 text-white font-medium transition-colors"
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

      {/* ─── TAB 4: Side Effects ──────────────────────────────────────────── */}
      {activeTab === 'feedback' && (
        <GlassCard className="p-6 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-white/10">
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <MessageSquareWarning className="w-4 h-4 text-status-warning" />
                <span>Side Effect Reports & Adverse Reactions ({feedbackList.length})</span>
              </h3>
              <p className="text-xs text-on-surface-variant mt-0.5">
                Patient-reported adverse events, symptoms, and severity classifications.
              </p>
            </div>

            {severeFeedbackCount > 0 && (
              <span className="px-3 py-1 rounded-lg bg-status-danger/15 text-status-danger border border-status-danger/30 text-xs font-bold flex items-center gap-1.5 self-start sm:self-auto animate-pulse">
                <AlertCircle className="w-3.5 h-3.5" />
                <span>{severeFeedbackCount} Severe / Critical Alerts</span>
              </span>
            )}
          </div>

          {feedbackLoading ? (
            <div className="space-y-3 animate-pulse">
              <div className="h-20 bg-white/5 rounded-xl" />
              <div className="h-20 bg-white/5 rounded-xl" />
            </div>
          ) : feedbackList.length === 0 ? (
            <div className="text-center py-12 text-on-surface-variant">
              <div className="w-12 h-12 mx-auto rounded-2xl bg-white/5 flex items-center justify-center mb-3">
                <MessageSquareWarning className="w-6 h-6 opacity-30 text-status-warning" />
              </div>
              <p className="text-sm font-bold text-white">No adverse reactions reported</p>
              <p className="text-xs text-on-surface-variant mt-1">
                This user has not filed any side-effect feedback or symptom reports.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {feedbackList.map((f: any) => {
                const isCritical = f.severity >= 3;
                const severityLabels: Record<number, { label: string; color: string }> = {
                  1: { label: 'Grade 1 — Mild', color: 'bg-blue-500/10 text-blue-400 border-blue-500/30' },
                  2: { label: 'Grade 2 — Moderate', color: 'bg-status-warning/10 text-status-warning border-status-warning/30' },
                  3: { label: 'Grade 3 — Severe', color: 'bg-orange-500/10 text-orange-400 border-orange-500/30 font-bold' },
                  4: { label: 'Grade 4 — Critical / Urgent', color: 'bg-status-danger/15 text-status-danger border-status-danger/40 font-extrabold' },
                };
                const currentSeverity = severityLabels[f.severity] || severityLabels[1];
                const medName = f.medicine_name || f.medicines?.name || 'Unspecified Prescription';

                return (
                  <div
                    key={f.id}
                    className={`p-4 rounded-2xl border transition-colors space-y-2.5 ${
                      isCritical
                        ? 'bg-status-danger/[0.03] border-status-danger/30 shadow-sm'
                        : 'bg-white/[0.02] border-white/5'
                    }`}
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className={`px-2.5 py-0.5 rounded-full text-[11px] border ${currentSeverity.color}`}>
                          {currentSeverity.label}
                        </span>
                        <span className="text-xs font-bold text-primary">{medName}</span>
                      </div>
                      <span className="text-xs text-on-surface-variant">{formatDate(f.created_at)}</span>
                    </div>

                    <p className="text-xs sm:text-sm text-white font-medium leading-relaxed">
                      {f.description}
                    </p>

                    {isCritical && (
                      <div className="pt-1 flex items-center gap-1.5 text-[11px] text-status-danger font-semibold">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        <span>Requires clinical provider review / dosage adjustment</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </GlassCard>
      )}

      {/* ─── TAB 5: Assignments ───────────────────────────────────────────── */}
      {activeTab === 'assignments' && (
        <GlassCard className="p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-white/10">
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <UserPlus className="w-4 h-4 text-secondary" />
                <span>Care Provider & Patient Relationships ({assignmentsList.length})</span>
              </h3>
              <p className="text-xs text-on-surface-variant mt-0.5">
                Active and historical assignments between patients and clinical practitioners.
              </p>
            </div>
          </div>

          {assignmentsLoading ? (
            <div className="space-y-3 animate-pulse">
              <div className="h-16 bg-white/5 rounded-xl" />
            </div>
          ) : assignmentsList.length === 0 ? (
            <div className="text-center py-12 text-on-surface-variant">
              <div className="w-12 h-12 mx-auto rounded-2xl bg-white/5 flex items-center justify-center mb-3">
                <UserPlus className="w-6 h-6 opacity-30 text-secondary" />
              </div>
              <p className="text-sm font-bold text-white">No assignment records</p>
              <p className="text-xs text-on-surface-variant mt-1">
                No doctor-patient relationships recorded for this profile.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {assignmentsList.map((a) => {
                const isActiveAsg = a.status === 'active';
                return (
                  <div
                    key={a.id}
                    className="p-4 rounded-2xl bg-white/[0.02] border border-white/5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
                  >
                    <div className="space-y-1.5">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-white text-sm">
                          {isPatient
                            ? `Provider: Dr. ${a.provider_name || 'Healthcare Provider'}`
                            : `Patient: ${a.patient_name || 'Patient'}`}
                        </span>
                        <span
                          className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border uppercase ${
                            isActiveAsg
                              ? 'bg-status-success/10 text-status-success border-status-success/30'
                              : 'bg-white/5 text-white/40 border-white/10'
                          }`}
                        >
                          {a.status}
                        </span>
                      </div>

                      <div className="text-on-surface-variant flex flex-wrap gap-x-4 gap-y-1">
                        {isPatient ? (
                          <span>Doctor Email: <strong className="text-white/80">{a.provider_email || '—'}</strong></span>
                        ) : (
                          <span>Patient Email: <strong className="text-white/80">{a.patient_email || '—'}</strong></span>
                        )}
                        <span>
                          Assigned on: <strong className="text-white/80">{formatShortDate(a.assigned_on || a.created_at)}</strong>
                        </span>
                      </div>
                    </div>

                    <div className="text-on-surface-variant text-right">
                      {isProvider && a.patient_id && (
                        <button
                          onClick={() => navigate(`/admin/directory/${a.patient_id}`)}
                          className="px-3 py-1.5 rounded-lg bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20 font-semibold text-xs flex items-center gap-1.5 transition-colors"
                        >
                          <span>Open Patient</span>
                          <ExternalLink className="w-3 h-3" />
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </GlassCard>
      )}

      {/* ─── TAB 6: Audit Trail ───────────────────────────────────────────── */}
      {activeTab === 'audit' && (
        <GlassCard className="p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-white/10">
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <FileSpreadsheet className="w-4 h-4 text-primary" />
                <span>Security & Identity Audit Trail ({auditLogs.length} events)</span>
              </h3>
              <p className="text-xs text-on-surface-variant mt-0.5">
                Append-only chronological audit log of administrative and authentication events.
              </p>
            </div>
          </div>

          {auditLoading ? (
            <div className="space-y-3 animate-pulse">
              <div className="h-12 bg-white/5 rounded-xl" />
              <div className="h-12 bg-white/5 rounded-xl" />
            </div>
          ) : auditLogs.length === 0 ? (
            <div className="text-center py-12 text-on-surface-variant">
              <div className="w-12 h-12 mx-auto rounded-2xl bg-white/5 flex items-center justify-center mb-3">
                <Shield className="w-6 h-6 opacity-30 text-primary" />
              </div>
              <p className="text-sm font-bold text-white">No audit records found</p>
              <p className="text-xs text-on-surface-variant mt-1">
                No security or modification events have been logged for this profile yet.
              </p>
            </div>
          ) : (
            <div className="space-y-2.5">
              {auditLogs.map((log: any) => (
                <div
                  key={log.id}
                  className="p-3.5 rounded-xl bg-white/[0.02] hover:bg-white/[0.04] border border-white/5 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs transition-colors"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-primary bg-primary/10 px-2 py-0.5 rounded border border-primary/20">
                        {log.action_code}
                      </span>
                      {log.actor_name && (
                        <span className="text-white/80 font-medium">
                          by {log.actor_name} ({log.actor_role || 'user'})
                        </span>
                      )}
                    </div>

                    {log.details && (
                      <div className="text-on-surface-variant font-mono text-[11px] bg-black/30 p-1.5 rounded border border-white/5 overflow-x-auto">
                        {typeof log.details === 'object' ? JSON.stringify(log.details) : String(log.details)}
                      </div>
                    )}
                  </div>

                  <div className="text-on-surface-variant text-right shrink-0">
                    <span className="flex items-center gap-1 font-mono text-[11px]">
                      <Clock className="w-3 h-3" />
                      <span>{formatDate(log.created_at)}</span>
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </GlassCard>
      )}

      {/* ─── MODAL: Status Modification (Suspend / Reactivate) ───────────── */}
      <Modal
        isOpen={statusModalOpen}
        onClose={() => setStatusModalOpen(false)}
        title={user.is_active ? 'Confirm Account Suspension' : 'Confirm Account Reactivation'}
        maxWidth="md"
      >
        <form onSubmit={handleConfirmStatusChange} className="space-y-4">
          <div
            className={`p-3.5 rounded-xl border text-xs flex items-start gap-2.5 ${
              user.is_active
                ? 'bg-status-danger/10 border-status-danger/20 text-status-danger'
                : 'bg-status-success/10 border-status-success/20 text-status-success'
            }`}
          >
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>
              {user.is_active
                ? 'Suspending this account will immediately revoke authentication tokens and block the user from logging in or receiving notifications.'
                : 'Reactivating this account will restore application access and allow the user to resume medication adherence tracking.'}
            </span>
          </div>

          <div>
            <label className="block text-xs font-semibold text-white mb-1.5">
              Administrative Reason <span className="text-status-danger">*</span>
            </label>
            <textarea
              required
              rows={3}
              value={statusReason}
              onChange={(e) => setStatusReason(e.target.value)}
              placeholder="e.g., Requested by patient, routine compliance review, identity verification..."
              className="w-full px-3.5 py-2.5 bg-black/40 border border-white/10 rounded-xl text-xs sm:text-sm text-white placeholder-on-surface-variant focus:outline-none focus:border-primary/50 transition-colors"
            />
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-white/10">
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
                user.is_active
                  ? 'bg-status-danger hover:bg-status-danger/80'
                  : 'bg-status-success hover:bg-status-success/80'
              }`}
            >
              {statusUpdating
                ? 'Updating...'
                : user.is_active
                ? 'Confirm Suspension'
                : 'Confirm Reactivation'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default DirectoryUserDetail;
