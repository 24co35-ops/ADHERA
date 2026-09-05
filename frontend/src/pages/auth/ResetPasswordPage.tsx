import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { api } from '../../lib/api';
import { Activity, Lock, ArrowRight, CheckCircle2 } from 'lucide-react';
import { GlassCard } from '../../components/GlassCard';

export const ResetPasswordPage: React.FC = () => {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const navigate = useNavigate();
  const location = useLocation();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);
    try {
      // Get token from URL query or hash if present
      const params = new URLSearchParams(location.search);
      const token = params.get('token') || params.get('access_token');

      const res = await api.post<any>('/auth/reset-password', {
        password,
        token,
      });

      if (res.success) {
        setSuccess(true);
        setTimeout(() => navigate('/login'), 2500);
      }
    } catch (err: any) {
      setError(err.message || 'Password reset failed. Token may be expired.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
      <div className="sm:mx-auto sm:w-full sm:max-w-md z-10 px-4">
        <div className="flex flex-col items-center text-center">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-primary-dark via-primary to-primary-light flex items-center justify-center shadow-glow mb-3">
            <Activity className="w-6 h-6 text-surface font-black" />
          </div>
          <h2 className="text-2xl font-extrabold tracking-tight text-white">
            Set New Password
          </h2>
        </div>

        {success ? (
          <GlassCard className="mt-6 sm:px-8 py-8 shadow-2xl text-center space-y-4">
            <CheckCircle2 className="w-12 h-12 text-status-success mx-auto" />
            <h3 className="text-lg font-bold text-white">Password Updated!</h3>
            <p className="text-xs text-on-surface-variant">
              Your password has been changed. Redirecting you to sign in...
            </p>
            <Link
              to="/login"
              className="inline-block px-4 py-2 bg-primary text-surface font-bold text-xs rounded-xl"
            >
              Sign In Now
            </Link>
          </GlassCard>
        ) : (
          <GlassCard className="mt-6 sm:px-8 py-8 shadow-2xl">
            {error && (
              <div className="mb-4 p-3 rounded-xl bg-status-error/10 border border-status-error/30 text-status-error text-xs text-center">
                {error}
              </div>
            )}

            <form className="space-y-4" onSubmit={handleSubmit}>
              <div>
                <label htmlFor="reset-password" className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-2">
                  New Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-on-surface-variant">
                    <Lock className="w-4 h-4" />
                  </div>
                  <input
                    id="reset-password"
                    name="password"
                    type="password"
                    required
                    minLength={8}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    autoComplete="new-password"
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl glass-input text-sm"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="reset-confirm-password" className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-2">
                  Confirm New Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-on-surface-variant">
                    <Lock className="w-4 h-4" />
                  </div>
                  <input
                    id="reset-confirm-password"
                    name="confirmPassword"
                    type="password"
                    required
                    minLength={8}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="••••••••"
                    autoComplete="new-password"
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl glass-input text-sm"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full btn-press flex items-center justify-center space-x-2 py-3 px-4 rounded-xl bg-primary text-surface font-bold text-sm shadow-glow hover:bg-primary-container transition-colors disabled:opacity-50"
              >
                <span>{loading ? 'Updating...' : 'Update Password'}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </form>
          </GlassCard>
        )}
      </div>
    </div>
  );
};
