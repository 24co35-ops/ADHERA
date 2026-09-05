import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { GlassCard } from '../../components/GlassCard';
import { ToastMessage, ToastContainer } from '../../components/Toast';
import { Modal } from '../../components/Modal';
import {
  MessageSquareWarning,
  AlertTriangle,
  Send,
  Calendar,
  Pill,
  ShieldAlert,
  Clock,
  PhoneCall,
} from 'lucide-react';
import { Medicine, Feedback } from '../../types';
import clsx from 'clsx';

export const FeedbackPage: React.FC = () => {
  const [medicines, setMedicines] = useState<Medicine[]>([]);
  const [feedbackList, setFeedbackList] = useState<Feedback[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  // Form
  const [selectedMedId, setSelectedMedId] = useState('');
  const [severity, setSeverity] = useState<1 | 2 | 3 | 4>(1);
  const [description, setDescription] = useState('');
  const [occurredAt, setOccurredAt] = useState(new Date().toISOString().slice(0, 16));
  const [emergencyModalOpen, setEmergencyModalOpen] = useState(false);

  const addToast = (type: 'success' | 'warning' | 'error' | 'info', message: string) => {
    setToasts((prev) => [...prev, { id: Math.random().toString(36).substring(2, 9), type, message }]);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const loadData = async () => {
    try {
      setLoading(true);
      const [medsRes, feedbackRes] = await Promise.all([
        api.get<Medicine[]>('/medicines/'),
        api.get<Feedback[]>('/feedback/?limit=50'),
      ]);

      if (medsRes.success && medsRes.data) {
        setMedicines(medsRes.data);
        if (medsRes.data.length > 0) {
          setSelectedMedId(medsRes.data[0].id);
        }
      }
      if (feedbackRes.success && feedbackRes.data) {
        setFeedbackList(feedbackRes.data);
      }
    } catch (err: any) {
      addToast('error', err.message || 'Failed to load feedback records');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim()) {
      addToast('error', 'Please describe the side effect or symptom.');
      return;
    }

    if (severity === 4) {
      setEmergencyModalOpen(true);
    } else {
      executeSubmit();
    }
  };

  const executeSubmit = async () => {
    try {
      setSubmitting(true);
      const payload = {
        medicine_id: selectedMedId,
        severity,
        description,
        occurred_at: occurredAt ? new Date(occurredAt).toISOString() : new Date().toISOString(),
      };

      const res = await api.post<Feedback>('/feedback/', payload);
      if (res.success) {
        if (severity === 4) {
          addToast('error', 'Emergency alert dispatched to your healthcare provider and emergency contact.');
        } else {
          addToast('success', 'Feedback recorded. Insights engine updated.');
        }
        setDescription('');
        setSeverity(1);
        setEmergencyModalOpen(false);
        loadData();
      }
    } catch (err: any) {
      addToast('error', err.message || 'Failed to submit feedback');
    } finally {
      setSubmitting(false);
    }
  };

  const severityOptions = [
    {
      level: 1 as const,
      label: 'Level 1: Mild',
      desc: 'Minor symptom, daily activities unaffected',
      color: 'border-status-success/30 hover:border-status-success',
      activeBg: 'bg-status-success/15 border-status-success text-status-success',
    },
    {
      level: 2 as const,
      label: 'Level 2: Moderate',
      desc: 'Noticeable discomfort, manageable',
      color: 'border-yellow-500/30 hover:border-yellow-500',
      activeBg: 'bg-yellow-500/15 border-yellow-500 text-yellow-400',
    },
    {
      level: 3 as const,
      label: 'Level 3: Severe',
      desc: 'Disruptive symptom, difficult to perform tasks',
      color: 'border-status-warning/30 hover:border-status-warning',
      activeBg: 'bg-status-warning/15 border-status-warning text-status-warning',
    },
    {
      level: 4 as const,
      label: 'Level 4: Critical / Emergency',
      desc: 'Severe reaction requiring immediate clinical attention',
      color: 'border-status-error/40 hover:border-status-error',
      activeBg: 'bg-status-error/20 border-status-error text-status-error glow-red',
    },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <ToastContainer toasts={toasts} onDismiss={removeToast} />

      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-2">
          <MessageSquareWarning className="w-7 h-7 text-status-error" />
          <span>Report Side Effect / Feedback</span>
        </h1>
        <p className="text-xs sm:text-sm text-on-surface-variant mt-1">
          Log any symptoms or reactions to help your provider tune your prescription dosage
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left 2 Cols: Form */}
        <div className="lg:col-span-2">
          <GlassCard className="p-6">
            <form onSubmit={handleFormSubmit} className="space-y-6">
              {/* Medicine Select */}
              <div>
                <label htmlFor="feedback-medicine" className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-2">
                  Related Medicine *
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-primary">
                    <Pill className="w-4 h-4" />
                  </div>
                  <select
                    id="feedback-medicine"
                    value={selectedMedId}
                    onChange={(e) => setSelectedMedId(e.target.value)}
                    required
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl glass-input text-sm bg-surface-container"
                  >
                    {medicines.map((med) => (
                      <option key={med.id} value={med.id}>
                        {med.name} ({med.dosage})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Severity Cards */}
              <div>
                <label className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-2">
                  Severity Rating *
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {severityOptions.map((opt) => (
                    <div
                      key={opt.level}
                      onClick={() => setSeverity(opt.level)}
                      className={clsx(
                        'p-3.5 rounded-2xl border cursor-pointer transition-all duration-150',
                        severity === opt.level
                          ? opt.activeBg
                          : 'bg-white/5 border-white/10 hover:bg-white/[0.08]'
                      )}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold">{opt.label}</span>
                        {opt.level === 4 && <ShieldAlert className="w-4 h-4 text-status-error" />}
                      </div>
                      <p className="text-[11px] text-on-surface-variant mt-1">{opt.desc}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Description */}
              <div>
                <label className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-2">
                  Detailed Description *
                </label>
                <textarea
                  rows={4}
                  required
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe your symptoms, when they started, intensity, and any actions taken..."
                  className="w-full p-3 rounded-xl glass-input text-sm"
                />
              </div>

              {/* Occurred At */}
              <div>
                <label htmlFor="feedback-occurred-at" className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-2">
                  Time of Occurrence
                </label>
                <input
                  id="feedback-occurred-at"
                  type="datetime-local"
                  value={occurredAt}
                  onChange={(e) => setOccurredAt(e.target.value)}
                  className="w-full p-2.5 rounded-xl glass-input text-sm text-white"
                />
              </div>

              <button
                type="submit"
                disabled={submitting}
                className={clsx(
                  'w-full btn-press flex items-center justify-center space-x-2 py-3 px-4 rounded-xl font-bold text-sm shadow-md transition-colors disabled:opacity-50',
                  severity === 4
                    ? 'bg-status-error text-white hover:bg-red-600 glow-red'
                    : 'bg-primary text-surface hover:bg-primary-container shadow-glow'
                )}
              >
                <span>{submitting ? 'Submitting...' : severity === 4 ? 'Submit Emergency Alert' : 'Submit Feedback'}</span>
                <Send className="w-4 h-4" />
              </button>
            </form>
          </GlassCard>
        </div>

        {/* Right 1 Col: Past Reports */}
        <div>
          <GlassCard className="p-6">
            <h2 className="text-base font-bold text-white mb-4 pb-3 border-b border-white/10">
              Past Feedback History
            </h2>

            {loading ? (
              <div className="py-10 text-center">
                <div className="w-8 h-8 border-3 border-primary/20 border-t-primary rounded-full animate-spin mx-auto" />
              </div>
            ) : feedbackList.length === 0 ? (
              <p className="text-xs text-on-surface-variant text-center py-6">
                No past feedback submitted.
              </p>
            ) : (
              <div className="space-y-3 max-h-[600px] overflow-y-auto pr-1">
                {feedbackList.map((fb) => (
                  <div
                    key={fb.id}
                    className="p-3.5 rounded-2xl bg-white/5 border border-white/10 text-xs space-y-1.5"
                  >
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
                    <p className="text-on-surface-variant leading-relaxed">{fb.description}</p>
                    <div className="flex items-center space-x-2 text-[10px] text-on-surface-variant/70 pt-1">
                      <Clock className="w-3 h-3" />
                      <span>{new Date(fb.created_at).toLocaleDateString()} at {new Date(fb.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </GlassCard>
        </div>
      </div>

      {/* Emergency Severity 4 Confirmation Modal */}
      <Modal
        isOpen={emergencyModalOpen}
        onClose={() => setEmergencyModalOpen(false)}
        title="Immediate Care Notification"
        maxWidth="md"
      >
        <div className="space-y-4">
          <div className="p-4 rounded-2xl bg-status-error/20 border border-status-error/40 flex items-start space-x-3 glow-red">
            <ShieldAlert className="w-6 h-6 text-status-error shrink-0 mt-0.5" />
            <div>
              <h4 className="text-sm font-bold text-white">Emergency Severity Triggered</h4>
              <p className="text-xs text-on-surface mt-1">
                Submitting a Level 4 alert automatically transmits your details to your assigned doctor and your emergency contacts.
              </p>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-surface-container border border-white/5 text-xs text-on-surface-variant">
            <p>
              If you are experiencing life-threatening symptoms (chest pain, shortness of breath, severe allergic reaction), please call emergency services (911 / 112) immediately.
            </p>
          </div>

          <div className="pt-3 flex items-center justify-end space-x-2">
            <button
              type="button"
              onClick={() => setEmergencyModalOpen(false)}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-on-surface-variant hover:bg-white/5"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={executeSubmit}
              disabled={submitting}
              className="btn-press px-4 py-2 rounded-xl bg-status-error text-white font-bold text-xs shadow-lg hover:bg-red-600"
            >
              {submitting ? 'Dispatching Alert...' : 'Confirm & Dispatch Alert'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
