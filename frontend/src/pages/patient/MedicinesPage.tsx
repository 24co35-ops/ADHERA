import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { useI18n } from '../../lib/i18n';
import { GlassCard } from '../../components/GlassCard';
import { Modal } from '../../components/Modal';
import { ToastMessage, ToastContainer } from '../../components/Toast';
import {
  Pill,
  Plus,
  Edit2,
  Trash2,
  Clock,
  Calendar,
  AlertCircle,
  Check,
  X,
  Bell,
} from 'lucide-react';
import { Medicine, Reminder } from '../../types';

export const MedicinesPage: React.FC = () => {
  const { t } = useI18n();

  const [medicines, setMedicines] = useState<Medicine[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingMed, setEditingMed] = useState<Medicine | null>(null);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  // Form State
  const [name, setName] = useState('');
  const [dosage, setDosage] = useState('');
  const [route, setRoute] = useState<'oral' | 'injection' | 'topical' | 'inhalation' | 'drops' | 'other'>('oral');
  const [frequency, setFrequency] = useState('Once daily');
  const [startDate, setStartDate] = useState(new Date().toISOString().slice(0, 10));
  const [endDate, setEndDate] = useState('');
  const [instructions, setInstructions] = useState('');

  // Reminder / Timing slots for new/edit medicine
  const [timings, setTimings] = useState<
    { id?: string; dose_label: string; dose_time: string; recurrence_type: 'daily' | 'weekday' | 'alternate' | 'prn'; advance_notification: boolean }[]
  >([{ dose_label: 'Morning', dose_time: '08:00', recurrence_type: 'daily', advance_notification: true }]);

  const addToast = (type: 'success' | 'warning' | 'error' | 'info', message: string) => {
    setToasts((prev) => [...prev, { id: Math.random().toString(36).substring(2, 9), type, message }]);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const loadMedicines = async () => {
    try {
      setLoading(true);
      const res = await api.get<Medicine[]>('/medicines/');
      if (res.success && res.data) {
        setMedicines(res.data);
      }
    } catch (err: any) {
      addToast('error', err.message || 'Failed to load medicines');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMedicines();
  }, []);

  const openAddModal = () => {
    setEditingMed(null);
    setName('');
    setDosage('');
    setRoute('oral');
    setFrequency('Once daily');
    setStartDate(new Date().toISOString().slice(0, 10));
    setEndDate('');
    setInstructions('');
    setTimings([{ dose_label: 'Morning', dose_time: '08:00', recurrence_type: 'daily', advance_notification: true }]);
    setModalOpen(true);
  };

  const openEditModal = (med: Medicine) => {
    setEditingMed(med);
    setName(med.name);
    setDosage(med.dosage);
    setRoute(med.route);
    setFrequency(med.frequency);
    setStartDate(med.start_date || new Date().toISOString().slice(0, 10));
    setEndDate(med.end_date || '');
    setInstructions(med.instructions || '');

    if (med.reminders && med.reminders.length > 0) {
      setTimings(
        med.reminders.map((r) => ({
          id: r.id,
          dose_label: r.dose_label,
          dose_time: r.dose_time_utc?.slice(0, 5) || '08:00',
          recurrence_type: r.recurrence_type,
          advance_notification: (r.advance_notification_minutes || 0) > 0,
        }))
      );
    } else {
      setTimings([{ dose_label: 'Morning', dose_time: '08:00', recurrence_type: 'daily', advance_notification: true }]);
    }
    setModalOpen(true);
  };

  const handleAddTimingRow = () => {
    setTimings((prev) => [
      ...prev,
      { dose_label: 'Evening', dose_time: '20:00', recurrence_type: 'daily', advance_notification: true },
    ]);
  };

  const handleRemoveTimingRow = (index: number) => {
    setTimings((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const medPayload = {
        name,
        dosage,
        route,
        frequency,
        start_date: startDate,
        end_date: endDate || null,
        instructions: instructions || null,
        is_active: true,
      };

      let medId = editingMed?.id;

      if (editingMed) {
        const updateRes = await api.put<Medicine>(`/medicines/${editingMed.id}`, medPayload);
        if (!updateRes.success) throw new Error('Failed to update medicine');
      } else {
        const createRes = await api.post<Medicine>('/medicines/', medPayload);
        if (!createRes.success) throw new Error('Failed to create medicine');
        medId = createRes.data.id;
      }

      // Sync Reminders / Timing slots
      if (medId) {
        for (const timing of timings) {
          const reminderPayload = {
            medicine_id: medId,
            dose_label: timing.dose_label,
            dose_time_utc: `${timing.dose_time}:00`,
            recurrence_type: timing.recurrence_type,
            advance_notification_minutes: timing.advance_notification ? 10 : 0,
            is_active: true,
          };

          if (timing.id) {
            await api.put(`/reminders/${timing.id}`, reminderPayload).catch(() => {});
          } else {
            await api.post('/reminders/', reminderPayload).catch(() => {});
          }
        }
      }

      addToast('success', editingMed ? 'Medicine updated successfully!' : 'Medicine added successfully!');
      setModalOpen(false);
      loadMedicines();
    } catch (err: any) {
      addToast('error', err.message || 'Error saving medicine');
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this medicine and its reminders?')) return;
    try {
      const res = await api.delete(`/medicines/${id}`);
      if (res.success) {
        addToast('success', 'Medicine deleted.');
        loadMedicines();
      }
    } catch (err: any) {
      addToast('error', err.message || 'Failed to delete medicine');
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <ToastContainer toasts={toasts} onDismiss={removeToast} />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-2">
            <Pill className="w-7 h-7 text-primary" />
            <span>{t('medicines.active_title')}</span>
          </h1>
          <p className="text-xs sm:text-sm text-on-surface-variant mt-1">
            Manage your daily prescriptions, dosage schedules, and reminder triggers
          </p>
        </div>

        <button
          onClick={openAddModal}
          className="btn-press inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-primary text-surface font-bold text-xs shadow-glow hover:bg-primary-container transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>{t('medicines.add_title')}</span>
        </button>
      </div>

      {/* Medicines Grid */}
      {loading ? (
        <div className="py-20 text-center space-y-3">
          <div className="w-10 h-10 border-4 border-primary/20 border-t-primary rounded-full animate-spin mx-auto" />
          <p className="text-xs text-on-surface-variant">Loading your prescriptions...</p>
        </div>
      ) : medicines.length === 0 ? (
        <GlassCard className="p-12 text-center space-y-4">
          <Pill className="w-12 h-12 text-on-surface-variant mx-auto opacity-40" />
          <h3 className="text-base font-bold text-white">{t('medicines.empty')}</h3>
          <p className="text-xs text-on-surface-variant max-w-sm mx-auto">
            Add your first medicine to configure reminders and track adherence.
          </p>
          <button
            onClick={openAddModal}
            className="btn-press inline-flex items-center space-x-2 px-4 py-2 bg-primary text-surface font-bold text-xs rounded-xl shadow-glow"
          >
            <Plus className="w-4 h-4" />
            <span>Add Medicine</span>
          </button>
        </GlassCard>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {medicines.map((med) => (
            <GlassCard key={med.id} className="p-6 flex flex-col justify-between space-y-4">
              <div>
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-xl bg-primary/15 text-primary flex items-center justify-center font-bold">
                      <Pill className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-white tracking-tight">{med.name}</h3>
                      <span className="text-xs text-primary font-semibold">{med.dosage}</span>
                    </div>
                  </div>
                  <span className="capitalize text-[11px] px-2.5 py-0.5 rounded-full bg-white/5 border border-white/10 text-on-surface-variant">
                    {med.route}
                  </span>
                </div>

                <div className="mt-4 pt-3 border-t border-white/5 space-y-2 text-xs text-on-surface-variant">
                  <div className="flex items-center justify-between">
                    <span>Frequency</span>
                    <span className="font-semibold text-white">{med.frequency}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Start Date</span>
                    <span className="text-white">{med.start_date}</span>
                  </div>
                  {med.instructions && (
                    <div className="mt-2 p-2.5 rounded-xl bg-white/5 text-[11px] text-on-surface">
                      <span className="font-semibold block text-primary/80 mb-0.5">Instructions:</span>
                      {med.instructions}
                    </div>
                  )}
                </div>

                {/* Timing / Reminders List */}
                <div className="mt-4">
                  <span className="block text-[11px] font-semibold text-on-surface-variant uppercase tracking-wider mb-2">
                    {t('timing.title')}
                  </span>
                  {med.reminders && med.reminders.length > 0 ? (
                    <div className="flex flex-wrap gap-1.5">
                      {med.reminders.map((r) => (
                        <div
                          key={r.id}
                          className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-surface-container border border-white/5 text-xs text-white"
                        >
                          <Clock className="w-3 h-3 text-secondary" />
                          <span>{r.dose_label}:</span>
                          <span className="font-mono text-primary font-semibold">
                            {r.dose_time_utc?.slice(0, 5)}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <span className="text-xs text-on-surface-variant italic">
                      No reminder slots set.
                    </span>
                  )}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-4 border-t border-white/10 flex items-center justify-end space-x-2">
                <button
                  onClick={() => openEditModal(med)}
                  className="p-2 rounded-xl text-on-surface-variant hover:text-white hover:bg-white/10 text-xs flex items-center space-x-1"
                >
                  <Edit2 className="w-3.5 h-3.5" />
                  <span>{t('btn.edit')}</span>
                </button>
                <button
                  onClick={() => handleDelete(med.id)}
                  className="p-2 rounded-xl text-status-error/80 hover:text-status-error hover:bg-status-error/10 text-xs flex items-center space-x-1"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>{t('btn.delete')}</span>
                </button>
              </div>
            </GlassCard>
          ))}
        </div>
      )}

      {/* Add / Edit Medicine Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editingMed ? 'Edit Medicine' : t('medicines.add_title')}
        maxWidth="lg"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-1">
                Medicine Name *
              </label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Lisinopril"
                className="w-full px-3 py-2 rounded-xl glass-input text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-1">
                Dosage Amount *
              </label>
              <input
                type="text"
                required
                value={dosage}
                onChange={(e) => setDosage(e.target.value)}
                placeholder="e.g. 10mg / 1 tablet"
                className="w-full px-3 py-2 rounded-xl glass-input text-sm"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-1">
                Route
              </label>
              <select
                value={route}
                onChange={(e) => setRoute(e.target.value as any)}
                className="w-full px-3 py-2 rounded-xl glass-input text-sm bg-surface-container"
              >
                <option value="oral">Oral</option>
                <option value="injection">Injection</option>
                <option value="topical">Topical</option>
                <option value="inhalation">Inhalation</option>
                <option value="drops">Drops</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-1">
                Frequency
              </label>
              <input
                type="text"
                value={frequency}
                onChange={(e) => setFrequency(e.target.value)}
                placeholder="e.g. Once daily"
                className="w-full px-3 py-2 rounded-xl glass-input text-sm"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-1">
                Start Date
              </label>
              <input
                type="date"
                required
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full px-3 py-2 rounded-xl glass-input text-sm text-white"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-1">
                End Date (Optional)
              </label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full px-3 py-2 rounded-xl glass-input text-sm text-white"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-1">
              Special Instructions
            </label>
            <textarea
              rows={2}
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              placeholder="e.g. Take with food or a glass of water"
              className="w-full px-3 py-2 rounded-xl glass-input text-sm"
            />
          </div>

          {/* Timings & Reminders Builder */}
          <div className="pt-3 border-t border-white/10 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-primary" />
                <span>{t('timing.title')}</span>
              </span>
              <button
                type="button"
                onClick={handleAddTimingRow}
                className="text-xs text-primary font-semibold hover:underline"
              >
                {t('timing.add_btn')}
              </button>
            </div>

            <div className="space-y-2">
              {timings.map((timing, idx) => (
                <div key={idx} className="p-3 rounded-xl bg-surface-container border border-white/5 space-y-2">
                  <div className="grid grid-cols-3 gap-2">
                    <input
                      type="text"
                      placeholder="Label (e.g. Morning)"
                      value={timing.dose_label}
                      onChange={(e) => {
                        const newT = [...timings];
                        newT[idx].dose_label = e.target.value;
                        setTimings(newT);
                      }}
                      className="px-2.5 py-1.5 rounded-lg glass-input text-xs"
                    />
                    <input
                      type="time"
                      value={timing.dose_time}
                      onChange={(e) => {
                        const newT = [...timings];
                        newT[idx].dose_time = e.target.value;
                        setTimings(newT);
                      }}
                      className="px-2.5 py-1.5 rounded-lg glass-input text-xs text-white"
                    />
                    <div className="flex items-center space-x-1">
                      <select
                        value={timing.recurrence_type}
                        onChange={(e) => {
                          const newT = [...timings];
                          newT[idx].recurrence_type = e.target.value as any;
                          setTimings(newT);
                        }}
                        className="w-full px-2 py-1.5 rounded-lg glass-input text-xs bg-surface-container"
                      >
                        <option value="daily">Daily</option>
                        <option value="weekday">Weekday</option>
                        <option value="alternate">Alternate</option>
                        <option value="prn">PRN</option>
                      </select>
                      {timings.length > 1 && (
                        <button
                          type="button"
                          onClick={() => handleRemoveTimingRow(idx)}
                          className="p-1.5 text-status-error hover:bg-status-error/10 rounded-lg"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </div>

                  <label className="flex items-center space-x-2 text-[11px] text-on-surface-variant cursor-pointer">
                    <input
                      type="checkbox"
                      checked={timing.advance_notification}
                      onChange={(e) => {
                        const newT = [...timings];
                        newT[idx].advance_notification = e.target.checked;
                        setTimings(newT);
                      }}
                      className="w-3.5 h-3.5 rounded border-white/20 bg-white/5 text-primary"
                    />
                    <span>10-Minute Advance Push Notification</span>
                  </label>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-4 flex items-center justify-end space-x-2">
            <button
              type="button"
              onClick={() => setModalOpen(false)}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-on-surface-variant hover:bg-white/5"
            >
              {t('btn.cancel')}
            </button>
            <button
              type="submit"
              className="btn-press px-4 py-2 rounded-xl bg-primary text-surface font-bold text-xs shadow-glow hover:bg-primary-container"
            >
              {t('btn.save')}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
