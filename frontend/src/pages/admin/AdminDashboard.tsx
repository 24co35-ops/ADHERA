import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { GlassCard } from '../../components/GlassCard';
import { ToastMessage, ToastContainer } from '../../components/Toast';
import { Modal } from '../../components/Modal';
import {
  ShieldCheck,
  Users,
  UserCheck,
  Stethoscope,
  Activity,
  Search,
  Check,
  X,
  Plus,
  Server,
  FileText,
  UserX,
  TrendingUp,
  AlertTriangle,
} from 'lucide-react';
import { Profile, UserRole } from '../../types';

export const AdminDashboard: React.FC = () => {
  const [users, setUsers] = useState<Profile[]>([]);
  const [pendingProviders, setPendingProviders] = useState<Profile[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [healthStatus, setHealthStatus] = useState<any>(null);
  const [platformStats, setPlatformStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [roleFilter, setRoleFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  // Manual Assignment Modal
  const [assignModalOpen, setAssignModalOpen] = useState(false);
  const [selectedPatientId, setSelectedPatientId] = useState('');
  const [selectedProviderId, setSelectedProviderId] = useState('');

  const addToast = (type: 'success' | 'warning' | 'error' | 'info', message: string) => {
    setToasts((prev) => [...prev, { id: Math.random().toString(36).substring(2, 9), type, message }]);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const loadAdminData = async () => {
    try {
      setLoading(true);
      const [usersRes, providersRes, healthRes, statsRes, auditRes] = await Promise.allSettled([
        api.get<Profile[]>('/admin/users'),
        api.get<Profile[]>('/admin/pending-providers'),
        api.get<any>('/health'),
        api.get<any>('/analytics/dashboard'),
        api.get<any[]>('/admin/audit-logs'),
      ]);

      if (usersRes.status === 'fulfilled' && usersRes.value.success) {
        setUsers(usersRes.value.data);
      }
      if (providersRes.status === 'fulfilled' && providersRes.value.success) {
        setPendingProviders(providersRes.value.data);
      }
      if (healthRes.status === 'fulfilled' && healthRes.value.success) {
        setHealthStatus(healthRes.value.data);
      }
      if (statsRes.status === 'fulfilled' && statsRes.value.success) {
        setPlatformStats(statsRes.value.data);
      }
      if (auditRes.status === 'fulfilled' && auditRes.value.success) {
        setAuditLogs(auditRes.value.data);
      }
    } catch (err: any) {
      addToast('error', err.message || 'Failed to load admin console data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAdminData();
  }, []);

  const handleToggleUserStatus = async (userId: string, currentStatus: boolean) => {
    try {
      const res = await api.put(`/admin/users/${userId}/status`, { is_active: !currentStatus });
      if (res.success) {
        addToast('success', `User status updated to ${!currentStatus ? 'Active' : 'Suspended'}`);
        loadAdminData();
      }
    } catch (err: any) {
      addToast('error', err.message || 'Failed to update user status');
    }
  };

  const handleApproveProvider = async (providerId: string) => {
    try {
      const res = await api.post(`/admin/providers/${providerId}/approve`);
      if (res.success) {
        addToast('success', 'Healthcare provider approved!');
        loadAdminData();
      }
    } catch (err: any) {
      addToast('error', err.message || 'Approval failed');
    }
  };

  const handleRejectProvider = async (providerId: string) => {
    try {
      const res = await api.post(`/admin/providers/${providerId}/reject`);
      if (res.success) {
        addToast('info', 'Provider application rejected.');
        loadAdminData();
      }
    } catch (err: any) {
      addToast('error', err.message || 'Action failed');
    }
  };

  const handleCreateAssignment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPatientId || !selectedProviderId) {
      addToast('warning', 'Select both patient and provider.');
      return;
    }

    try {
      const res = await api.post('/admin/assignments', {
        patient_id: selectedPatientId,
        provider_id: selectedProviderId,
      });
      if (res.success) {
        addToast('success', 'Patient assigned to provider successfully!');
        setAssignModalOpen(false);
        loadAdminData();
      }
    } catch (err: any) {
      addToast('error', err.message || 'Assignment failed');
    }
  };

  const patientsList = users.filter((u) => u.role === 'patient');
  const verifiedProvidersList = users.filter((u) => u.role === 'provider' && u.is_active);

  const filteredUsers = users.filter((u) => {
    const matchesRole = roleFilter === 'all' || u.role === roleFilter;
    const matchesSearch =
      (u.full_name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (u.email || '').toLowerCase().includes(searchQuery.toLowerCase());
    return matchesRole && matchesSearch;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <ToastContainer toasts={toasts} onDismiss={removeToast} />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-2">
            <ShieldCheck className="w-7 h-7 text-primary" />
            <span>Adhera System Administration</span>
          </h1>
          <p className="text-xs sm:text-sm text-on-surface-variant mt-1">
            Global governance, identity access management, and infrastructure telemetry
          </p>
        </div>

        <button
          onClick={() => {
            if (patientsList.length > 0) setSelectedPatientId(patientsList[0].id);
            if (verifiedProvidersList.length > 0) setSelectedProviderId(verifiedProvidersList[0].id);
            setAssignModalOpen(true);
          }}
          className="btn-press inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-primary text-surface font-bold text-xs shadow-glow hover:bg-primary-container"
        >
          <Plus className="w-4 h-4" />
          <span>Assign Patient to Doctor</span>
        </button>
      </div>

      {/* Global Telemetry Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <GlassCard className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
              Total Accounts
            </span>
            <Users className="w-4 h-4 text-primary" />
          </div>
          <div className="mt-3 text-3xl font-extrabold text-white">{users.length}</div>
          <span className="text-[11px] text-on-surface-variant mt-1 block">Active on platform</span>
        </GlassCard>

        <GlassCard className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
              Active Patients
            </span>
            <UserCheck className="w-4 h-4 text-secondary" />
          </div>
          <div className="mt-3 text-3xl font-extrabold text-white">{patientsList.length}</div>
          <span className="text-[11px] text-secondary mt-1 block">Registered patients</span>
        </GlassCard>

        <GlassCard className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
              Care Providers
            </span>
            <Stethoscope className="w-4 h-4 text-tertiary" />
          </div>
          <div className="mt-3 text-3xl font-extrabold text-white">{verifiedProvidersList.length}</div>
          <span className="text-[11px] text-tertiary mt-1 block">Verified doctors</span>
        </GlassCard>

        <GlassCard className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
              System Health
            </span>
            <Server className="w-4 h-4 text-status-success" />
          </div>
          <div className="mt-3 text-2xl font-extrabold text-status-success flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-status-success animate-pulse" />
            <span>{healthStatus?.status === 'ok' ? 'HEALTHY' : 'OPERATIONAL'}</span>
          </div>
          <span className="text-[11px] text-on-surface-variant mt-1 block">DB: {healthStatus?.db || 'ok'}</span>
        </GlassCard>
      </div>

      {/* Pending Provider Verification Queue */}
      {pendingProviders.length > 0 && (
        <GlassCard className="p-6 border-status-warning/40 glow-amber">
          <div className="flex items-center justify-between pb-3 border-b border-white/10 mb-4">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-5 h-5 text-status-warning" />
              <h3 className="text-base font-bold text-white">
                Pending Provider Credentials Queue ({pendingProviders.length})
              </h3>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {pendingProviders.map((prov) => (
              <div
                key={prov.id}
                className="p-4 rounded-2xl bg-surface-container border border-white/10 flex items-center justify-between"
              >
                <div>
                  <span className="font-bold text-sm text-white block">{prov.full_name}</span>
                  <span className="text-xs text-on-surface-variant block">{prov.email}</span>
                  <div className="flex items-center space-x-2 text-[11px] text-primary mt-1">
                    <span>License: {prov.license_number || 'N/A'}</span>
                    <span>&bull;</span>
                    <span>{prov.specialization || 'General'}</span>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleApproveProvider(prov.id)}
                    className="btn-press px-3 py-1.5 rounded-xl bg-status-success text-surface font-bold text-xs"
                  >
                    Approve
                  </button>
                  <button
                    onClick={() => handleRejectProvider(prov.id)}
                    className="btn-press px-3 py-1.5 rounded-xl bg-status-error/10 text-status-error hover:bg-status-error/20 text-xs font-semibold"
                  >
                    Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      )}

      {/* User Governance Table */}
      <GlassCard className="p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/10">
          <div>
            <h3 className="text-base font-bold text-white">Platform Identity Directory</h3>
            <p className="text-xs text-on-surface-variant">View accounts, roles, and status</p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {/* Role Filter Chips */}
            <div className="flex rounded-xl bg-white/5 p-1 border border-white/5 text-xs">
              {['all', 'patient', 'provider', 'admin'].map((r) => (
                <button
                  key={r}
                  onClick={() => setRoleFilter(r)}
                  className={`px-3 py-1 rounded-lg capitalize font-medium transition-colors ${
                    roleFilter === r ? 'bg-primary text-surface font-bold shadow-sm' : 'text-on-surface-variant'
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>

            {/* Search Input */}
            <div className="relative w-48">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-on-surface-variant" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Filter users..."
                className="w-full pl-8 pr-3 py-1.5 rounded-xl glass-input text-xs"
              />
            </div>
          </div>
        </div>

        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-xs text-on-surface">
            <thead>
              <tr className="border-b border-white/10 text-[11px] uppercase tracking-wider text-on-surface-variant">
                <th className="py-3 px-4 font-semibold">User</th>
                <th className="py-3 px-4 font-semibold">Role</th>
                <th className="py-3 px-4 font-semibold">Timezone</th>
                <th className="py-3 px-4 font-semibold">Status</th>
                <th className="py-3 px-4 font-semibold text-right">Toggle</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {filteredUsers.map((u) => (
                <tr key={u.id} className="hover:bg-white/5 transition-colors">
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 rounded-full bg-primary/20 text-primary flex items-center justify-center font-bold uppercase text-xs">
                        {u.full_name?.charAt(0) || u.email?.charAt(0) || 'U'}
                      </div>
                      <div>
                        <span className="font-bold text-white block">{u.full_name || 'Anonymous'}</span>
                        <span className="text-[11px] text-on-surface-variant">{u.email}</span>
                      </div>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                        u.role === 'admin'
                          ? 'bg-tertiary/20 text-tertiary'
                          : u.role === 'provider'
                          ? 'bg-secondary/20 text-secondary'
                          : 'bg-primary/20 text-primary'
                      }`}
                    >
                      {u.role}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-on-surface-variant">{u.timezone || 'UTC'}</td>
                  <td className="py-3 px-4">
                    <span
                      className={`risk-badge-pill text-[10px] ${
                        u.is_active ? 'low' : 'critical'
                      }`}
                    >
                      {u.is_active ? 'Active' : 'Suspended'}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => handleToggleUserStatus(u.id, u.is_active)}
                      className={`px-3 py-1 rounded-lg text-xs font-semibold ${
                        u.is_active
                          ? 'bg-status-error/10 text-status-error hover:bg-status-error/20'
                          : 'bg-status-success/10 text-status-success hover:bg-status-success/20'
                      }`}
                    >
                      {u.is_active ? 'Deactivate' : 'Activate'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </GlassCard>

      {/* Manual Patient-Provider Assignment Modal */}
      <Modal
        isOpen={assignModalOpen}
        onClose={() => setAssignModalOpen(false)}
        title="Assign Patient to Healthcare Provider"
      >
        <form onSubmit={handleCreateAssignment} className="space-y-4 text-xs">
          <div>
            <label className="block font-semibold text-on-surface uppercase tracking-wider mb-1.5">
              Select Patient *
            </label>
            <select
              value={selectedPatientId}
              onChange={(e) => setSelectedPatientId(e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl glass-input text-sm bg-surface-container"
            >
              {patientsList.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.full_name || p.email} ({p.email})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block font-semibold text-on-surface uppercase tracking-wider mb-1.5">
              Select Provider *
            </label>
            <select
              value={selectedProviderId}
              onChange={(e) => setSelectedProviderId(e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl glass-input text-sm bg-surface-container"
            >
              {verifiedProvidersList.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.full_name} - {p.specialization || 'General'}
                </option>
              ))}
            </select>
          </div>

          <div className="pt-3 flex justify-end space-x-2">
            <button
              type="button"
              onClick={() => setAssignModalOpen(false)}
              className="px-4 py-2 rounded-xl text-on-surface-variant hover:bg-white/5 font-semibold"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-press px-4 py-2 rounded-xl bg-primary text-surface font-bold shadow-glow"
            >
              Create Assignment
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
