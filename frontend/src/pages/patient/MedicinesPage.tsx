import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { useI18n } from '../../lib/i18n';
import { useAuthStore } from '../../stores/authStore';
import { GlassCard } from '../../components/GlassCard';
import { Modal } from '../../components/Modal';
import { ToastMessage, ToastContainer } from '../../components/Toast';
import {
  Pill,
  Plus,
  Edit2,
  Trash2,
  Clock,
  AlertCircle,
  X,
} from 'lucide-react';
import { Medicine } from '../../types';

export const MedicinesPage: React.FC = () => {
  const { t } = useI18n();
  const { user, profile } = useAuthStore();

  const [medicines, setMedicines] = useState<Medicine[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingMed, setEditingMed] = useState<Medicine | null>(null);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const [submitting, setSubmitting] = useState(false);

  // Form State
  const [name, setName] = useState('');
  const [dosageAmount, setDosageAmount] = useState('');
  const [dosageUnit, setDosageUnit] = useState<'mg' | 'ml' | 'units'>('mg');
  const [route, setRoute] = useState<'oral' | 'topical' | 'injection' | 'inhaled' | 'other'>('oral');
  const [frequencyType, setFrequencyType] = useState<'daily' | 'weekday' | 'alternate' | 'prn'>('daily');
  const [startDate, setStartDate] = useState(new Date().toISOString().slice(0, 10));
  const [endDate, setEndDate] = useState('');
  const [instructions, setInstructions] = useState('');
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  // Reminder / Timing slots for new/edit medicine
  const [timings, setTimings] = useState<
    { id?: string; dose_label: 'morning' | 'afternoon' | 'evening' | 'night'; dose_time: string; recurrence_type: 'daily' | 'weekday' | 'alternate' | 'prn'; advance_notification: boolean }[]
  >([{ dose_label: 'morning', dose_time: '08:00', recurrence_type: 'daily', advance_notification: true }]);

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
    setDosageAmount('');
    setDosageUnit('mg');
    setRoute('oral');
    setFrequencyType('daily');
    setStartDate(new Date().toISOString().slice(0, 10));
    setEndDate('');
    setInstructions('');
    setFieldErrors({});
    setTimings([{ dose_label: 'morning', dose_time: '08:00', recurrence_type: 'daily', advance_notification: true }]);
    setModalOpen(true);
  };

  const openEditModal = (med: Medicine) => {
    setEditingMed(med);
    setName(med.name);

    // Parse dosage amount and unit
    if (med.dosage_amount !== undefined && med.dosage_amount !== null) {
      setDosageAmount(String(med.dosage_amount));
    } else if (med.dosage) {
      const match = med.dosage.match(/^([0-9.]+)\s*([a-zA-Z]+)?/);
      if (match) {
        setDosageAmount(match[1]);
        if (match[2] && ['mg', 'ml', 'units'].includes(match[2].toLowerCase())) {
          setDosageUnit(match[2].toLowerCase() as any);
        }
      } else {
        setDosageAmount(med.dosage);
      }
    } else {
      setDosageAmount('');
    }

    if (med.dosage_unit && ['mg', 'ml', 'units'].includes(med.dosage_unit)) {
      setDosageUnit(med.dosage_unit as any);
    }

    // Route normalization
    const r = (med.route || 'oral').toLowerCase();
    if (r === 'inhalation') setRoute('inhaled');
    else if (['oral', 'topical', 'injection', 'inhaled', 'other'].includes(r)) setRoute(r as any);
    else setRoute('other');

    // Frequency type normalization
    const f = (med.frequency_type || med.frequency || 'daily').toLowerCase();
    if (['daily', 'weekday', 'alternate', 'prn'].includes(f)) setFrequencyType(f as any);
    else if (f.includes('week')) setFrequencyType('weekday');
    else if (f.includes('alt')) setFrequencyType('alternate');
    else if (f.includes('prn') || f.includes('need')) setFrequencyType('prn');
    else setFrequencyType('daily');

    setStartDate(med.start_date || new Date().toISOString().slice(0, 10));
    setEndDate(med.end_date || '');
    setInstructions(med.instructions || '');
    setFieldErrors({});

    if (med.reminders && med.reminders.length > 0) {
      setTimings(
        med.reminders.map((r) => {
          let dl: 'morning' | 'afternoon' | 'evening' | 'night' = 'morning';
          const lowerDl = (r.dose_label || '').toLowerCase();
          if (['morning', 'afternoon', 'evening', 'night'].includes(lowerDl)) {
            dl = lowerDl as any;
          }
          return {
            id: r.id,
            dose_label: dl,
            dose_time: r.dose_time_utc ? r.dose_time_utc.slice(0, 5) : '08:00',
            recurrence_type: r.recurrence_type || 'daily',
            advance_notification: r.advance_notify ?? ((r.advance_notification_minutes || 0) > 0),
          };
        })
      );
    } else {
      setTimings([{ dose_label: 'morning', dose_time: '08:00', recurrence_type: 'daily', advance_notification: true }]);
    }
    setModalOpen(true);
  };

  const handleAddTimingRow = () => {
    setTimings((prev) => [
      ...prev,
      { dose_label: 'evening', dose_time: '20:00', recurrence_type: frequencyType, advance_notification: true },
    ]);
  };

  const handleRemoveTimingRow = (index: number) => {
    setTimings((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFieldErrors({});

    // Client-side validation
    const errors: Record<string, string> = {};
    if (!name.trim()) {
      errors.name = 'Medicine name is required';
    }
    const dNum = parseFloat(dosageAmount);
    if (!dosageAmount || isNaN(dNum) || dNum <= 0) {
      errors.dosage_amount = 'Dosage amount must be a positive number';
    } else if (dNum > 9999.99) {
      errors.dosage_amount = 'Dosage amount cannot exceed 9999.99';
    }
    if (!dosageUnit) {
      errors.dosage_unit = 'Dosage unit is required';
    }
    if (!route) {
      errors.route = 'Route is required';
    }
    if (!frequencyType) {
      errors.frequency_type = 'Frequency type is required';
    }
    if (!startDate) {
      errors.start_date = 'Start date is required';
    }
    if (endDate && startDate && endDate < startDate) {
      errors.end_date = 'End date must be on or after start date';
    }

    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      const firstError = Object.values(errors)[0];
      addToast('error', firstError);
      return;
    }

    try {
      setSubmitting(true);
      const medPayload = {
        name: name.trim(),
        dosage_amount: parseFloat(dosageAmount),
        dosage_unit: dosageUnit,
        route,
        frequency_type: frequencyType,
        start_date: startDate,
        end_date: endDate || null,
        instructions: instructions.trim() || null,
        is_active: true,
      };

      let medId = editingMed?.id;

      if (editingMed) {
        const updateRes = await api.patch<Medicine>(`/medicines/${editingMed.id}`, medPayload);
        if (!updateRes.success) throw new Error('Failed to update medicine');
      } else {
        const createRes = await api.post<Medicine>('/medicines/', medPayload);
        if (!createRes.success) throw new Error('Failed to create medicine');
        medId = createRes.data.id;
      }

      // Sync Reminders / Timing slots
      const userTimezone = profile?.timezone || user?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
      if (medId && timings.length > 0) {
        for (const timing of timings) {
          const reminderPayload = {
            dose_label: timing.dose_label.toLowerCase(),
            dose_time_utc: timing.dose_time.length === 5 ? `${timing.dose_time}:00` : timing.dose_time,
            timezone: userTimezone,
            recurrence_type: timing.recurrence_type || frequencyType,
            advance_notify: timing.advance_notification,
            is_active: true,
          };

          if (timing.id) {
            await api.patch(`/reminders/${timing.id}`, reminderPayload).catch((err) => {
              console.warn('Failed to update reminder:', err);
            });
          } else {
            await api.post(`/medicines/${medId}/reminders`, reminderPayload).catch((err) => {
              console.warn('Failed to create reminder:', err);
            });
          }
        }
      }

      addToast('success', editingMed ? 'Medicine updated successfully!' : 'Medicine added successfully!');
      setModalOpen(false);
      setFieldErrors({});
      loadMedicines();
    } catch (err: any) {
      const backendErrors: Record<string, string> = {};
      if (err.details && Array.isArray(err.details)) {
        err.details.forEach((d: any) => {
          if (d.field) backendErrors[d.field] = d.message;
        });
      } else if (err.field) {
        backendErrors[err.field] = err.message;
      }
      setFieldErrors(backendErrors);
      addToast('error', err.message || 'Error saving medicine');
    } finally {
      setSubmitting(false);
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
                      <span className="text-xs text-primary font-semibold">
                        {med.dosage_amount !== undefined && med.dosage_unit
                          ? `${med.dosage_amount} ${med.dosage_unit}`
                          : med.dosage || 'Prescribed'}
                      </span>
                    </div>
                  </div>
                  <span className="capitalize text-[11px] px-2.5 py-0.5 rounded-full bg-white/5 border border-white/10 text-on-surface-variant">
                    {med.route}
                  </span>
                </div>

                <div className="mt-4 pt-3 border-t border-white/5 space-y-2 text-xs text-on-surface-variant">
                  <div className="flex items-center justify-between">
                    <span>Frequency</span>
                    <span className="font-semibold text-white capitalize">{med.frequency_type || med.frequency || 'Daily'}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Start Date</span>
                    <span className="text-white">{med.start_date}</span>
                  </div>
                  {med.end_date && (
                    <div className="flex items-center justify-between">
                      <span>End Date</span>
                      <span className="text-white">{med.end_date}</span>
                    </div>
                  )}
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
                          <span className="capitalize">{r.dose_label}:</span>
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
          {/* Error Summary Banner */}
          {Object.keys(fieldErrors).length > 0 && (
            <div className="p-3 rounded-xl bg-status-error/15 border border-status-error/30 text-xs text-status-error space-y-1">
              <div className="font-bold flex items-center gap-1.5">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>Please fix the following error{Object.keys(fieldErrors).length > 1 ? 's' : ''}:</span>
              </div>
              <ul className="list-disc list-inside space-y-0.5 pl-1">
                {Object.entries(fieldErrors).map(([f, msg]) => (
                  <li key={f}>
                    <span className="font-semibold capitalize">{f.replace('_', ' ')}:</span> {msg}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label htmlFor="med-name" className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-1">
                Medicine Name *
              </label>
              <input
                id="med-name"
                name="name"
                type="text"
                required
                value={name}
                onChange={(e) => {
                  setName(e.target.value);
                  if (fieldErrors.name) setFieldErrors((prev) => ({ ...prev, name: '' }));
                }}
                placeholder="e.g. Lisinopril"
                className={`w-full px-3 py-2 rounded-xl glass-input text-sm ${
                  fieldErrors.name ? 'border-status-error focus:ring-status-error' : ''
                }`}
              />
              {fieldErrors.name && (
                <p className="text-xs text-status-error mt-1 flex items-center gap-1">
                  <AlertCircle className="w-3.5 h-3.5" />
                  <span>{fieldErrors.name}</span>
                </p>
              )}
            </div>

            <div>
              <label htmlFor="med-dosage-amount" className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-1">
                Dosage *
              </label>
              <div className="flex gap-2">
                <input
                  id="med-dosage-amount"
                  name="dosage_amount"
                  type="number"
                  step="any"
                  min="0.01"
                  required
                  value={dosageAmount}
                  onChange={(e) => {
                    setDosageAmount(e.target.value);
                    if (fieldErrors.dosage_amount) setFieldErrors((prev) => ({ ...prev, dosage_amount: '' }));
                  }}
                  placeholder="e.g. 10"
                  className={`w-2/3 px-3 py-2 rounded-xl glass-input text-sm ${
                    fieldErrors.dosage_amount ? 'border-status-error focus:ring-status-error' : ''
                  }`}
                />
                <select
                  id="med-dosage-unit"
                  name="dosage_unit"
                  value={dosageUnit}
                  onChange={(e) => {
                    setDosageUnit(e.target.value as any);
                    if (fieldErrors.dosage_unit) setFieldErrors((prev) => ({ ...prev, dosage_unit: '' }));
                  }}
                  className="w-1/3 px-3 py-2 rounded-xl glass-input text-sm bg-surface-container"
                >
                  <option value="mg">mg</option>
                  <option value="ml">ml</option>
                  <option value="units">units</option>
                </select>
              </div>
              {fieldErrors.dosage_amount && (
                <p className="text-xs text-status-error mt-1 flex items-center gap-1">
                  <AlertCircle className="w-3.5 h-3.5" />
                  <span>{fieldErrors.dosage_amount}</span>
                </p>
              )}
              {fieldErrors.dosage_unit && (
                <p className="text-xs text-status-error mt-1 flex items-center gap-1">
                  <AlertCircle className="w-3.5 h-3.5" />
                  <span>{fieldErrors.dosage_unit}</span>
                </p>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label htmlFor="med-route" className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-1">
                Route *
              </label>
              <select
                id="med-route"
                name="route"
                value={route}
                onChange={(e) => {
                  setRoute(e.target.value as any);
                  if (fieldErrors.route) setFieldErrors((prev) => ({ ...prev, route: '' }));
                }}
                className={`w-full px-3 py-2 rounded-xl glass-input text-sm bg-surface-container ${
                  fieldErrors.route ? 'border-status-error focus:ring-status-error' : ''
                }`}
              >
                <option value="oral">Oral</option>
                <option value="topical">Topical</option>
                <option value="injection">Injection</option>
                <option value="inhaled">Inhaled</option>
                <option value="other">Other</option>
              </select>
              {fieldErrors.route && (
                <p className="text-xs text-status-error mt-1 flex items-center gap-1">
                  <AlertCircle className="w-3.5 h-3.5" />
                  <span>{fieldErrors.route}</span>
                </p>
              )}
            </div>

            <div>
              <label htmlFor="med-frequency" className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-1">
                Frequency *
              </label>
              <select
                id="med-frequency"
                name="frequency_type"
                value={frequencyType}
                onChange={(e) => {
                  setFrequencyType(e.target.value as any);
                  if (fieldErrors.frequency_type) setFieldErrors((prev) => ({ ...prev, frequency_type: '' }));
                }}
                className={`w-full px-3 py-2 rounded-xl glass-input text-sm bg-surface-container ${
                  fieldErrors.frequency_type ? 'border-status-error focus:ring-status-error' : ''
                }`}
              >
                <option value="daily">Daily</option>
                <option value="weekday">Weekday (Mon–Fri)</option>
                <option value="alternate">Alternate Days</option>
                <option value="prn">PRN (As Needed)</option>
              </select>
              {fieldErrors.frequency_type && (
                <p className="text-xs text-status-error mt-1 flex items-center gap-1">
                  <AlertCircle className="w-3.5 h-3.5" />
                  <span>{fieldErrors.frequency_type}</span>
                </p>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label htmlFor="med-start-date" className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-1">
                Start Date *
              </label>
              <input
                id="med-start-date"
                name="startDate"
                type="date"
                required
                value={startDate}
                onChange={(e) => {
                  setStartDate(e.target.value);
                  if (fieldErrors.start_date) setFieldErrors((prev) => ({ ...prev, start_date: '' }));
                }}
                className={`w-full px-3 py-2 rounded-xl glass-input text-sm text-white ${
                  fieldErrors.start_date ? 'border-status-error focus:ring-status-error' : ''
                }`}
              />
              {fieldErrors.start_date && (
                <p className="text-xs text-status-error mt-1 flex items-center gap-1">
                  <AlertCircle className="w-3.5 h-3.5" />
                  <span>{fieldErrors.start_date}</span>
                </p>
              )}
            </div>

            <div>
              <label htmlFor="med-end-date" className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-1">
                End Date (Optional)
              </label>
              <input
                id="med-end-date"
                name="endDate"
                type="date"
                value={endDate}
                onChange={(e) => {
                  setEndDate(e.target.value);
                  if (fieldErrors.end_date) setFieldErrors((prev) => ({ ...prev, end_date: '' }));
                }}
                className={`w-full px-3 py-2 rounded-xl glass-input text-sm text-white ${
                  fieldErrors.end_date ? 'border-status-error focus:ring-status-error' : ''
                }`}
              />
              {fieldErrors.end_date && (
                <p className="text-xs text-status-error mt-1 flex items-center gap-1">
                  <AlertCircle className="w-3.5 h-3.5" />
                  <span>{fieldErrors.end_date}</span>
                </p>
              )}
            </div>
          </div>

          <div>
            <label htmlFor="med-instructions" className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-1">
              Special Instructions
            </label>
            <textarea
              id="med-instructions"
              name="instructions"
              rows={2}
              value={instructions}
              onChange={(e) => {
                setInstructions(e.target.value);
                if (fieldErrors.instructions) setFieldErrors((prev) => ({ ...prev, instructions: '' }));
              }}
              placeholder="e.g. Take with food or a glass of water"
              className="w-full px-3 py-2 rounded-xl glass-input text-sm"
            />
            {fieldErrors.instructions && (
              <p className="text-xs text-status-error mt-1 flex items-center gap-1">
                <AlertCircle className="w-3.5 h-3.5" />
                <span>{fieldErrors.instructions}</span>
              </p>
            )}
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
                    <select
                      id={`timing-label-${idx}`}
                      name={`timing_label_${idx}`}
                      value={timing.dose_label.toLowerCase()}
                      onChange={(e) => {
                        const newT = [...timings];
                        newT[idx].dose_label = e.target.value as any;
                        setTimings(newT);
                      }}
                      className="px-2.5 py-1.5 rounded-lg glass-input text-xs bg-surface-container capitalize"
                    >
                      <option value="morning">Morning</option>
                      <option value="afternoon">Afternoon</option>
                      <option value="evening">Evening</option>
                      <option value="night">Night</option>
                    </select>

                    <input
                      id={`timing-time-${idx}`}
                      name={`timing_time_${idx}`}
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
                        id={`timing-recurrence-${idx}`}
                        name={`timing_recurrence_${idx}`}
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

                  <label htmlFor={`timing-advance-${idx}`} className="flex items-center space-x-2 text-[11px] text-on-surface-variant cursor-pointer">
                    <input
                      id={`timing-advance-${idx}`}
                      name={`timing_advance_${idx}`}
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
              disabled={submitting}
              className="btn-press px-4 py-2 rounded-xl bg-primary text-surface font-bold text-xs shadow-glow hover:bg-primary-container disabled:opacity-50"
            >
              {submitting ? 'Saving...' : t('btn.save')}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
