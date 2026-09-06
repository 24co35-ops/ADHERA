import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../lib/api';
import { GlassCard } from '../../components/GlassCard';
import { ToastMessage, ToastContainer } from '../../components/Toast';
import {
  BookUser,
  Search,
  ChevronRight,
  UserX,
  RefreshCw,
  UserCheck,
  Stethoscope,
  ChevronLeft,
} from 'lucide-react';
import { DirectoryUser, DirectoryPage as DirectoryPageType } from '../../types';

export const DirectoryPage: React.FC = () => {
  const navigate = useNavigate();
  const [users, setUsers] = useState<DirectoryUser[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(20);
  const [roleFilter, setRoleFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const addToast = (type: 'success' | 'warning' | 'error' | 'info', message: string) => {
    setToasts((prev) => [...prev, { id: Math.random().toString(36).substring(2, 9), type, message }]);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  // Debounce search input
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(searchQuery);
      setPage(1);
    }, 300);
    return () => clearTimeout(handler);
  }, [searchQuery]);

  const loadDirectory = useCallback(async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      params.set('page', page.toString());
      params.set('limit', limit.toString());
      if (roleFilter) params.set('role', roleFilter);
      if (statusFilter) params.set('status', statusFilter);
      if (debouncedSearch) params.set('search', debouncedSearch);

      const res = await api.get<DirectoryPageType<DirectoryUser>>(`/admin/directory?${params.toString()}`);
      if (res.success && res.data) {
        setUsers(res.data.items || []);
        setTotal(res.data.total || 0);
      }
    } catch (err: any) {
      addToast('error', err.message || 'Failed to load identity directory');
    } finally {
      setLoading(false);
    }
  }, [page, limit, roleFilter, statusFilter, debouncedSearch]);

  useEffect(() => {
    loadDirectory();
  }, [loadDirectory]);

  const totalPages = Math.max(1, Math.ceil(total / limit));

  const formatDate = (isoStr?: string | null) => {
    if (!isoStr) return '—';
    try {
      const d = new Date(isoStr);
      return isNaN(d.getTime()) ? '—' : d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
    } catch {
      return '—';
    }
  };

  const formatLastActivity = (isoStr?: string | null) => {
    if (!isoStr) return 'Never';
    try {
      const d = new Date(isoStr);
      if (isNaN(d.getTime())) return 'Never';
      const diffSecs = Math.floor((Date.now() - d.getTime()) / 1000);
      if (diffSecs < 60) return 'Just now';
      if (diffSecs < 3600) return `${Math.floor(diffSecs / 60)}m ago`;
      if (diffSecs < 86400) return `${Math.floor(diffSecs / 3600)}h ago`;
      if (diffSecs < 604800) return `${Math.floor(diffSecs / 86400)}d ago`;
      return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    } catch {
      return '—';
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <ToastContainer toasts={toasts} onDismiss={removeToast} />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-2.5">
            <BookUser className="w-7 h-7 text-primary" />
            <span>Platform Identity Directory</span>
          </h1>
          <p className="text-xs sm:text-sm text-on-surface-variant mt-1">
            Global registry of all registered Patients and Healthcare Providers on ADHERA.
          </p>
        </div>

        <button
          onClick={() => loadDirectory()}
          disabled={loading}
          className="btn-press inline-flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-white text-xs font-semibold border border-white/10 self-start sm:self-auto"
          title="Refresh Directory"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-primary' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Search & Filters Bar */}
      <GlassCard className="p-4 sm:p-5">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
          {/* Search Input */}
          <div className="relative lg:col-span-2">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-on-surface-variant" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by full name or email..."
              className="w-full pl-10 pr-4 py-2.5 bg-black/30 border border-white/10 rounded-xl text-xs sm:text-sm text-white placeholder-on-surface-variant focus:outline-none focus:border-primary/50 transition-colors"
            />
          </div>

          {/* Role Filter */}
          <div>
            <select
              value={roleFilter}
              onChange={(e) => {
                setRoleFilter(e.target.value);
                setPage(1);
              }}
              className="w-full px-3.5 py-2.5 bg-black/30 border border-white/10 rounded-xl text-xs sm:text-sm text-white focus:outline-none focus:border-primary/50 transition-colors"
            >
              <option value="">All Roles (Patients & Providers)</option>
              <option value="patient">Patients Only</option>
              <option value="provider">Healthcare Providers Only</option>
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="w-full px-3.5 py-2.5 bg-black/30 border border-white/10 rounded-xl text-xs sm:text-sm text-white focus:outline-none focus:border-primary/50 transition-colors"
            >
              <option value="">All Statuses (Active & Suspended)</option>
              <option value="active">Active Accounts</option>
              <option value="inactive">Suspended / Inactive</option>
            </select>
          </div>
        </div>
      </GlassCard>

      {/* Directory Table */}
      <GlassCard className="overflow-hidden p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-white/10 bg-white/[0.02] text-[11px] font-bold text-on-surface-variant uppercase tracking-wider">
                <th className="py-3.5 px-4 sm:px-6">User / Identity</th>
                <th className="py-3.5 px-4">Role</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4">Registered</th>
                <th className="py-3.5 px-4">Last Activity</th>
                <th className="py-3.5 px-4">Assigned / License</th>
                <th className="py-3.5 px-4 sm:px-6 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 text-xs sm:text-sm">
              {loading ? (
                // Skeletons
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={`skeleton-${i}`} className="animate-pulse">
                    <td className="py-4 px-4 sm:px-6">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 rounded-full bg-white/10" />
                        <div className="space-y-1.5">
                          <div className="w-28 h-3.5 bg-white/10 rounded" />
                          <div className="w-36 h-2.5 bg-white/5 rounded" />
                        </div>
                      </div>
                    </td>
                    <td className="py-4 px-4"><div className="w-16 h-5 bg-white/10 rounded-full" /></td>
                    <td className="py-4 px-4"><div className="w-14 h-5 bg-white/10 rounded-full" /></td>
                    <td className="py-4 px-4"><div className="w-20 h-3 bg-white/10 rounded" /></td>
                    <td className="py-4 px-4"><div className="w-16 h-3 bg-white/10 rounded" /></td>
                    <td className="py-4 px-4"><div className="w-24 h-3 bg-white/10 rounded" /></td>
                    <td className="py-4 px-4 sm:px-6 text-right"><div className="w-12 h-6 bg-white/10 rounded ml-auto" /></td>
                  </tr>
                ))
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-on-surface-variant">
                    <UserX className="w-10 h-10 mx-auto mb-3 opacity-40 text-on-surface-variant" />
                    <p className="text-sm font-semibold text-white">No identities found</p>
                    <p className="text-xs text-on-surface-variant mt-1">
                      {searchQuery || roleFilter || statusFilter
                        ? 'Try adjusting your search query or filter options'
                        : 'No patient or provider accounts registered yet.'}
                    </p>
                  </td>
                </tr>
              ) : (
                users.map((u) => {
                  const isPatient = u.role === 'patient';
                  const initials = (u.full_name || 'U')
                    .split(' ')
                    .map((n) => n[0])
                    .join('')
                    .substring(0, 2)
                    .toUpperCase();

                  return (
                    <tr
                      key={u.id}
                      onClick={() => navigate(`/admin/directory/${u.id}`)}
                      className="hover:bg-white/[0.04] transition-colors cursor-pointer group"
                    >
                      <td className="py-4 px-4 sm:px-6">
                        <div className="flex items-center space-x-3">
                          <div
                            className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-xs shrink-0 ${
                              isPatient
                                ? 'bg-primary/15 text-primary border border-primary/30'
                                : 'bg-secondary/15 text-secondary border border-secondary/30'
                            }`}
                          >
                            {initials}
                          </div>
                          <div className="min-w-0">
                            <div className="font-semibold text-white truncate group-hover:text-primary transition-colors">
                              {u.full_name || 'Unnamed User'}
                            </div>
                            <div className="text-xs text-on-surface-variant truncate">
                              {u.email || 'No email attached'}
                            </div>
                          </div>
                        </div>
                      </td>

                      <td className="py-4 px-4">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${
                            isPatient
                              ? 'bg-primary/10 text-primary border-primary/30'
                              : 'bg-secondary/10 text-secondary border-secondary/30'
                          }`}
                        >
                          {isPatient ? <UserCheck className="w-3 h-3" /> : <Stethoscope className="w-3 h-3" />}
                          <span className="capitalize">{u.role}</span>
                        </span>
                      </td>

                      <td className="py-4 px-4">
                        <span
                          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium border ${
                            u.is_active
                              ? 'bg-status-success/10 text-status-success border-status-success/30'
                              : 'bg-status-danger/10 text-status-danger border-status-danger/30'
                          }`}
                        >
                          <span
                            className={`w-1.5 h-1.5 rounded-full ${
                              u.is_active ? 'bg-status-success' : 'bg-status-danger'
                            }`}
                          />
                          <span>{u.is_active ? 'Active' : 'Suspended'}</span>
                        </span>
                      </td>

                      <td className="py-4 px-4 text-xs text-on-surface-variant whitespace-nowrap">
                        {formatDate(u.created_at)}
                      </td>

                      <td className="py-4 px-4 text-xs text-on-surface-variant whitespace-nowrap">
                        {formatLastActivity(u.last_activity)}
                      </td>

                      <td className="py-4 px-4 text-xs text-on-surface-variant">
                        {isPatient ? (
                          u.assigned_provider_name ? (
                            <span className="text-white font-medium">Dr. {u.assigned_provider_name}</span>
                          ) : (
                            <span className="text-white/40 italic">Unassigned</span>
                          )
                        ) : (
                          u.license_number ? (
                            <span className="font-mono text-white/80">{u.license_number}</span>
                          ) : (
                            <span className="text-white/40 italic">N/A</span>
                          )
                        )}
                      </td>

                      <td className="py-4 px-4 sm:px-6 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/admin/directory/${u.id}`);
                          }}
                          className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-white/5 hover:bg-primary/20 text-white hover:text-primary text-xs font-medium border border-white/10 hover:border-primary/40 transition-all"
                        >
                          <span>View</span>
                          <ChevronRight className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination & Limit Footer */}
        <div className="p-4 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-on-surface-variant bg-white/[0.01]">
          <div className="flex items-center gap-2">
            <span>Show</span>
            <select
              value={limit}
              onChange={(e) => {
                setLimit(Number(e.target.value));
                setPage(1);
              }}
              className="bg-black/40 border border-white/10 rounded-lg px-2 py-1 text-white text-xs focus:outline-none focus:border-primary/50"
            >
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
            </select>
            <span>users per page</span>
            <span className="hidden sm:inline text-white/40">•</span>
            <span className="hidden sm:inline">Total {total} identities</span>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-white/70 mr-1">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1 || loading}
              className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed text-white border border-white/10"
              title="Previous Page"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages || loading}
              className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed text-white border border-white/10"
              title="Next Page"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </GlassCard>
    </div>
  );
};
export default DirectoryPage;
