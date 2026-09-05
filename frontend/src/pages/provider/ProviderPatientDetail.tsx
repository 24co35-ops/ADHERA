import React, { useState, useEffect } from 'react';
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
} from 'lucide-react';
import { Profile, Medicine, Feedback, PatientFlag, AdherenceLog } from '../../types';

export const ProviderPatientDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [patient, setPatient] = useState<Profile | null>(null);
  const [medicines, setMedicines] = useState<Medicine[]>([]);
  const [feedback, setFeedback] = useState<Feedback[]>([]);
  const [flags, setFlags] = useState<PatientFlag[]>([]);
  const [adherenceLogs, setAdherenceLogs] = useState<AdherenceLog[]>([]);
  const [trendData, setTrendData] = useState<any[]>([]);
  const [adherenceRate, setAdherenceRate] = useState<number>(100);
  const [loading, setLoading] = useState(true);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const addToast = (type: 'success' | 'warning' | 'error' | 'info', message: string) => {
    setToasts((prev) => [...prev, { id: Math.random().toString(36).substring(2, 9), type, message }]);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const loadPatientData = async () => {
    if (!id) return;
    try {
      setLoading(true);
      const [patientRes, medsRes, fbRes, flagsRes, adhRes, trendRes] = await Promise.allSettled([
        api.get<Profile>(`/provider/patients/${id}`),
        api.get<Medicine[]>(`/provider/patients/${id}/medicines`),
        api.get<Feedback[]>(`/feedback/?patient_id=${id}`),
        api.get<PatientFlag[]>(`/provider/patients/${id}/flags`),
        api.get<any>(`/analytics/adherence?patient_id=${id}`),
        api.get<any[]>(`/analytics/trend?patient_id=${id}`),
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
          <p className="text-xs text-on-surface-variant">Loading patient medical chart...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <ToastContainer toasts={toasts} onDismiss={removeToast} />

      {/* Top Breadcrumb / Back Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/provider')}
          className="btn-press inline-flex items-center space-x-2 text-xs font-semibold text-on-surface-variant hover:text-white"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Provider Roster</span>
        </button>

        <span
          className={`risk-badge-pill ${
            adherenceRate >= 80 ? 'low' : adherenceRate >= 70 ? 'moderate' : 'critical'
          }`}
        >
          Adherence: {adherenceRate}%
        </span>
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
                {patient?.full_name || 'Patient'}
              </h1>
              <p className="text-xs text-on-surface-variant mt-0.5">{patient?.email}</p>
              <div className="flex flex-wrap items-center gap-3 text-xs text-on-surface-variant mt-2">
                {patient?.age && (
                  <span className="px-2.5 py-0.5 rounded-md bg-white/5 font-semibold text-white">
                    Age: {patient.age}
                  </span>
                )}
                {patient?.blood_group && (
                  <span className="px-2.5 py-0.5 rounded-md bg-white/5 font-semibold text-white">
                    Blood: {patient.blood_group}
                  </span>
                )}
                <span>Timezone: {patient?.timezone || 'UTC'}</span>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap gap-2 text-xs">
            {patient?.allergies && patient.allergies.length > 0 && (
              <div className="p-2.5 rounded-xl bg-status-error/10 border border-status-error/20 text-status-error">
                <span className="font-bold block text-[10px] uppercase">Allergies:</span>
                <span>{patient.allergies.join(', ')}</span>
              </div>
            )}
            {patient?.medical_conditions && patient.medical_conditions.length > 0 && (
              <div className="p-2.5 rounded-xl bg-primary/10 border border-primary/20 text-primary">
                <span className="font-bold block text-[10px] uppercase">Conditions:</span>
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
              AI Adherence Detector Flags ({flags.length})
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
                    <span>Resolve Flag</span>
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
          Adherence Rate History (Last 7 Days)
        </h3>
        <AdherenceChart trendData={trendData} />
      </GlassCard>

      {/* Main Bottom Grid: Active Prescriptions & Side Effects */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Active Prescriptions */}
        <GlassCard className="p-6">
          <div className="flex items-center space-x-2 pb-3 border-b border-white/10 mb-4">
            <Pill className="w-5 h-5 text-primary" />
            <h3 className="text-base font-bold text-white">Active Prescriptions ({medicines.length})</h3>
          </div>

          <div className="space-y-3">
            {medicines.length === 0 ? (
              <p className="text-xs text-on-surface-variant py-4 text-center">No active prescriptions.</p>
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
            <h3 className="text-base font-bold text-white">Reported Side Effects ({feedback.length})</h3>
          </div>

          <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
            {feedback.length === 0 ? (
              <p className="text-xs text-on-surface-variant py-4 text-center">No adverse events reported.</p>
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
    </div>
  );
};
