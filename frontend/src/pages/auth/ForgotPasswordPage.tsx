import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../../lib/api';
import { Activity, Mail, ArrowLeft, Send } from 'lucide-react';
import { GlassCard } from '../../components/GlassCard';

export const ForgotPasswordPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setLoading(true);

    try {
      const res = await api.post<any>('/auth/forgot-password', { email });
      if (res.success) {
        setMessage('Password reset instructions have been sent to your email address.');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to request password reset.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
      <div className="absolute top-1/3 right-1/4 w-[450px] h-[450px] bg-primary/10 rounded-full blur-[100px] pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md z-10 px-4">
        <div className="flex flex-col items-center text-center">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-primary-dark via-primary to-primary-light flex items-center justify-center shadow-glow mb-3">
            <Activity className="w-6 h-6 text-surface font-black" />
          </div>
          <h2 className="text-2xl font-extrabold tracking-tight text-white">
            Reset your password
          </h2>
          <p className="mt-1 text-xs text-on-surface-variant">
            Enter your email to receive a recovery link
          </p>
        </div>

        {message && (
          <div className="mt-4 p-3 rounded-xl bg-status-success/10 border border-status-success/30 text-status-success text-xs text-center">
            {message}
          </div>
        )}

        {error && (
          <div className="mt-4 p-3 rounded-xl bg-status-error/10 border border-status-error/30 text-status-error text-xs text-center">
            {error}
          </div>
        )}

        <GlassCard className="mt-6 sm:px-8 py-8 shadow-2xl">
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="forgot-email" className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-2">
                Email Address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-on-surface-variant">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  id="forgot-email"
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

            <button
              type="submit"
              disabled={loading}
              className="w-full btn-press flex items-center justify-center space-x-2 py-3 px-4 rounded-xl bg-primary text-surface font-bold text-sm shadow-glow hover:bg-primary-container transition-colors disabled:opacity-50"
            >
              <span>{loading ? 'Sending link...' : 'Send Reset Link'}</span>
              <Send className="w-4 h-4" />
            </button>
          </form>

          <div className="mt-6 text-center">
            <Link
              to="/login"
              className="inline-flex items-center space-x-1.5 text-xs text-on-surface-variant hover:text-white"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Login</span>
            </Link>
          </div>
        </GlassCard>
      </div>
    </div>
  );
};
