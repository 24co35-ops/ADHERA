import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { Activity, CheckCircle2, AlertCircle, Mail, Send } from 'lucide-react';
import { GlassCard } from '../../components/GlassCard';
import { api, setTokens } from '../../lib/api';
import { useAuthStore } from '../../stores/authStore';

export const ConfirmAuthPage: React.FC = () => {
  const [status, setStatus] = useState<'verifying' | 'success' | 'error'>('verifying');
  const [message, setMessage] = useState('Verifying your email token...');
  const [resendEmail, setResendEmail] = useState('');
  const [resending, setResending] = useState(false);
  const [resendStatus, setResendStatus] = useState<string | null>(null);

  const location = useLocation();
  const navigate = useNavigate();
  const { initialize } = useAuthStore();

  useEffect(() => {
    const handleAuth = async () => {
      try {
        const hash = location.hash.substring(1);
        const params = new URLSearchParams(hash || location.search);
        const token = params.get('token');
        const accessToken = params.get('access_token');
        const refreshToken = params.get('refresh_token');

        if (token) {
          // ADHERA v1.2 custom token confirmation
          const res = await api.get<any>(`/auth/confirm-email?token=${encodeURIComponent(token)}`);
          if (res.success) {
            setStatus('success');
            setMessage('Your email has been confirmed successfully! You can now sign in to your account.');
          } else {
            setStatus('error');
            setMessage(res.error?.message || 'Verification link expired or invalid.');
          }
        } else if (accessToken && refreshToken) {
          // Supabase session tokens
          setTokens(accessToken, refreshToken);
          await initialize();
          setStatus('success');
          setMessage('Email confirmed successfully! Redirecting to dashboard...');
          setTimeout(() => navigate('/dashboard'), 2000);
        } else {
          setStatus('error');
          setMessage('No confirmation token provided. Please check your verification link.');
        }
      } catch (err: any) {
        setStatus('error');
        setMessage(err.message || 'Verification link expired or invalid.');
      }
    };

    handleAuth();
  }, [location, navigate, initialize]);

  const handleResend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resendEmail) return;
    try {
      setResending(true);
      setResendStatus(null);
      const res = await api.post<any>('/auth/resend-confirmation', { email: resendEmail });
      if (res.success) {
        setResendStatus('A new confirmation email has been dispatched. Please check your inbox (valid for 30 minutes).');
      }
    } catch (err: any) {
      setResendStatus(err.message || 'Failed to send confirmation email.');
    } finally {
      setResending(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center p-4">
      <GlassCard className="max-w-md w-full text-center p-8 space-y-4 shadow-2xl">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-primary-dark via-primary to-primary-light flex items-center justify-center shadow-glow mx-auto mb-2">
          <Activity className="w-6 h-6 text-surface font-black" />
        </div>

        {status === 'verifying' && (
          <div className="space-y-3">
            <div className="w-8 h-8 border-3 border-primary/20 border-t-primary rounded-full animate-spin mx-auto" />
            <h3 className="text-base font-semibold text-white">Verifying Account...</h3>
            <p className="text-xs text-on-surface-variant">{message}</p>
          </div>
        )}

        {status === 'success' && (
          <div className="space-y-3">
            <CheckCircle2 className="w-10 h-10 text-status-success mx-auto" />
            <h3 className="text-base font-semibold text-white">Account Confirmed</h3>
            <p className="text-xs text-on-surface-variant">{message}</p>
            <Link
              to="/login"
              className="inline-block px-5 py-2.5 bg-primary text-surface font-bold text-xs rounded-xl mt-2 shadow-glow hover:bg-primary-light transition-all"
            >
              Sign In to Adhera
            </Link>
          </div>
        )}

        {status === 'error' && (
          <div className="space-y-4 text-left">
            <div className="text-center space-y-2">
              <AlertCircle className="w-10 h-10 text-status-error mx-auto" />
              <h3 className="text-base font-semibold text-white">Verification Link Expired</h3>
              <p className="text-xs text-status-error">{message}</p>
            </div>

            <div className="p-4 rounded-xl bg-white/5 border border-white/10 space-y-3">
              <p className="text-xs text-on-surface font-medium">
                Need a new confirmation link? (Links expire after 30 minutes)
              </p>
              <form onSubmit={handleResend} className="space-y-2">
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-on-surface-variant">
                    <Mail className="w-4 h-4" />
                  </div>
                  <input
                    type="email"
                    required
                    placeholder="Enter your email"
                    value={resendEmail}
                    onChange={(e) => setResendEmail(e.target.value)}
                    className="w-full pl-9 pr-3 py-1.5 rounded-lg glass-input text-xs"
                  />
                </div>
                <button
                  type="submit"
                  disabled={resending || !resendEmail}
                  className="w-full py-2 bg-primary/20 hover:bg-primary/30 border border-primary/40 text-primary font-bold text-xs rounded-lg flex items-center justify-center space-x-1.5 transition-all"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>{resending ? 'Sending...' : 'Resend Confirmation Email'}</span>
                </button>
              </form>

              {resendStatus && (
                <p className="text-[11px] text-status-success text-center mt-2">
                  {resendStatus}
                </p>
              )}
            </div>

            <div className="text-center pt-2">
              <Link
                to="/login"
                className="inline-block px-4 py-2 bg-white/10 hover:bg-white/15 text-white font-semibold text-xs rounded-xl"
              >
                Back to Login
              </Link>
            </div>
          </div>
        )}
      </GlassCard>
    </div>
  );
};
