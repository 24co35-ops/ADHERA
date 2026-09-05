import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { fetchConfig, config } from '../../lib/config';
import { useAuthStore } from '../../stores/authStore';
import { GlassCard } from '../../components/GlassCard';
import { ToastMessage, ToastContainer } from '../../components/Toast';
import { Modal } from '../../components/Modal';
import {
  User as UserIcon,
  Mail,
  Calendar,
  Heart,
  Globe,
  Bell,
  BellOff,
  Shield,
  Stethoscope,
  Plus,
  Trash2,
  Download,
  Save,
  CheckCircle2,
  Search,
} from 'lucide-react';
import { Profile, EmergencyContact, MyProviderResponse } from '../../types';

export const ProfilePage: React.FC = () => {
  const { user, profile, setProfile } = useAuthStore();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  // Form Fields
  const [fullName, setFullName] = useState('');
  const [bloodGroup, setBloodGroup] = useState('');
  const [dateOfBirth, setDateOfBirth] = useState('');
  const [timezoneStr, setTimezoneStr] = useState('');
  const [allergies, setAllergies] = useState<string[]>([]);
  const [allergyInput, setAllergyInput] = useState('');
  const [conditions, setConditions] = useState<string[]>([]);
  const [conditionInput, setConditionInput] = useState('');

  // Emergency Contacts
  const [contacts, setContacts] = useState<EmergencyContact[]>([]);
  const [contactName, setContactName] = useState('');
  const [contactPhone, setContactPhone] = useState('');
  const [contactEmail, setContactEmail] = useState('');
  const [contactRel, setContactRel] = useState('');
  const [contactModalOpen, setContactModalOpen] = useState(false);

  // Provider Assignment
  const [assignment, setAssignment] = useState<MyProviderResponse | null>(null);
  const [searchProviderQuery, setSearchProviderQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const [providerModalOpen, setProviderModalOpen] = useState(false);

  // Web Push
  const [pushSubscribed, setPushSubscribed] = useState(false);
  const [pushLoading, setPushLoading] = useState(false);

  const addToast = (type: 'success' | 'warning' | 'error' | 'info', message: string) => {
    setToasts((prev) => [...prev, { id: Math.random().toString(36).substring(2, 9), type, message }]);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const loadProfileData = async () => {
    try {
      setLoading(true);
      const [profRes, assignRes] = await Promise.all([
        api.get<Profile>('/profile/'),
        api.get<MyProviderResponse>('/assignments/my-provider'),
      ]);

      if (profRes.success && profRes.data) {
        const d = profRes.data;
        setProfile(d);
        setFullName(d.full_name || '');
        setBloodGroup(d.blood_group || '');
        setDateOfBirth(d.date_of_birth || '');
        setTimezoneStr(d.timezone || 'UTC');
        setAllergies(d.allergies || []);
        setConditions(d.medical_conditions || []);
        setContacts(d.emergency_contacts || []);
      }

      if (assignRes.success && assignRes.data) {
        setAssignment(assignRes.data);
      }

      // Check Push Subscription Status
      if ('serviceWorker' in navigator && 'PushManager' in window) {
        const reg = await navigator.serviceWorker.ready;
        const sub = await reg.pushManager.getSubscription();
        setPushSubscribed(!!sub);
      }
    } catch (err: any) {
      addToast('error', err.message || 'Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProfileData();
  }, []);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      const payload = {
        full_name: fullName,
        blood_group: bloodGroup || null,
        date_of_birth: dateOfBirth || null,
        timezone: timezoneStr,
        allergies,
        medical_conditions: conditions,
      };

      const res = await api.put<Profile>('/profile/', payload);
      if (res.success && res.data) {
        setProfile(res.data);
        addToast('success', 'Profile updated successfully!');
      }
    } catch (err: any) {
      addToast('error', err.message || 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const handleAddAllergy = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && allergyInput.trim()) {
      e.preventDefault();
      if (!allergies.includes(allergyInput.trim())) {
        setAllergies([...allergies, allergyInput.trim()]);
      }
      setAllergyInput('');
    }
  };

  const handleAddCondition = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && conditionInput.trim()) {
      e.preventDefault();
      if (!conditions.includes(conditionInput.trim())) {
        setConditions([...conditions, conditionInput.trim()]);
      }
      setConditionInput('');
    }
  };

  const handleAddContact = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        name: contactName,
        phone: contactPhone,
        email: contactEmail || null,
        relationship: contactRel || null,
      };

      const res = await api.post<any>('/profile/emergency-contact', payload);
      if (res.success) {
        addToast('success', 'Emergency contact saved!');
        setContactModalOpen(false);
        setContactName('');
        setContactPhone('');
        setContactEmail('');
        setContactRel('');
        loadProfileData();
      }
    } catch (err: any) {
      addToast('error', err.message || 'Failed to add emergency contact');
    }
  };

  const handleDeleteContact = async () => {
    try {
      const res = await api.delete('/profile/emergency-contact');
      if (res.success) {
        addToast('success', 'Emergency contact removed.');
        loadProfileData();
      }
    } catch (err: any) {
      addToast('error', err.message || 'Failed to delete emergency contact');
    }
  };

  const togglePushSubscription = async () => {
    try {
      setPushLoading(true);
      if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        addToast('warning', 'Push notifications not supported on this browser.');
        return;
      }

      await fetchConfig();
      const vapidKey = config.VAPID_PUBLIC_KEY;
      const reg = await navigator.serviceWorker.ready;

      if (pushSubscribed) {
        const sub = await reg.pushManager.getSubscription();
        if (sub) await sub.unsubscribe();
        await api.delete('/profile/push-subscription');
        setPushSubscribed(false);
        addToast('info', 'Push notifications disabled.');
      } else {
        const permission = await Notification.requestPermission();
        if (permission !== 'granted') {
          addToast('warning', 'Notification permission was denied.');
          return;
        }

        const sub = await reg.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: vapidKey,
        });

        const subObj = sub.toJSON();
        await api.post('/profile/push-subscription', subObj);
        setPushSubscribed(true);
        addToast('success', 'Push notifications successfully activated!');
      }
    } catch (err: any) {
      addToast('error', err.message || 'Failed to update push subscription');
    } finally {
      setPushLoading(false);
    }
  };

  const handleSearchProviders = async () => {
    try {
      setSearching(true);
      const res = await api.get<any[]>(`/assignments/search-providers?query=${encodeURIComponent(searchProviderQuery)}`);
      if (res.success && res.data) {
        setSearchResults(res.data);
      }
    } catch (err: any) {
      addToast('error', err.message || 'Search failed');
    } finally {
      setSearching(false);
    }
  };

  const handleRequestProvider = async (providerId: string) => {
    try {
      const res = await api.post('/assignments/request', { provider_id: providerId });
      if (res.success) {
        addToast('success', 'Assignment request sent to provider!');
        setProviderModalOpen(false);
        loadProfileData();
      }
    } catch (err: any) {
      addToast('error', err.message || 'Failed to request provider');
    }
  };

  const handleCancelRequest = async () => {
    try {
      const res = await api.delete('/assignments/request');
      if (res.success) {
        addToast('info', 'Provider request cancelled.');
        loadProfileData();
      }
    } catch (err: any) {
      addToast('error', err.message || 'Failed to cancel request');
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <ToastContainer toasts={toasts} onDismiss={removeToast} />

      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-2">
          <UserIcon className="w-7 h-7 text-primary" />
          <span>Patient Profile & Settings</span>
        </h1>
        <p className="text-xs sm:text-sm text-on-surface-variant mt-1">
          Personal medical info, emergency contacts, provider link, and alerts
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left 2 Cols: Profile Form */}
        <div className="lg:col-span-2 space-y-6">
          <GlassCard className="p-6">
            <h3 className="text-base font-bold text-white pb-3 border-b border-white/10 mb-4">
              Personal Information
            </h3>

            <form onSubmit={handleSaveProfile} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-1">
                    Full Name
                  </label>
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl glass-input text-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-1">
                    Email Address
                  </label>
                  <input
                    type="email"
                    disabled
                    value={user?.email || ''}
                    className="w-full px-3 py-2 rounded-xl glass-input text-sm opacity-60 cursor-not-allowed"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-1">
                    Date of Birth
                  </label>
                  <input
                    type="date"
                    value={dateOfBirth}
                    onChange={(e) => setDateOfBirth(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl glass-input text-sm text-white"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-1">
                    Blood Group
                  </label>
                  <select
                    value={bloodGroup}
                    onChange={(e) => setBloodGroup(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl glass-input text-sm bg-surface-container"
                  >
                    <option value="">Select</option>
                    <option value="A+">A+</option>
                    <option value="A-">A-</option>
                    <option value="B+">B+</option>
                    <option value="B-">B-</option>
                    <option value="AB+">AB+</option>
                    <option value="AB-">AB-</option>
                    <option value="O+">O+</option>
                    <option value="O-">O-</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-1">
                    Timezone
                  </label>
                  <input
                    type="text"
                    value={timezoneStr}
                    onChange={(e) => setTimezoneStr(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl glass-input text-sm font-mono text-xs"
                  />
                </div>
              </div>

              {/* Known Allergies Tag Input */}
              <div>
                <label className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-1">
                  Known Allergies (Press Enter to add)
                </label>
                <div className="flex flex-wrap gap-1.5 mb-2">
                  {allergies.map((all, i) => (
                    <span
                      key={i}
                      className="px-2.5 py-1 rounded-lg bg-status-error/15 text-status-error text-xs flex items-center gap-1 border border-status-error/20"
                    >
                      <span>{all}</span>
                      <button
                        type="button"
                        onClick={() => setAllergies(allergies.filter((_, idx) => idx !== i))}
                        className="hover:text-white"
                      >
                        &times;
                      </button>
                    </span>
                  ))}
                </div>
                <input
                  type="text"
                  placeholder="e.g. Penicillin, Peanuts"
                  value={allergyInput}
                  onChange={(e) => setAllergyInput(e.target.value)}
                  onKeyDown={handleAddAllergy}
                  className="w-full px-3 py-2 rounded-xl glass-input text-sm"
                />
              </div>

              {/* Medical Conditions Tag Input */}
              <div>
                <label className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-1">
                  Medical Conditions (Press Enter to add)
                </label>
                <div className="flex flex-wrap gap-1.5 mb-2">
                  {conditions.map((cond, i) => (
                    <span
                      key={i}
                      className="px-2.5 py-1 rounded-lg bg-primary/15 text-primary text-xs flex items-center gap-1 border border-primary/20"
                    >
                      <span>{cond}</span>
                      <button
                        type="button"
                        onClick={() => setConditions(conditions.filter((_, idx) => idx !== i))}
                        className="hover:text-white"
                      >
                        &times;
                      </button>
                    </span>
                  ))}
                </div>
                <input
                  type="text"
                  placeholder="e.g. Hypertension, Type 2 Diabetes"
                  value={conditionInput}
                  onChange={(e) => setConditionInput(e.target.value)}
                  onKeyDown={handleAddCondition}
                  className="w-full px-3 py-2 rounded-xl glass-input text-sm"
                />
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  type="submit"
                  disabled={saving}
                  className="btn-press inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-primary text-surface font-bold text-xs shadow-glow hover:bg-primary-container disabled:opacity-50"
                >
                  <Save className="w-4 h-4" />
                  <span>{saving ? 'Saving...' : 'Save Profile Changes'}</span>
                </button>
              </div>
            </form>
          </GlassCard>

          {/* Emergency Contacts Section */}
          <GlassCard className="p-6">
            <div className="flex items-center justify-between pb-3 border-b border-white/10 mb-4">
              <div>
                <h3 className="text-base font-bold text-white">Emergency Contacts</h3>
                <p className="text-xs text-on-surface-variant">
                  Notified automatically in case of Level 4 emergency side effects
                </p>
              </div>
              <button
                onClick={() => setContactModalOpen(true)}
                className="btn-press inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-xs font-semibold text-primary"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Contact</span>
              </button>
            </div>

            {contacts.length === 0 ? (
              <p className="text-xs text-on-surface-variant py-4 text-center">
                No emergency contacts configured yet.
              </p>
            ) : (
              <div className="space-y-3">
                {contacts.map((c, i) => (
                  <div
                    key={i}
                    className="p-3.5 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-between text-xs"
                  >
                    <div>
                      <span className="font-bold text-white text-sm block">{c.name}</span>
                      <div className="text-on-surface-variant flex items-center space-x-3 mt-0.5">
                        <span>{c.phone}</span>
                        {c.email && <span>&bull; {c.email}</span>}
                        {c.relationship && <span>&bull; {c.relationship}</span>}
                      </div>
                    </div>
                    <button
                      onClick={handleDeleteContact}
                      className="p-1.5 text-status-error/80 hover:text-status-error rounded-lg"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </GlassCard>
        </div>

        {/* Right 1 Col: Provider & Push Notifications */}
        <div className="space-y-6">
          {/* Push Notification Toggle */}
          <GlassCard className="p-6">
            <div className="flex items-center space-x-3 pb-3 border-b border-white/10 mb-4">
              <div className="p-2 rounded-xl bg-primary/10 text-primary">
                <Bell className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Push Notifications</h3>
                <p className="text-xs text-on-surface-variant">10m advance dose alerts</p>
              </div>
            </div>

            <div className="flex items-center justify-between py-2">
              <div className="space-y-1">
                <span className="text-xs font-semibold text-white block">
                  {pushSubscribed ? 'Alerts Active' : 'Alerts Disabled'}
                </span>
                <span className="text-[11px] text-on-surface-variant block">
                  {pushSubscribed
                    ? 'Receiving reminders on this device'
                    : 'Enable to receive dose reminders'}
                </span>
              </div>
              <button
                onClick={togglePushSubscription}
                disabled={pushLoading}
                className={`btn-press px-3 py-1.5 rounded-xl font-bold text-xs transition-colors ${
                  pushSubscribed
                    ? 'bg-status-success/20 text-status-success border border-status-success/40'
                    : 'bg-primary text-surface shadow-glow'
                }`}
              >
                {pushLoading ? '...' : pushSubscribed ? 'Subscribed' : 'Enable'}
              </button>
            </div>
          </GlassCard>

          {/* Assigned Provider Details */}
          <GlassCard className="p-6">
            <div className="flex items-center space-x-3 pb-3 border-b border-white/10 mb-4">
              <div className="p-2 rounded-xl bg-secondary/10 text-secondary">
                <Stethoscope className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Care Provider</h3>
                <p className="text-xs text-on-surface-variant">Connected doctor</p>
              </div>
            </div>

            {assignment?.assigned && assignment.data?.profiles ? (
              <div className="space-y-3 text-xs">
                <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                  <span className="text-[10px] uppercase font-bold text-status-success tracking-wider block">
                    Connected Doctor
                  </span>
                  <span className="font-bold text-sm text-white block mt-1">
                    {assignment.data.profiles.full_name}
                  </span>
                  <span className="text-on-surface-variant block mt-0.5">
                    {assignment.data.profiles.email || 'Email on file'}
                  </span>
                </div>
              </div>
            ) : (
              <div className="text-center py-4 space-y-3">
                <p className="text-xs text-on-surface-variant">
                  You are not assigned to a healthcare provider.
                </p>
                <button
                  onClick={() => {
                    setProviderModalOpen(true);
                    handleSearchProviders();
                  }}
                  className="btn-press px-3.5 py-2 rounded-xl bg-white/10 hover:bg-white/15 text-white font-semibold text-xs border border-white/10"
                >
                  Search & Connect Doctor
                </button>
              </div>
            )}
          </GlassCard>
        </div>
      </div>

      {/* Add Emergency Contact Modal */}
      <Modal
        isOpen={contactModalOpen}
        onClose={() => setContactModalOpen(false)}
        title="Add Emergency Contact"
      >
        <form onSubmit={handleAddContact} className="space-y-4 text-xs">
          <div>
            <label className="block font-semibold text-on-surface uppercase tracking-wider mb-1">
              Contact Full Name *
            </label>
            <input
              type="text"
              required
              value={contactName}
              onChange={(e) => setContactName(e.target.value)}
              placeholder="e.g. John Doe"
              className="w-full px-3 py-2 rounded-xl glass-input text-sm"
            />
          </div>

          <div>
            <label className="block font-semibold text-on-surface uppercase tracking-wider mb-1">
              Phone Number *
            </label>
            <input
              type="tel"
              required
              value={contactPhone}
              onChange={(e) => setContactPhone(e.target.value)}
              placeholder="+1 (555) 000-0000"
              className="w-full px-3 py-2 rounded-xl glass-input text-sm"
            />
          </div>

          <div>
            <label className="block font-semibold text-on-surface uppercase tracking-wider mb-1">
              Email Address (Optional)
            </label>
            <input
              type="email"
              value={contactEmail}
              onChange={(e) => setContactEmail(e.target.value)}
              placeholder="contact@example.com"
              className="w-full px-3 py-2 rounded-xl glass-input text-sm"
            />
          </div>

          <div>
            <label className="block font-semibold text-on-surface uppercase tracking-wider mb-1">
              Relationship (Optional)
            </label>
            <input
              type="text"
              value={contactRel}
              onChange={(e) => setContactRel(e.target.value)}
              placeholder="e.g. Spouse, Sibling, Caregiver"
              className="w-full px-3 py-2 rounded-xl glass-input text-sm"
            />
          </div>

          <div className="pt-3 flex justify-end space-x-2">
            <button
              type="button"
              onClick={() => setContactModalOpen(false)}
              className="px-3 py-2 rounded-xl text-on-surface-variant hover:bg-white/5"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-press px-4 py-2 bg-primary text-surface font-bold rounded-xl shadow-glow"
            >
              Save Contact
            </button>
          </div>
        </form>
      </Modal>

      {/* Connect Provider Modal */}
      <Modal
        isOpen={providerModalOpen}
        onClose={() => setProviderModalOpen(false)}
        title="Find Healthcare Provider"
        maxWidth="lg"
      >
        <div className="space-y-4">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3 top-3 text-on-surface-variant" />
              <input
                type="text"
                value={searchProviderQuery}
                onChange={(e) => setSearchProviderQuery(e.target.value)}
                placeholder="Search provider by name..."
                className="w-full pl-9 pr-3 py-2 rounded-xl glass-input text-xs"
              />
            </div>
            <button
              type="button"
              onClick={handleSearchProviders}
              className="px-3 py-2 rounded-xl bg-white/10 hover:bg-white/15 text-xs font-semibold text-white"
            >
              Search
            </button>
          </div>

          <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
            {searching ? (
              <p className="text-xs text-on-surface-variant text-center py-4">Searching providers...</p>
            ) : searchResults.length === 0 ? (
              <p className="text-xs text-on-surface-variant text-center py-4">No verified providers found.</p>
            ) : (
              searchResults.map((p) => (
                <div
                  key={p.id}
                  className="p-3 rounded-xl bg-white/5 border border-white/5 flex items-center justify-between text-xs"
                >
                  <div>
                    <span className="font-bold text-white block">{p.full_name}</span>
                    <span className="text-on-surface-variant text-[11px] block">{p.email}</span>
                  </div>
                  <button
                    onClick={() => handleRequestProvider(p.id)}
                    className="btn-press px-3 py-1.5 rounded-lg bg-primary text-surface font-bold text-xs shadow-glow"
                  >
                    Request Care
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </Modal>
    </div>
  );
};
