import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuthStore, parseJwt } from '../../stores/authStore';
import { UserRole } from '../../types';
import { api } from '../../lib/api';
import { Activity, Lock, Mail, ArrowRight, ShieldCheck, UserCheck, Stethoscope } from 'lucide-react';
import { GlassCard } from '../../components/GlassCard';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(true);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [sessionExpiredNotice, setSessionExpiredNotice] = useState(false);

  const { login, isAuthenticated, role } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    if (params.get('expired')) {
      setSessionExpiredNotice(true);
    }
  }, [location]);

  useEffect(() => {
    if (isAuthenticated) {
      if (role === 'admin') navigate('/admin');
      else if (role === 'provider') navigate('/provider');
      else navigate('/dashboard');
    }
  }, [isAuthenticated, role, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage('');
    setLoading(true);

    try {
      const res = await api.post<any>('/auth/login', { email, password });
      if (res.success && res.data) {
        const { access_token, refresh_token } = res.data;
        const payload = parseJwt(access_token);
        const userRole: UserRole = res.data.user?.role || payload?.user_metadata?.role || payload?.role || 'patient';
        const userObj = res.data.user || {
          id: payload?.sub || '',
          email: payload?.email || email,
          role: userRole,
          full_name: payload?.user_metadata?.full_name || '',
        };

        login(access_token, refresh_token, userObj, rememberMe);

        if (userRole === 'admin') navigate('/admin');
        else if (userRole === 'provider') navigate('/provider');
        else navigate('/dashboard');
      } else {
        setErrorMessage('Invalid credentials');
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const fillDemo = (roleType: 'patient' | 'provider' | 'admin') => {
    if (roleType === 'patient') {
      setEmail('patient@adhera.io');
      setPassword('PatientPass123!');
    } else if (roleType === 'provider') {
      setEmail('dr.house@adhera.io');
      setPassword('ProviderPass123!');
    } else {
      setEmail('admin@adhera.io');
      setPassword('AdminPass123!');
    }
  };

  return (
    <div className="min-h-screen bg-surface flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Background Decorative Glow Circles */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-primary/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-10 right-10 w-[400px] h-[400px] bg-secondary-container/10 rounded-full blur-[100px] pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md z-10 px-4">
        {/* Brand Header */}
        <div className="flex flex-col items-center text-center">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-primary-dark via-primary to-primary-light flex items-center justify-center shadow-glow mb-4">
            <Activity className="w-8 h-8 text-surface font-black" />
          </div>
          <h2 className="text-3xl font-extrabold tracking-tight text-white">
            Welcome to Adhera
          </h2>
          <p className="mt-2 text-sm text-on-surface-variant">
            Intelligent Medication Adherence Platform
          </p>
        </div>

        {sessionExpiredNotice && (
          <div className="mt-4 p-3 rounded-xl bg-status-warning/10 border border-status-warning/30 text-status-warning text-xs text-center">
            Your session expired. Please sign in again.
          </div>
        )}

        {errorMessage && (
          <div className="mt-4 p-3 rounded-xl bg-status-error/10 border border-status-error/30 text-status-error text-xs text-center">
            {errorMessage}
          </div>
        )}

        {/* Login Card */}
        <GlassCard className="mt-6 sm:px-8 py-8 shadow-2xl">
          <form className="space-y-5" onSubmit={handleSubmit}>
            <div>
              <label className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-2">
                Email Address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-on-surface-variant">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl glass-input text-sm"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-xs font-semibold text-on-surface uppercase tracking-wider">
                  Password
                </label>
                <Link
                  to="/forgot-password"
                  className="text-xs text-primary hover:underline"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-on-surface-variant">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl glass-input text-sm"
                />
              </div>
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-4 h-4 rounded border-white/20 bg-white/5 text-primary focus:ring-primary focus:ring-offset-surface"
                />
                <span className="text-xs text-on-surface-variant">Remember me</span>
              </label>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full btn-press flex items-center justify-center space-x-2 py-3 px-4 rounded-xl bg-primary text-surface font-bold text-sm shadow-glow hover:bg-primary-container transition-colors disabled:opacity-50"
            >
              <span>{loading ? 'Authenticating...' : 'Sign In'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Quick Demo Accounts */}
          <div className="mt-6 pt-6 border-t border-white/10">
            <span className="block text-[11px] font-semibold text-on-surface-variant uppercase tracking-wider text-center mb-3">
              Quick Demo Fill
            </span>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => fillDemo('patient')}
                className="flex flex-col items-center p-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-[11px] text-on-surface transition-colors"
              >
                <UserCheck className="w-4 h-4 text-primary mb-1" />
                <span>Patient</span>
              </button>
              <button
                type="button"
                onClick={() => fillDemo('provider')}
                className="flex flex-col items-center p-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-[11px] text-on-surface transition-colors"
              >
                <Stethoscope className="w-4 h-4 text-secondary mb-1" />
                <span>Provider</span>
              </button>
              <button
                type="button"
                onClick={() => fillDemo('admin')}
                className="flex flex-col items-center p-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-[11px] text-on-surface transition-colors"
              >
                <ShieldCheck className="w-4 h-4 text-tertiary mb-1" />
                <span>Admin</span>
              </button>
            </div>
          </div>
        </GlassCard>

        <p className="mt-6 text-center text-xs text-on-surface-variant">
          Don't have an account?{' '}
          <Link to="/register" className="text-primary font-semibold hover:underline">
            Create an account
          </Link>
        </p>
      </div>
    </div>
  );
};
