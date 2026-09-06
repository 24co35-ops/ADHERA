import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { useAuthStore } from '../../stores/authStore';
import { useI18n } from '../../lib/i18n';
import { GlassCard } from '../../components/GlassCard';
import { AdherenceChart } from '../../components/AdherenceChart';
import { ToastMessage, ToastContainer } from '../../components/Toast';
import {
  CheckCircle,
  XCircle,
  Clock,
  Flame,
  AlertTriangle,
  Pill,
  Download,
  Stethoscope,
  ChevronRight,
  TrendingUp,
  Calendar,
  Sparkles,
  Wind,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { DashboardStats, UpcomingDose, Feedback, MyProviderResponse } from '../../types';
import { adheraFetch } from '../../lib/api';
import { ChatDrawer } from '../../components/ChatDrawer';

export const PatientDashboard: React.FC = () => {
  const { user } = useAuthStore();
  const { t } = useI18n();

  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [upcomingDoses, setUpcomingDoses] = useState<UpcomingDose[]>([]);
  const [trendData, setTrendData] = useState<any[]>([]);
  const [recentFeedback, setRecentFeedback] = useState<Feedback[]>([]);
  const [providerInfo, setProviderInfo] = useState<MyProviderResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const addToast = (type: 'success' | 'warning' | 'error' | 'info', message: string) => {
    const newToast: ToastMessage = {
      id: Math.random().toString(36).substring(2, 9),
      type,
      message,
    };
    setToasts((prev) => [...prev, newToast]);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [statsRes, dosesRes, trendRes, feedbackRes, providerRes] = await Promise.allSettled([
        api.get<DashboardStats>('/analytics/dashboard'),
        api.get<UpcomingDose[]>('/doses/upcoming'),
        api.get<any[]>('/analytics/trend'),
        api.get<Feedback[]>('/feedback/?limit=3'),
        api.get<MyProviderResponse>('/assignments/my-provider'),
      ]);

      if (statsRes.status === 'fulfilled' && statsRes.value.success) {
        setStats(statsRes.value.data);
      }
      if (dosesRes.status === 'fulfilled' && dosesRes.value.success) {
        setUpcomingDoses(dosesRes.value.data || []);
      }
      if (trendRes.status === 'fulfilled' && trendRes.value.success) {
        setTrendData(trendRes.value.data || []);
      }
      if (feedbackRes.status === 'fulfilled' && feedbackRes.value.success) {
        setRecentFeedback(feedbackRes.value.data || []);
      }
      if (providerRes.status === 'fulfilled' && providerRes.value.success) {
        setProviderInfo(providerRes.value.data);
      }
    } catch (err) {
      console.error('Failed to load dashboard:', err);
      addToast('error', 'Could not refresh some dashboard data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const handleDoseAction = async (reminderId: string, action: 'taken' | 'missed' | 'snooze') => {
    try {
      const res = await api.post<any>(`/doses/${reminderId}/${action}`);
      if (res.success) {
        if (action === 'taken') addToast('success', 'Dose recorded as taken! Great job.');
        else if (action === 'missed') addToast('warning', 'Dose marked as missed.');
        else addToast('info', 'Dose snoozed for 15 minutes.');

        // Refresh upcoming doses and analytics
        loadDashboardData();
      }
    } catch (err: any) {
      addToast('error', err.message || `Failed to record dose as ${action}`);
    }
  };

  const handleExport = async (format: 'json' | 'csv') => {
    try {
      setExporting(true);
      const res = await fetch(`/v1/profile/export?format=${format}`, {
        headers: {
          Authorization: `Bearer ${sessionStorage.getItem('adhera_token') || localStorage.getItem('adhera_token')}`,
        },
      });

      if (!res.ok) throw new Error('Export download failed');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `adhera_export_${new Date().toISOString().slice(0, 10)}.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      addToast('success', `Export generated! Check your downloads.`);
    } catch (err: any) {
      addToast('error', err.message || 'Export failed.');
    } finally {
      setExporting(false);
    }
  };

  const formatUtcTime = (isoString: string) => {
    try {
      const dt = new Date(isoString);
      return dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <ToastContainer toasts={toasts} onDismiss={removeToast} />

      {/* Header Greeting */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-2">
            <span>Hello, {user?.full_name?.split(' ')[0] || 'Patient'}</span>
            <span className="text-xl">👋</span>
          </h1>
          <p className="text-xs sm:text-sm text-on-surface-variant mt-1">
            Track your daily prescription adherence and insights
          </p>
        </div>

        {/* Action button to export / report */}
        <div className="flex items-center gap-2">
          <Link
            to="/feedback"
            className="btn-press flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-status-error/10 hover:bg-status-error/20 text-status-error text-xs font-semibold border border-status-error/20"
          >
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>Report Side Effect</span>
          </Link>
          <button
            onClick={() => handleExport('csv')}
            disabled={exporting}
            className="btn-press flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-on-surface text-xs font-semibold border border-white/10"
          >
            <Download className="w-3.5 h-3.5 text-primary" />
            <span>{exporting ? 'Exporting...' : 'Export Data'}</span>
          </button>
        </div>
      </div>

      {/* Low Adherence Alert Banner */}
      {stats?.weekly_warning && (
        <div className="rounded-2xl p-4 bg-status-warning/10 border border-status-warning/30 flex items-start space-x-3 glow-amber">
          <AlertTriangle className="w-5 h-5 text-status-warning shrink-0 mt-0.5" />
          <div className="text-xs">
            <span className="font-bold text-status-warning block text-sm">
              Adherence Warning (&lt; 70%)
            </span>
            <p className="text-on-surface mt-0.5">
              Your weekly adherence is at {stats.weekly_percentage}%. Please follow your daily schedule to stay on track with your doctor's recommendations.
            </p>
          </div>
        </div>
      )}

      {/* Key Stats Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Weekly Adherence */}
        <GlassCard className="p-5 flex flex-col justify-between" glow={stats?.weekly_warning ? 'amber' : 'cyan'}>
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
              {t('stat.overall_adherence')}
            </span>
            <TrendingUp className="w-4 h-4 text-primary" />
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-white tracking-tight">
              {stats?.weekly_adherence ?? 100}%
            </span>
            <span className="text-[11px] text-primary font-medium">Weekly rate</span>
          </div>
          <div className="mt-2 w-full bg-white/5 rounded-full h-1.5 overflow-hidden">
            <div
              className="bg-primary h-full rounded-full transition-all duration-500 shadow-glow"
              style={{ width: `${Math.min(stats?.weekly_adherence ?? 100, 100)}%` }}
            />
          </div>
        </GlassCard>

        {/* Day Streak */}
        <GlassCard className="p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
              {t('stat.day_streak')}
            </span>
            <Flame className="w-4 h-4 text-status-warning" />
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-white tracking-tight">
              {stats?.streak ?? 0}
            </span>
            <span className="text-[11px] text-on-surface-variant">Consecutive days</span>
          </div>
          <span className="text-[11px] text-status-warning font-semibold mt-2 flex items-center gap-1">
            <Sparkles className="w-3 h-3" />
            Keep it going!
          </span>
        </GlassCard>

        {/* Missed this month */}
        <GlassCard className="p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
              {t('stat.missed_this_month')}
            </span>
            <XCircle className="w-4 h-4 text-status-error" />
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-white tracking-tight">
              {stats?.missed_this_month ?? 0}
            </span>
            <span className="text-[11px] text-on-surface-variant">Doses missed</span>
          </div>
          <span className="text-[11px] text-on-surface-variant mt-2">
            This calendar month
          </span>
        </GlassCard>

        {/* Due Today */}
        <GlassCard className="p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
              {t('stat.due_today')}
            </span>
            <Calendar className="w-4 h-4 text-secondary" />
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-white tracking-tight">
              {stats?.today_taken ?? 0}/{stats?.today_total ?? 0}
            </span>
            <span className="text-[11px] text-secondary font-medium">Completed</span>
          </div>
          <div className="mt-2 w-full bg-white/5 rounded-full h-1.5 overflow-hidden">
            <div
              className="bg-secondary h-full rounded-full transition-all duration-500"
              style={{
                width: `${
                  (stats?.today_total ?? 0) > 0
                    ? Math.round(((stats?.today_taken ?? 0) / (stats?.today_total ?? 1)) * 100)
                    : 100
                }%`,
              }}
            />
          </div>
        </GlassCard>
      </div>

      {/* Main Grid: Today's Schedule + Analytics Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left 2 Cols: Today's Schedule */}
        <div className="lg:col-span-2 space-y-6">
          <GlassCard className="p-6">
            <div className="flex items-center justify-between pb-4 border-b border-white/10">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 rounded-xl bg-primary/10 text-primary">
                  <Pill className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-white">{t('schedule.title')}</h2>
                  <p className="text-xs text-on-surface-variant">Scheduled doses for today</p>
                </div>
              </div>
              <Link
                to="/medicines"
                className="text-xs text-primary font-semibold hover:underline flex items-center gap-1"
              >
                <span>Manage Medicines</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {/* Doses List */}
            <div className="mt-4 space-y-3">
              {upcomingDoses.length === 0 ? (
                <div className="py-10 text-center text-on-surface-variant space-y-2">
                  <CheckCircle className="w-10 h-10 text-status-success mx-auto opacity-75" />
                  <p className="text-sm font-medium">{t('schedule.all_done')}</p>
                </div>
              ) : (
                upcomingDoses.map((item) => {
                  const med = item.reminders?.medicines;
                  return (
                    <div
                      key={item.id}
                      className="p-4 rounded-2xl bg-white/5 border border-white/10 flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-all hover:bg-white/[0.07]"
                    >
                      <div className="flex items-start space-x-3.5">
                        <div className="w-10 h-10 rounded-xl bg-primary/15 text-primary flex items-center justify-center font-bold text-sm shrink-0">
                          <Pill className="w-5 h-5" />
                        </div>
                        <div>
                          <div className="flex items-center space-x-2">
                            <h3 className="text-sm font-bold text-white">{med?.name || 'Medicine'}</h3>
                            <span className="text-xs text-primary font-medium">
                              {med?.dosage}
                            </span>
                          </div>
                          <div className="flex items-center space-x-3 text-xs text-on-surface-variant mt-1">
                            <span className="flex items-center space-x-1">
                              <Clock className="w-3.5 h-3.5 text-secondary" />
                              <span>{formatUtcTime(item.scheduled_utc)}</span>
                            </span>
                            <span className="capitalize px-2 py-0.5 rounded-full bg-white/5 text-[10px]">
                              {item.reminders?.dose_label || 'Dose'}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* One-Tap Buttons */}
                      <div className="flex items-center space-x-2 shrink-0">
                        <button
                          onClick={() => handleDoseAction(item.reminders?.id || item.id, 'taken')}
                          className="btn-press flex items-center space-x-1.5 px-3 py-2 rounded-xl bg-status-success text-surface font-bold text-xs shadow-md hover:opacity-90"
                        >
                          <CheckCircle className="w-3.5 h-3.5" />
                          <span>{t('btn.taken')}</span>
                        </button>
                        <button
                          onClick={() => handleDoseAction(item.reminders?.id || item.id, 'snooze')}
                          className="btn-press px-2.5 py-2 rounded-xl bg-white/10 hover:bg-white/15 text-on-surface text-xs font-semibold"
                        >
                          {t('btn.snooze')}
                        </button>
                        <button
                          onClick={() => handleDoseAction(item.reminders?.id || item.id, 'missed')}
                          className="btn-press px-2.5 py-2 rounded-xl bg-status-error/10 hover:bg-status-error/20 text-red-300 text-xs font-semibold"
                        >
                          {t('btn.missed')}
                        </button>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </GlassCard>

          {/* Adherence Chart Card */}
          <GlassCard className="p-6">
            <div className="flex items-center justify-between pb-3 border-b border-white/10 mb-4">
              <div>
                <h3 className="text-base font-bold text-white">{t('chart.weekly_adherence')}</h3>
                <p className="text-xs text-on-surface-variant">Daily completion rates over the last 7 days</p>
              </div>
            </div>
            <AdherenceChart trendData={trendData} />
          </GlassCard>
        </div>

        {/* Right 1 Col: Provider Connection + Recent Feedback */}
        <div className="space-y-6">
          {/* Provider Card */}
          <GlassCard className="p-6">
            <div className="flex items-center space-x-2.5 pb-4 border-b border-white/10">
              <div className="p-2 rounded-xl bg-secondary/15 text-secondary">
                <Stethoscope className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Healthcare Provider</h3>
                <p className="text-xs text-on-surface-variant">Clinical care team</p>
              </div>
            </div>

            <div className="mt-4">
              {providerInfo?.assigned && providerInfo.data?.profiles ? (
                <div className="space-y-2">
                  <span className="text-xs text-status-success font-semibold flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-status-success animate-pulse" />
                    Connected
                  </span>
                  <p className="text-sm font-bold text-white">
                    {providerInfo.data.profiles.full_name || 'Dr. Physician'}
                  </p>
                  {providerInfo.data.profiles.email && (
                    <p className="text-xs text-on-surface-variant">
                      {providerInfo.data.profiles.email}
                    </p>
                  )}

                </div>
              ) : (
                <div className="text-center py-4 space-y-2">
                  <p className="text-xs text-on-surface-variant">
                    No active provider assigned yet.
                  </p>
                  <Link
                    to="/profile"
                    className="inline-block text-xs text-primary font-semibold hover:underline"
                  >
                    Request Provider &rarr;
                  </Link>
                </div>
              )}
            </div>
          </GlassCard>

          {/* Mental Wellness Breathing Card */}
          <GlassCard className="p-6 border-primary/20 bg-gradient-to-br from-primary/5 via-surface-container to-surface">
            <div className="flex items-center justify-between pb-3 border-b border-white/10 mb-3">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-lg bg-primary/10 text-primary">
                  <Wind className="w-4 h-4" />
                </div>
                <h3 className="text-sm font-bold text-white">Mental Wellness</h3>
              </div>
              <span className="text-[10px] font-bold uppercase text-primary bg-primary/10 px-2 py-0.5 rounded">
                3D Resonance
              </span>
            </div>
            <p className="text-xs text-on-surface-variant mb-4">
              Calm your nervous system and reinforce treatment adherence with guided 3D resonance breathing.
            </p>
            <Link
              to="/patient/wellness"
              className="btn-press flex items-center justify-center gap-2 w-full py-2.5 rounded-xl bg-primary text-surface font-bold text-xs shadow-glow hover:bg-primary-container transition-all"
            >
              <Wind className="w-3.5 h-3.5" />
              <span>Start Breathing Exercise</span>
            </Link>
          </GlassCard>

          {/* Recent Side Effects / Feedback */}
          <GlassCard className="p-6">
            <div className="flex items-center justify-between pb-3 border-b border-white/10 mb-4">
              <h3 className="text-sm font-bold text-white">{t('feedback.title')}</h3>
              <Link to="/feedback" className="text-xs text-primary font-semibold hover:underline">
                {t('feedback.view_all')}
              </Link>
            </div>

            <div className="space-y-3">
              {recentFeedback.length === 0 ? (
                <p className="text-xs text-on-surface-variant py-4 text-center">
                  {t('feedback.empty')}
                </p>
              ) : (
                recentFeedback.map((fb) => (
                  <div key={fb.id} className="p-3 rounded-xl bg-white/5 border border-white/5 text-xs space-y-1">
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
                        Sev {fb.severity}
                      </span>
                    </div>
                    <p className="text-on-surface-variant line-clamp-2">{fb.description}</p>
                  </div>
                ))
              )}
            </div>
          </GlassCard>
        </div>
      </div>

      {/* Floating Medical AI Assistant */}
      <ChatDrawer />
    </div>
  );
};
