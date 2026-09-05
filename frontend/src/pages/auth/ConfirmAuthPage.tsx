import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { Activity, CheckCircle2, AlertCircle } from 'lucide-react';
import { GlassCard } from '../../components/GlassCard';
import { setTokens } from '../../lib/api';
import { useAuthStore } from '../../stores/authStore';

export const ConfirmAuthPage: React.FC = () => {
  const [status, setStatus] = useState<'verifying' | 'success' | 'error'>('verifying');
  const [message, setMessage] = useState('Verifying your email token...');
  const location = useLocation();
  const navigate = useNavigate();
  const { initialize } = useAuthStore();

  useEffect(() => {
    const handleAuth = async () => {
      try {
        // Hash fragments: #access_token=...&refresh_token=...
        const hash = location.hash.substring(1);
        const params = new URLSearchParams(hash || location.search);
        const accessToken = params.get('access_token');
        const refreshToken = params.get('refresh_token');

        if (accessToken && refreshToken) {
          setTokens(accessToken, refreshToken);
          await initialize();
          setStatus('success');
          setMessage('Email confirmed successfully! Redirecting...');
          setTimeout(() => navigate('/dashboard'), 2000);
        } else {
          setStatus('success');
          setMessage('Email verification recorded. Please sign in with your credentials.');
          setTimeout(() => navigate('/login'), 2500);
        }
      } catch (err: any) {
        setStatus('error');
        setMessage(err.message || 'Verification link expired or invalid.');
      }
    };

    handleAuth();
  }, [location, navigate, initialize]);

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
            <Link to="/login" className="inline-block px-4 py-2 bg-primary text-surface font-bold text-xs rounded-xl mt-2">
              Sign In
            </Link>
          </div>
        )}

        {status === 'error' && (
          <div className="space-y-3">
            <AlertCircle className="w-10 h-10 text-status-error mx-auto" />
            <h3 className="text-base font-semibold text-white">Verification Failed</h3>
            <p className="text-xs text-status-error">{message}</p>
            <Link to="/login" className="inline-block px-4 py-2 bg-white/10 hover:bg-white/15 text-white font-semibold text-xs rounded-xl mt-2">
              Go to Login
            </Link>
          </div>
        )}
      </GlassCard>
    </div>
  );
};
