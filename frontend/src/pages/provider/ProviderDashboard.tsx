import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../lib/api';
import { GlassCard } from '../../components/GlassCard';
import { ToastMessage, ToastContainer } from '../../components/Toast';
import {
  Users,
  AlertTriangle,
  Search,
  Check,
  X,
  ChevronRight,
  TrendingUp,
  Activity,
  HeartPulse,
  Clock,
  ShieldCheck,
} from 'lucide-react';

export const ProviderDashboard: React.FC = () => {
  const navigate = useNavigate();

  const [patients, setPatients] = useState<any[]>([]);
  const [pendingRequests, setPendingRequests] = useState<any[]>([]);
  const [criticalAlerts, setCriticalAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const addToast = (type: 'success' | 'warning' | 'error' | 'info', message: string) => {
    setToasts((prev) => [...prev, { id: Math.random().toString(36).substring(2, 9), type, message }]);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const loadProviderData = async () => {
    try {
      setLoading(true);
      const [patientsRes, requestsRes, alertsRes] = await Promise.all([
        api.get<any[]>('/provider/patients'),
        api.get<any[]>('/provider/pending-requests'),
        api.get<any[]>('/provider/critical-alerts'),
      ]);

      if (patientsRes.success && patientsRes.data) {
        setPatients(patientsRes.data);
      }
      if (requestsRes.success && requestsRes.data) {
        setPendingRequests(requestsRes.data);
      }
      if (alertsRes.success && alertsRes.data) {
        setCriticalAlerts(alertsRes.data);
      }
    } catch (err: any) {
      addToast('error', err.message || 'Failed to load provider data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProviderData();
  }, []);

  const handleApproveRequest = async (requestId: string) => {
    try {
      const res = await api.post(`/provider/requests/${requestId}/approve`);
      if (res.success) {
        addToast('success', 'Patient assignment approved!');
        loadProviderData();
      }
    } catch (err: any) {
      addToast('error', err.message || 'Failed to approve request');
    }
  };

  const handleRejectRequest = async (requestId: string) => {
    try {
      const res = await api.post(`/provider/requests/${requestId}/reject`);
      if (res.success) {
        addToast('info', 'Patient request rejected.');
        loadProviderData();
      }
    } catch (err: any) {
      addToast('error', err.message || 'Failed to reject request');
    }
  };

  const filteredPatients = patients.filter((p) =>
    (p.full_name || p.email || '').toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <ToastContainer toasts={toasts} onDismiss={removeToast} />

      {/* Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-2">
          <Users className="w-7 h-7 text-primary" />
          <span>Provider Clinical Command Center</span>
        </h1>
        <p className="text-xs sm:text-sm text-on-surface-variant mt-1">
          Monitor real-time patient adherence, clinical flags, and care requests
        </p>
      </div>

      {/* Critical Adherence Alerts Banner (<70%) */}
      {criticalAlerts.length > 0 && (
        <div className="p-4 rounded-2xl bg-status-warning/10 border border-status-warning/30 space-y-2 glow-amber">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-5 h-5 text-status-warning shrink-0" />
            <span className="text-sm font-bold text-status-warning">
              {criticalAlerts.length} Patient(s) with Low Adherence (&lt; 70%)
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {criticalAlerts.map((patient) => (
              <div
                key={patient.id}
                onClick={() => navigate(`/provider/patient/${patient.id}`)}
                className="p-2.5 rounded-xl bg-surface-container/90 border border-status-warning/20 flex items-center justify-between text-xs cursor-pointer hover:bg-surface-container"
              >
                <div>
                  <span className="font-bold text-white block">{patient.full_name || patient.email}</span>
                  <span className="text-[11px] text-status-warning font-semibold">
                    Adherence: {patient.adherence_rate}%
                  </span>
                </div>
                <ChevronRight className="w-4 h-4 text-status-warning" />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Pending Assignment Requests */}
      {pendingRequests.length > 0 && (
        <GlassCard className="p-6">
          <h3 className="text-base font-bold text-white mb-4 pb-3 border-b border-white/10 flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-secondary" />
              <span>Pending Patient Requests</span>
            </span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-secondary/20 text-secondary font-bold">
              {pendingRequests.length} pending
            </span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {pendingRequests.map((req) => (
              <div
                key={req.id}
                className="p-4 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-between"
              >
                <div>
                  <span className="font-bold text-sm text-white block">
                    {req.profiles?.full_name || 'Patient'}
                  </span>
                  <span className="text-xs text-on-surface-variant block">
                    {req.profiles?.email}
                  </span>
                  <span className="text-[10px] text-on-surface-variant/70 block mt-1">
                    Requested on {new Date(req.assigned_on).toLocaleDateString()}
                  </span>
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleApproveRequest(req.id)}
                    className="btn-press flex items-center space-x-1 px-3 py-1.5 rounded-xl bg-status-success text-surface font-bold text-xs"
                  >
                    <Check className="w-3.5 h-3.5" />
                    <span>Approve</span>
                  </button>
                  <button
                    onClick={() => handleRejectRequest(req.id)}
                    className="btn-press flex items-center space-x-1 px-3 py-1.5 rounded-xl bg-status-error/10 text-status-error hover:bg-status-error/20 font-semibold text-xs"
                  >
                    <X className="w-3.5 h-3.5" />
                    <span>Decline</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      )}

      {/* Patient Roster Table */}
      <GlassCard className="p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/10">
          <div>
            <h3 className="text-base font-bold text-white">Assigned Patient Roster</h3>
            <p className="text-xs text-on-surface-variant">Active patient records and adherence stats</p>
          </div>

          <div className="relative w-full sm:w-64">
            <Search className="w-4 h-4 absolute left-3 top-3 text-on-surface-variant" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search patients..."
              className="w-full pl-9 pr-3 py-2 rounded-xl glass-input text-xs"
            />
          </div>
        </div>

        {loading ? (
          <div className="py-12 text-center">
            <div className="w-8 h-8 border-3 border-primary/20 border-t-primary rounded-full animate-spin mx-auto" />
            <p className="text-xs text-on-surface-variant mt-2">Loading patient roster...</p>
          </div>
        ) : filteredPatients.length === 0 ? (
          <div className="py-12 text-center space-y-2">
            <Users className="w-10 h-10 text-on-surface-variant/40 mx-auto" />
            <p className="text-sm font-semibold text-white">No active patients found</p>
            <p className="text-xs text-on-surface-variant">
              When patients connect with you or admins assign them, they will appear here.
            </p>
          </div>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-xs text-on-surface">
              <thead>
                <tr className="border-b border-white/10 text-[11px] uppercase tracking-wider text-on-surface-variant">
                  <th className="py-3 px-4 font-semibold">Patient Name</th>
                  <th className="py-3 px-4 font-semibold">Contact / Timezone</th>
                  <th className="py-3 px-4 font-semibold">Adherence Rate</th>
                  <th className="py-3 px-4 font-semibold">Active Rx</th>
                  <th className="py-3 px-4 font-semibold text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {filteredPatients.map((patient) => {
                  const rate = patient.adherence_rate ?? 100;
                  const isWarning = rate < 70;
                  return (
                    <tr
                      key={patient.id}
                      onClick={() => navigate(`/provider/patient/${patient.id}`)}
                      className="hover:bg-white/5 transition-colors cursor-pointer"
                    >
                      <td className="py-3 px-4">
                        <div className="flex items-center space-x-3">
                          <div className="w-8 h-8 rounded-full bg-primary/20 text-primary flex items-center justify-center font-bold uppercase text-xs">
                            {patient.full_name?.charAt(0) || 'P'}
                          </div>
                          <div>
                            <span className="font-bold text-white block">
                              {patient.full_name || 'Patient'}
                            </span>
                            <span className="text-[11px] text-on-surface-variant">
                              {patient.email}
                            </span>
                          </div>
                        </div>
                      </td>
                      <td className="py-3 px-4 text-on-surface-variant">
                        <span>{patient.timezone || 'UTC'}</span>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center space-x-2">
                          <span
                            className={`font-bold ${
                              isWarning ? 'text-status-warning' : 'text-status-success'
                            }`}
                          >
                            {rate}%
                          </span>
                          <div className="w-16 bg-white/10 rounded-full h-1.5 overflow-hidden">
                            <div
                              className={`h-full rounded-full ${
                                isWarning ? 'bg-status-warning' : 'bg-status-success'
                              }`}
                              style={{ width: `${Math.min(rate, 100)}%` }}
                            />
                          </div>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded-full bg-white/5 border border-white/5 text-[11px] font-semibold text-white">
                          {patient.active_medicines_count ?? '-'} Rx
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/provider/patient/${patient.id}`);
                          }}
                          className="btn-press px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/15 text-white font-semibold text-xs inline-flex items-center space-x-1"
                        >
                          <span>Review</span>
                          <ChevronRight className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </GlassCard>
    </div>
  );
};
