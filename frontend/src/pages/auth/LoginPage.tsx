import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuthStore, parseJwt } from '../../stores/authStore';
import { UserRole } from '../../types';
import { api } from '../../lib/api';
import { Activity, Lock, Mail, ArrowRight, ShieldAlert, ChevronLeft } from 'lucide-react';
import { GlassCard } from '../../components/GlassCard';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(true);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [sessionExpiredNotice, setSessionExpiredNotice] = useState(false);

  // MFA step state
  const [mfaPartialToken, setMfaPartialToken] = useState<string | null>(null);
  const [mfaCode, setMfaCode] = useState('');
  const [mfaLoading, setMfaLoading] = useState(false);
  const [mfaError, setMfaError] = useState('');
  const mfaInputRef = useRef<HTMLInputElement>(null);

  const { login, isAuthenticated, role } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    if (params.get('expired')) {
      setSessionExpiredNotice(true);
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, [location]);

  useEffect(() => {
    if (isAuthenticated) {
      if (role === 'admin') navigate('/admin');
      else if (role === 'provider') navigate('/provider');
      else navigate('/dashboard');
    }
  }, [isAuthenticated, role, navigate]);

  // Auto-focus MFA input when step activates
  useEffect(() => {
    if (mfaPartialToken) {
      setTimeout(() => mfaInputRef.current?.focus(), 50);
    }
  }, [mfaPartialToken]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage('');
    setSessionExpiredNotice(false);
    setLoading(true);

    try {
      const res = await api.post<any>('/auth/login', { email, password });
      if (res.success && res.data) {
        // MFA required — switch to MFA step
        if (res.data.mfa_required) {
          setMfaPartialToken(res.data.partial_token);
          return;
        }

        const { access_token, refresh_token } = res.data;

        // Guard: reject empty/malformed tokens before storing
        if (!access_token || access_token.split('.').length !== 3) {
          setErrorMessage('Received invalid token from server. Please try again.');
          return;
        }

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

  const handleMfaSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!mfaPartialToken || mfaCode.length !== 6) return;
    setMfaError('');
    setMfaLoading(true);

    try {
      const res = await api.post<any>('/auth/mfa/confirm', {
        partial_token: mfaPartialToken,
        code: mfaCode,
      });

      if (res.success && res.data) {
        const { access_token, refresh_token } = res.data;

        if (!access_token || access_token.split('.').length !== 3) {
          setMfaError('Invalid token received. Please try again.');
          setMfaCode('');
          return;
        }

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
      }
    } catch (err: any) {
      const msg: string = err.message || '';
      if (msg.toLowerCase().includes('expired') || msg.toLowerCase().includes('invalid partial')) {
        setMfaError('Your verification session expired. Please sign in again.');
        setTimeout(() => backToLogin(), 2500);
      } else {
        setMfaError(msg || 'Invalid code. Please try again.');
      }
      setMfaCode('');
    } finally {
      setMfaLoading(false);
    }
  };

  const backToLogin = () => {
    setMfaPartialToken(null);
    setMfaCode('');
    setMfaError('');
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

        {/* ── MFA STEP ── */}
        {mfaPartialToken ? (
          <>
            {mfaError && (
              <div className="mt-4 p-3 rounded-xl bg-status-error/10 border border-status-error/30 text-status-error text-xs text-center">
                {mfaError}
              </div>
            )}

            <GlassCard className="mt-6 sm:px-8 py-8 shadow-2xl">
              <div className="flex flex-col items-center mb-6">
                <div className="w-12 h-12 rounded-2xl bg-primary/10 border border-primary/30 flex items-center justify-center mb-3">
                  <ShieldAlert className="w-6 h-6 text-primary" />
                </div>
                <h3 className="text-lg font-bold text-white">Two-Factor Authentication</h3>
                <p className="mt-1 text-xs text-on-surface-variant text-center">
                  Enter the 6-digit code from your authenticator app
                </p>
              </div>

              <form className="space-y-5" onSubmit={handleMfaSubmit}>
                <div>
                  <label htmlFor="mfa-code" className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-2">
                    Verification Code
                  </label>
                  <input
                    id="mfa-code"
                    name="mfa-code"
                    ref={mfaInputRef}
                    type="text"
                    inputMode="numeric"
                    pattern="[0-9]{6}"
                    maxLength={6}
                    required
                    autoComplete="one-time-code"
                    value={mfaCode}
                    onChange={(e) => setMfaCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    placeholder="000000"
                    className="w-full text-center tracking-[0.5em] text-xl font-mono py-3 rounded-xl glass-input"
                  />
                </div>

                <button
                  type="submit"
                  disabled={mfaLoading || mfaCode.length !== 6}
                  className="w-full btn-press flex items-center justify-center space-x-2 py-3 px-4 rounded-xl bg-primary text-surface font-bold text-sm shadow-glow hover:bg-primary-container transition-colors disabled:opacity-50"
                >
                  <span>{mfaLoading ? 'Verifying...' : 'Verify'}</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </form>

              <button
                type="button"
                onClick={backToLogin}
                className="mt-4 w-full flex items-center justify-center space-x-1 text-xs text-on-surface-variant hover:text-on-surface transition-colors"
              >
                <ChevronLeft className="w-3 h-3" />
                <span>Back to sign in</span>
              </button>
            </GlassCard>
          </>
        ) : (
          /* ── PASSWORD STEP ── */
          <>
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

            <GlassCard className="mt-6 sm:px-8 py-8 shadow-2xl">
              <form className="space-y-5" onSubmit={handleSubmit}>
                <div>
                  <label htmlFor="login-email" className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-2">
                    Email Address
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-on-surface-variant">
                      <Mail className="w-4 h-4" />
                    </div>
                    <input
                      id="login-email"
                      name="email"
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="name@example.com"
                      autoComplete="email"
                      className="w-full pl-10 pr-4 py-2.5 rounded-xl glass-input text-sm"
                    />
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label htmlFor="login-password" className="block text-xs font-semibold text-on-surface uppercase tracking-wider">
                      Password
                    </label>
                    <Link to="/forgot-password" className="text-xs text-primary hover:underline">
                      Forgot password?
                    </Link>
                  </div>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-on-surface-variant">
                      <Lock className="w-4 h-4" />
                    </div>
                    <input
                      id="login-password"
                      name="password"
                      type="password"
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••"
                      autoComplete="current-password"
                      className="w-full pl-10 pr-4 py-2.5 rounded-xl glass-input text-sm"
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <label htmlFor="login-remember-me" className="flex items-center space-x-2 cursor-pointer">
                    <input
                      id="login-remember-me"
                      name="rememberMe"
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
            </GlassCard>

            <p className="mt-6 text-center text-xs text-on-surface-variant">
              Don't have an account?{' '}
              <Link to="/register" className="text-primary font-semibold hover:underline">
                Create an account
              </Link>
            </p>
          </>
        )}
      </div>
    </div>
  );
};
