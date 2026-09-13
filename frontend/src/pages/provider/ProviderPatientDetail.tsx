import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../../lib/api';
import { GlassCard } from '../../components/GlassCard';
import { AdherenceChart } from '../../components/AdherenceChart';
import { ToastMessage, ToastContainer } from '../../components/Toast';
import {
  User as UserIcon,
  ArrowLeft,
  Pill,
  MessageSquareWarning,
  Activity,
  AlertTriangle,
  CheckCircle2,
  Calendar,
  Clock,
  Sparkles,
  ShieldCheck,
  TrendingUp,
  Bot,
  Send,
  X,
  ShieldAlert,
  Wind,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import clsx from 'clsx';
import { Profile, Medicine, Feedback, PatientFlag, AdherenceLog } from '../../types';
import { useI18n } from '../../lib/i18n';
import { usePageMeta } from '../../hooks/usePageMeta';

const CLINICAL_PROMPTS = [
  'Summarise adherence pattern (last 30 days)',
  'List reported side effects & severity',
  'Draft consultation talking points',
  'Analyze potential reasons for missed doses',
  'Identify red flags & clinical risks',
];

export const ProviderPatientDetail: React.FC = () => {
  usePageMeta('Patient Medical Chart', 'Detailed patient medication compliance, adherence curve, and clinical flags.');
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { t } = useI18n();

  const [patient, setPatient] = useState<Profile | null>(null);
  const [medicines, setMedicines] = useState<Medicine[]>([]);
  const [feedback, setFeedback] = useState<Feedback[]>([]);
  const [flags, setFlags] = useState<PatientFlag[]>([]);
  const [adherenceLogs, setAdherenceLogs] = useState<AdherenceLog[]>([]);
  const [trendData, setTrendData] = useState<any[]>([]);
  const [adherenceRate, setAdherenceRate] = useState<number>(100);
  const [loading, setLoading] = useState(true);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  // Wellness Activity State
  const [wellnessData, setWellnessData] = useState<{
    total_sessions_30d: number;
    total_sessions_all_time: number;
    last_session_at: string | null;
    most_used_pattern: string | null;
    avg_duration_seconds: number;
    recent_sessions: Array<{ id: string; pattern_name: string; duration_seconds: number; completed_at: string }>;
  } | null>(null);
  const [wellnessExpanded, setWellnessExpanded] = useState(false);

  // Clinical AI Assistant State
  const [aiOpen, setAiOpen] = useState(false);
  const [aiMessages, setAiMessages] = useState<Array<{ id: string; role: 'user' | 'assistant'; content: string; created_at: string }>>([]);
  const [aiInput, setAiInput] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const aiEndRef = useRef<HTMLDivElement>(null);

  const addToast = (type: 'success' | 'warning' | 'error' | 'info', message: string) => {
    setToasts((prev) => [...prev, { id: Math.random().toString(36).substring(2, 9), type, message }]);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const handleSendAi = async (queryText?: string) => {
    const text = queryText || aiInput;
    if (!text.trim() || aiLoading || !id) return;

    const userMsg = {
      id: Math.random().toString(36).substring(2, 9),
      role: 'user' as const,
      content: text.trim(),
      created_at: new Date().toISOString(),
    };

    setAiMessages((prev) => [...prev, userMsg]);
    if (!queryText) setAiInput('');
    setAiLoading(true);

    try {
      const res = await api.post<any>('/chat/query', {
        message: userMsg.content,
        patient_id: id,
      });

      if (res.success && res.data) {
        setAiMessages((prev) => [
          ...prev,
          {
            id: res.data.id || Math.random().toString(36).substring(2, 9),
            role: 'assistant',
            content: res.data.content,
            created_at: res.data.created_at || new Date().toISOString(),
          },
        ]);
      }
    } catch (err: any) {
      setAiMessages((prev) => [
        ...prev,
        {
          id: Math.random().toString(36).substring(2, 9),
          role: 'assistant',
          content: err.message || 'Unable to connect to clinical decision support.',
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setAiLoading(false);
      setTimeout(() => aiEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);
    }
  };

  const loadPatientData = async () => {
    if (!id) return;
    try {
      setLoading(true);
      const [patientRes, medsRes, fbRes, flagsRes, adhRes, trendRes, wellnessRes] = await Promise.allSettled([
        api.get<Profile>(`/provider/patients/${id}`),
        api.get<Medicine[]>(`/medicines/?patient_id=${id}`),
        api.get<Feedback[]>(`/feedback/?patient_id=${id}`),
        api.get<PatientFlag[]>(`/provider/patients/${id}/flags`),
        api.get<any>(`/analytics/adherence?patient_id=${id}`),
        api.get<any[]>(`/analytics/trend?patient_id=${id}`),
        api.get<any>(`/provider/patients/${id}/wellness`),
      ]);

      if (patientRes.status === 'fulfilled' && patientRes.value.success) {
        setPatient(patientRes.value.data);
      }
      if (medsRes.status === 'fulfilled' && medsRes.value.success) {
        setMedicines(medsRes.value.data || []);
      }
      if (fbRes.status === 'fulfilled' && fbRes.value.success) {
        setFeedback(fbRes.value.data || []);
      }
      if (flagsRes.status === 'fulfilled' && flagsRes.value.success) {
        setFlags(flagsRes.value.data || []);
      }
      if (adhRes.status === 'fulfilled' && adhRes.value.success) {
        setAdherenceRate(adhRes.value.data.rate ?? 100);
        setAdherenceLogs(adhRes.value.data.history || []);
      }
      if (trendRes.status === 'fulfilled' && trendRes.value.success) {
        setTrendData(trendRes.value.data || []);
      }
      if (wellnessRes.status === 'fulfilled' && wellnessRes.value.success) {
        setWellnessData(wellnessRes.value.data);
      }
    } catch (err: any) {
      addToast('error', err.message || 'Failed to load patient details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPatientData();
  }, [id]);

  const handleResolveFlag = async (flagId: string) => {
    try {
      const res = await api.post(`/provider/patients/${id}/flags/${flagId}/resolve`);
      if (res.success) {
        addToast('success', 'Clinical insight flag marked as resolved.');
        loadPatientData();
      }
    } catch (err: any) {
      addToast('error', err.message || 'Failed to resolve flag');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center">
        <div className="flex flex-col items-center space-y-3">
          <div className="w-10 h-10 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
          <p className="text-xs text-on-surface-variant">{t('provider.loading_chart')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <ToastContainer toasts={toasts} onDismiss={removeToast} />

      {/* Top Breadcrumb / Back Navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <button
          onClick={() => navigate('/provider')}
          className="btn-press inline-flex items-center space-x-2 text-xs font-semibold text-on-surface-variant hover:text-white"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>{t('provider.back_to_roster')}</span>
        </button>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => setAiOpen(true)}
            className="btn-press inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-xl bg-primary/10 hover:bg-primary/20 text-primary border border-primary/30 font-bold text-xs shadow-glow transition-all"
          >
            <Bot className="w-4 h-4" />
            <span>Ask Clinical AI</span>
            <span className="text-[10px] bg-primary/20 text-primary px-1.5 py-0.5 rounded font-mono uppercase">
              Patient Context
            </span>
          </button>

          <span
            className={`risk-badge-pill ${
              adherenceRate >= 80 ? 'low' : adherenceRate >= 70 ? 'moderate' : 'critical'
            }`}
          >
            {t('provider.adherence_rate_label')}: {adherenceRate}%
          </span>
        </div>
      </div>

      {/* Patient Header Card */}
      <GlassCard className="p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start space-x-4">
            <div className="w-14 h-14 rounded-2xl bg-primary/20 text-primary flex items-center justify-center font-bold text-xl uppercase shadow-glow shrink-0">
              {patient?.full_name?.charAt(0) || 'P'}
            </div>
            <div>
              <h1 className="text-xl sm:text-2xl font-extrabold text-white">
                {patient?.full_name || t('dashboard.patient')}
              </h1>
              <p className="text-xs text-on-surface-variant mt-0.5">{patient?.email}</p>
              <div className="flex flex-wrap items-center gap-3 text-xs text-on-surface-variant mt-2">
                {patient?.age && (
                  <span className="px-2.5 py-0.5 rounded-md bg-white/5 font-semibold text-white">
                    {t('provider.age')}: {patient.age}
                  </span>
                )}
                {patient?.blood_group && (
                  <span className="px-2.5 py-0.5 rounded-md bg-white/5 font-semibold text-white">
                    {t('provider.blood')}: {patient.blood_group}
                  </span>
                )}
                <span>{t('provider.timezone')}: {patient?.timezone || 'UTC'}</span>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap gap-2 text-xs">
            {patient?.allergies && patient.allergies.length > 0 && (
              <div className="p-2.5 rounded-xl bg-status-error/10 border border-status-error/20 text-status-error">
                <span className="font-bold block text-[10px] uppercase">{t('provider.allergies')}:</span>
                <span>{patient.allergies.join(', ')}</span>
              </div>
            )}
            {patient?.medical_conditions && patient.medical_conditions.length > 0 && (
              <div className="p-2.5 rounded-xl bg-primary/10 border border-primary/20 text-primary">
                <span className="font-bold block text-[10px] uppercase">{t('provider.conditions')}:</span>
                <span>{patient.medical_conditions.join(', ')}</span>
              </div>
            )}
          </div>
        </div>
      </GlassCard>

      {/* AI Clinical Insight Flags */}
      {flags.length > 0 && (
        <GlassCard className="p-6 border-status-warning/30 glow-amber">
          <div className="flex items-center space-x-2 pb-3 border-b border-white/10 mb-4">
            <Sparkles className="w-5 h-5 text-status-warning" />
            <h3 className="text-base font-bold text-white">
              {t('provider.ai_flags_title')} ({flags.length})
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {flags.map((flag) => (
              <div
                key={flag.id}
                className="p-4 rounded-2xl bg-surface-container border border-white/10 space-y-2"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-xs uppercase tracking-wider text-white">
                    {flag.flag_type.replace(/_/g, ' ')}
                  </span>
                  <span
                    className={`risk-badge-pill text-[10px] ${
                      flag.severity === 'critical'
                        ? 'critical'
                        : flag.severity === 'high'
                        ? 'high'
                        : 'moderate'
                    }`}
                  >
                    {flag.severity}
                  </span>
                </div>
                <p className="text-xs text-on-surface-variant">
                  {flag.details?.reason || 'Detector algorithm flagged non-conforming pattern.'}
                </p>
                <div className="pt-2 flex justify-end">
                  <button
                    onClick={() => handleResolveFlag(flag.id)}
                    className="btn-press px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/15 text-xs font-semibold text-white flex items-center space-x-1"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5 text-status-success" />
                    <span>{t('provider.resolve_flag')}</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      )}

      {/* Adherence Trend */}
      <GlassCard className="p-6">
        <h3 className="text-base font-bold text-white mb-4 pb-3 border-b border-white/10">
          {t('provider.adherence_history_title')}
        </h3>
        <AdherenceChart trendData={trendData} />
      </GlassCard>

      {/* Main Bottom Grid: Active Prescriptions & Side Effects */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Active Prescriptions */}
        <GlassCard className="p-6">
          <div className="flex items-center space-x-2 pb-3 border-b border-white/10 mb-4">
            <Pill className="w-5 h-5 text-primary" />
            <h3 className="text-base font-bold text-white">{t('provider.active_rx_title')} ({medicines.length})</h3>
          </div>

          <div className="space-y-3">
            {medicines.length === 0 ? (
              <p className="text-xs text-on-surface-variant py-4 text-center">{t('provider.no_active_rx')}</p>
            ) : (
              medicines.map((med) => (
                <div key={med.id} className="p-3.5 rounded-2xl bg-white/5 border border-white/10 text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white text-sm">{med.name}</span>
                    <span className="text-primary font-semibold">{med.dosage}</span>
                  </div>
                  <div className="flex items-center space-x-3 text-on-surface-variant text-[11px]">
                    <span>Route: {med.route}</span>
                    <span>&bull;</span>
                    <span>{med.frequency}</span>
                    <span>&bull;</span>
                    <span>Started: {med.start_date}</span>
                  </div>
                  {med.instructions && (
                    <p className="text-on-surface-variant/80 italic text-[11px] pt-1">
                      "{med.instructions}"
                    </p>
                  )}
                </div>
              ))
            )}
          </div>
        </GlassCard>

        {/* Side Effects Log */}
        <GlassCard className="p-6">
          <div className="flex items-center space-x-2 pb-3 border-b border-white/10 mb-4">
            <MessageSquareWarning className="w-5 h-5 text-status-error" />
            <h3 className="text-base font-bold text-white">{t('provider.reported_side_effects')} ({feedback.length})</h3>
          </div>

          <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
            {feedback.length === 0 ? (
              <p className="text-xs text-on-surface-variant py-4 text-center">{t('provider.no_adverse_events')}</p>
            ) : (
              feedback.map((fb) => (
                <div key={fb.id} className="p-3.5 rounded-2xl bg-white/5 border border-white/10 text-xs space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white">{fb.medicines?.name || 'Medicine'}</span>
                    <span
                      className={`risk-badge-pill text-[10px] ${
                        fb.severity === 4
                          ? 'critical'
                          : fb.severity === 3
                          ? 'high'
                          : fb.severity === 2
                          ? 'moderate'
                          : 'low'
                      }`}
                    >
                      Severity {fb.severity}
                    </span>
                  </div>
                  <p className="text-on-surface-variant">{fb.description}</p>
                  <span className="text-[10px] text-on-surface-variant/70 block">
                    {new Date(fb.created_at).toLocaleString()}
                  </span>
                </div>
              ))
            )}
          </div>
        </GlassCard>
      </div>

      {/* Wellness Activity */}
      <GlassCard className="p-6 opacity-90">
        <div className="flex items-center justify-between pb-3 border-b border-white/10 mb-4">
          <div className="flex items-center space-x-2">
            <Wind className="w-5 h-5 text-primary/70" />
            <h3 className="text-base font-bold text-white">Wellness Activity</h3>
            <span className="text-[10px] uppercase font-semibold text-on-surface-variant bg-white/5 px-1.5 py-0.5 rounded">Breathing Sessions</span>
          </div>
          {wellnessData && wellnessData.total_sessions_all_time > 0 && (
            <button
              onClick={() => setWellnessExpanded((v) => !v)}
              className="btn-press inline-flex items-center space-x-1 text-xs text-on-surface-variant hover:text-white transition-colors"
            >
              {wellnessExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              <span>{wellnessExpanded ? 'Hide sessions' : 'View sessions'}</span>
            </button>
          )}
        </div>

        {!wellnessData || wellnessData.total_sessions_all_time === 0 ? (
          <p className="text-xs text-on-surface-variant py-4 text-center">
            This patient has not recorded any breathing sessions yet.
          </p>
        ) : (
          <>
            {/* Summary stats */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
              <div className="p-3 rounded-xl bg-white/5 border border-white/10 text-center">
                <p className="text-xl font-extrabold text-white">{wellnessData.total_sessions_30d}</p>
                <p className="text-[10px] text-on-surface-variant mt-0.5">Sessions (30d)</p>
              </div>
              <div className="p-3 rounded-xl bg-white/5 border border-white/10 text-center">
                <p className="text-xs font-bold text-white leading-snug">
                  {wellnessData.last_session_at
                    ? new Date(wellnessData.last_session_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
                    : 'No sessions yet'}
                </p>
                <p className="text-[10px] text-on-surface-variant mt-0.5">Last Session</p>
              </div>
              <div className="p-3 rounded-xl bg-white/5 border border-white/10 text-center">
                <p className="text-xs font-bold text-white leading-snug">{wellnessData.most_used_pattern ?? '—'}</p>
                <p className="text-[10px] text-on-surface-variant mt-0.5">Fav. Pattern</p>
              </div>
              <div className="p-3 rounded-xl bg-white/5 border border-white/10 text-center">
                <p className="text-xs font-bold text-white leading-snug">
                  {wellnessData.avg_duration_seconds > 0
                    ? wellnessData.avg_duration_seconds >= 60
                      ? `${Math.floor(wellnessData.avg_duration_seconds / 60)}m ${wellnessData.avg_duration_seconds % 60}s`
                      : `${wellnessData.avg_duration_seconds}s`
                    : '—'}
                </p>
                <p className="text-[10px] text-on-surface-variant mt-0.5">Avg Duration</p>
              </div>
            </div>

            {/* Expandable recent sessions list */}
            {wellnessExpanded && (
              <div className="space-y-2">
                <p className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant mb-2">Recent Sessions</p>
                {wellnessData.recent_sessions.map((s) => {
                  const dur = s.duration_seconds >= 60
                    ? `${Math.floor(s.duration_seconds / 60)}m ${s.duration_seconds % 60}s`
                    : `${s.duration_seconds}s`;
                  return (
                    <div key={s.id} className="flex items-center justify-between px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-xs">
                      <span className="text-on-surface-variant text-[11px]">
                        {new Date(s.completed_at).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                      </span>
                      <span className="font-semibold text-white">{s.pattern_name}</span>
                      <span className="text-on-surface-variant font-mono">{dur}</span>
                    </div>
                  );
                })}
              </div>
            )}
          </>
        )}
      </GlassCard>

      {/* ── PATIENT-CONTEXTUAL CLINICAL AI ASSISTANT DRAWER ── */}
      {aiOpen && (
        <div className="fixed inset-0 z-50 overflow-hidden flex justify-end">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/70 backdrop-blur-sm transition-opacity"
            onClick={() => setAiOpen(false)}
          />

          {/* Drawer Panel */}
          <div className="relative w-full max-w-xl bg-surface border-l border-white/10 shadow-2xl flex flex-col h-full z-10 animate-in slide-in-from-right duration-200">
            {/* Header */}
            <div className="p-4 border-b border-white/10 flex items-center justify-between bg-surface-container-low shrink-0">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shadow-glow">
                  <Bot className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-bold text-sm text-white">Clinical AI Assistant</h3>
                    <span className="text-[10px] uppercase font-bold text-primary bg-primary/10 px-1.5 py-0.5 rounded border border-primary/20">
                      Decision Support
                    </span>
                  </div>
                  <p className="text-[11px] text-on-surface-variant flex items-center gap-1.5 mt-0.5">
                    <span>Target: <strong className="text-white">{patient?.full_name || 'Selected Patient'}</strong></span>
                    <span className="text-white/30">•</span>
                    <span className="font-mono text-[10px] text-primary">{patient?.id ? `${patient.id.slice(0, 8)}...` : ''}</span>
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={() => setAiOpen(false)}
                className="p-1.5 rounded-lg text-on-surface-variant hover:text-white hover:bg-white/10 transition-colors"
                aria-label="Close assistant"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Injected Patient Context Pills */}
            <div className="bg-white/[0.02] border-b border-white/5 px-4 py-2 flex flex-wrap items-center gap-2 text-[11px] shrink-0">
              <span className="text-on-surface-variant font-semibold">Active Context:</span>
              <span className="px-2 py-0.5 rounded bg-primary/10 text-primary font-medium">
                {medicines.length} Active Rx
              </span>
              <span className="px-2 py-0.5 rounded bg-white/5 text-white font-medium">
                {adherenceRate}% Adherence
              </span>
              {flags.length > 0 && (
                <span className="px-2 py-0.5 rounded bg-status-warning/10 text-status-warning font-medium">
                  {flags.length} AI Flag{flags.length > 1 ? 's' : ''}
                </span>
              )}
              {feedback.length > 0 && (
                <span className="px-2 py-0.5 rounded bg-status-error/10 text-status-error font-medium">
                  {feedback.length} Adverse Event{feedback.length > 1 ? 's' : ''}
                </span>
              )}
            </div>

            {/* Clinical Safety Disclaimer Banner */}
            <div className="bg-primary/5 border-b border-primary/10 px-4 py-2 flex items-center gap-2 text-[11px] text-primary shrink-0">
              <ShieldCheck className="w-3.5 h-3.5 shrink-0" />
              <span>Restricted to patient-specific decision support. Does not replace clinical judgement.</span>
            </div>

            {/* Chat Stream */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {aiMessages.length === 0 ? (
                <div className="text-center py-6 space-y-4">
                  <div className="w-12 h-12 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary mx-auto shadow-glow">
                    <Sparkles className="w-6 h-6" />
                  </div>
                  <div>
                    <h4 className="font-bold text-sm text-white">
                      Ask about {patient?.full_name || 'this patient'}
                    </h4>
                    <p className="text-xs text-on-surface-variant max-w-sm mx-auto mt-1">
                      Query adherence patterns, adverse events, or generate consultation talking points grounded in this patient's records.
                    </p>
                  </div>

                  {/* Suggested Clinical Prompts */}
                  <div className="pt-2 text-left space-y-2 max-w-md mx-auto">
                    <span className="text-[11px] font-bold text-on-surface-variant uppercase tracking-wider block mb-1">
                      Suggested Inquiries
                    </span>
                    {CLINICAL_PROMPTS.map((prompt) => (
                      <button
                        key={prompt}
                        onClick={() => handleSendAi(prompt)}
                        className="w-full text-left p-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/5 hover:border-primary/30 text-xs text-on-surface transition-all flex items-center justify-between group"
                      >
                        <span>{prompt}</span>
                        <span className="text-primary opacity-0 group-hover:opacity-100 transition-opacity">&rarr;</span>
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                aiMessages.map((msg) => (
                  <div
                    key={msg.id}
                    className={clsx('flex flex-col', msg.role === 'user' ? 'items-end' : 'items-start')}
                  >
                    <div className="flex items-start gap-2.5 max-w-[90%]">
                      {msg.role === 'assistant' && (
                        <div className="w-7 h-7 rounded-lg bg-primary/20 border border-primary/30 flex items-center justify-center text-primary shrink-0 mt-0.5">
                          <Bot className="w-3.5 h-3.5" />
                        </div>
                      )}
                      <div
                        className={clsx(
                          'p-3.5 rounded-2xl text-xs leading-relaxed whitespace-pre-wrap shadow-sm',
                          msg.role === 'user'
                            ? 'bg-primary text-surface font-medium rounded-tr-sm'
                            : 'bg-surface-container border border-white/10 text-on-surface rounded-tl-sm'
                        )}
                      >
                        {msg.content}
                      </div>
                    </div>
                    <span className="text-[10px] text-on-surface-variant/60 mt-1 px-1">
                      {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                ))
              )}

              {aiLoading && (
                <div className="flex items-center gap-2 text-xs text-on-surface-variant py-2">
                  <div className="w-5 h-5 border-2 border-primary/20 border-t-primary rounded-full animate-spin" />
                  <span>Synthesizing patient-contextual decision support...</span>
                </div>
              )}
              <div ref={aiEndRef} />
            </div>

            {/* Input Bar */}
            <div className="p-4 border-t border-white/10 bg-surface-container-low shrink-0">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSendAi();
                }}
                className="flex items-center gap-2"
              >
                <input
                  type="text"
                  value={aiInput}
                  onChange={(e) => setAiInput(e.target.value)}
                  placeholder={`Ask about ${patient?.full_name || 'patient'}'s adherence or symptoms...`}
                  disabled={aiLoading}
                  className="flex-1 bg-surface-container border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white placeholder-on-surface-variant focus:outline-none focus:border-primary/50 disabled:opacity-50"
                />
                <button
                  type="submit"
                  disabled={!aiInput.trim() || aiLoading}
                  className="p-2.5 rounded-xl bg-primary text-surface hover:bg-primary-light disabled:opacity-30 transition-all shadow-glow shrink-0"
                  aria-label="Send clinical inquiry"
                >
                  <Send className="w-4 h-4" />
                </button>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
