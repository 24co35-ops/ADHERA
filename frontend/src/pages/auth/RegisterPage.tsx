import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '../../lib/api';
import { useAuthStore } from '../../stores/authStore';
import { Activity, Mail, Lock, User as UserIcon, Calendar, Stethoscope, ArrowRight } from 'lucide-react';
import { GlassCard } from '../../components/GlassCard';
import clsx from 'clsx';

export const RegisterPage: React.FC = () => {
  const [role, setRole] = useState<'patient' | 'provider'>('patient');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [dateOfBirth, setDateOfBirth] = useState('');
  const [licenseNumber, setLicenseNumber] = useState('');
  const [specialization, setSpecialization] = useState('General Practice');
  const [timezoneStr, setTimezoneStr] = useState(
    Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const navigate = useNavigate();
  const { login } = useAuthStore();

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const payload: any = {
        email,
        password,
        role,
        full_name: fullName,
        timezone: timezoneStr,
      };

      if (role === 'patient') {
        payload.date_of_birth = dateOfBirth || null;
      } else {
        payload.license_number = licenseNumber;
        payload.specialization = specialization;
      }

      const res = await api.post<any>('/auth/signup', payload);
      if (res.success) {
        if (res.data?.access_token) {
          login(res.data.access_token, res.data.refresh_token, res.data.user);
          if (role === 'provider') navigate('/provider');
          else navigate('/dashboard');
        } else {
          setSuccessMsg('Registration successful! Please check your email to verify your account, or sign in.');
          setTimeout(() => navigate('/login'), 2500);
        }
      }
    } catch (err: any) {
      setError(err.message || 'Registration failed. Please verify your details.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
      <div className="absolute top-10 left-10 w-[500px] h-[500px] bg-primary/10 rounded-full blur-[120px] pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-lg z-10 px-4">
        <div className="flex flex-col items-center text-center">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-primary-dark via-primary to-primary-light flex items-center justify-center shadow-glow mb-3">
            <Activity className="w-6 h-6 text-surface font-black" />
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
            Create your Adhera Account
          </h2>
          <p className="mt-1 text-sm text-on-surface-variant">
            Join the smart adherence ecosystem
          </p>
        </div>

        {error && (
          <div className="mt-4 p-3 rounded-xl bg-status-error/10 border border-status-error/30 text-status-error text-xs text-center">
            {error}
          </div>
        )}

        {successMsg && (
          <div className="mt-4 p-3 rounded-xl bg-status-success/10 border border-status-success/30 text-status-success text-xs text-center">
            {successMsg}
          </div>
        )}

        <GlassCard className="mt-6 sm:px-8 py-8 shadow-2xl">
          {/* Role selector tabs */}
          <div className="grid grid-cols-2 gap-2 p-1 rounded-xl bg-surface-container mb-6 border border-white/5">
            <button
              type="button"
              onClick={() => setRole('patient')}
              className={clsx(
                'py-2 px-3 rounded-lg text-xs font-semibold transition-all flex items-center justify-center space-x-2',
                role === 'patient'
                  ? 'bg-primary text-surface shadow-glow'
                  : 'text-on-surface-variant hover:text-white'
              )}
            >
              <UserIcon className="w-4 h-4" />
              <span>I am a Patient</span>
            </button>
            <button
              type="button"
              onClick={() => setRole('provider')}
              className={clsx(
                'py-2 px-3 rounded-lg text-xs font-semibold transition-all flex items-center justify-center space-x-2',
                role === 'provider'
                  ? 'bg-primary text-surface shadow-glow'
                  : 'text-on-surface-variant hover:text-white'
              )}
            >
              <Stethoscope className="w-4 h-4" />
              <span>I am a Provider</span>
            </button>
          </div>

          <form className="space-y-4" onSubmit={handleRegister}>
            <div>
              <label className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-1.5">
                Full Name
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-on-surface-variant">
                  <UserIcon className="w-4 h-4" />
                </div>
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder={role === 'provider' ? 'Dr. Jane Doe' : 'Jane Doe'}
                  className="w-full pl-10 pr-4 py-2 rounded-xl glass-input text-sm"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-1.5">
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
                  className="w-full pl-10 pr-4 py-2 rounded-xl glass-input text-sm"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-1.5">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-on-surface-variant">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type="password"
                  required
                  minLength={8}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Min 8 characters"
                  className="w-full pl-10 pr-4 py-2 rounded-xl glass-input text-sm"
                />
              </div>
            </div>

            {role === 'patient' ? (
              <div>
                <label className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-1.5">
                  Date of Birth
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-on-surface-variant">
                    <Calendar className="w-4 h-4" />
                  </div>
                  <input
                    type="date"
                    value={dateOfBirth}
                    onChange={(e) => setDateOfBirth(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 rounded-xl glass-input text-sm text-on-surface"
                  />
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-1.5">
                    License Number
                  </label>
                  <input
                    type="text"
                    required
                    value={licenseNumber}
                    onChange={(e) => setLicenseNumber(e.target.value)}
                    placeholder="MED-12345"
                    className="w-full px-3 py-2 rounded-xl glass-input text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-1.5">
                    Specialization
                  </label>
                  <input
                    type="text"
                    value={specialization}
                    onChange={(e) => setSpecialization(e.target.value)}
                    placeholder="Cardiology"
                    className="w-full px-3 py-2 rounded-xl glass-input text-sm"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-on-surface uppercase tracking-wider mb-1.5">
                Timezone
              </label>
              <input
                type="text"
                value={timezoneStr}
                onChange={(e) => setTimezoneStr(e.target.value)}
                placeholder="America/New_York"
                className="w-full px-3 py-2 rounded-xl glass-input text-sm font-mono text-xs"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full btn-press mt-2 flex items-center justify-center space-x-2 py-3 px-4 rounded-xl bg-primary text-surface font-bold text-sm shadow-glow hover:bg-primary-container transition-colors disabled:opacity-50"
            >
              <span>{loading ? 'Creating Account...' : 'Register'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>
        </GlassCard>

        <p className="mt-6 text-center text-xs text-on-surface-variant">
          Already registered?{' '}
          <Link to="/login" className="text-primary font-semibold hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
};
