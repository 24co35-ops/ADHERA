import React from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Compass, ArrowLeft, Home, LogIn } from 'lucide-react';
import { GlassCard } from '../components/GlassCard';
import { usePageMeta } from '../hooks/usePageMeta';
import { useAuthStore } from '../stores/authStore';

export const NotFoundPage: React.FC = () => {
  usePageMeta('404 Page Not Found', 'The requested page could not be located in the Adhera platform.');
  const navigate = useNavigate();
  const { isAuthenticated, role } = useAuthStore();

  const getHomeRoute = () => {
    if (!isAuthenticated) return '/login';
    if (role === 'admin') return '/admin';
    if (role === 'provider') return '/provider';
    return '/dashboard';
  };

  return (
    <div className="min-h-screen bg-surface flex flex-col justify-center items-center px-4 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Background ambient glow */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-primary/10 rounded-full blur-[140px] pointer-events-none" />

      <div className="max-w-md w-full z-10 text-center">
        <div className="w-16 h-16 rounded-3xl bg-primary/10 border border-primary/20 text-primary flex items-center justify-center mx-auto mb-6 shadow-glow">
          <Compass className="w-8 h-8 animate-pulse" />
        </div>

        <h1 className="text-5xl sm:text-6xl font-black text-white tracking-tight">
          404
        </h1>
        <h2 className="mt-2 text-xl font-bold text-white">
          Route Not Found
        </h2>
        <p className="mt-2 text-sm text-on-surface-variant leading-relaxed">
          The medication portal or clinical view you are seeking does not exist or has been relocated.
        </p>

        <GlassCard className="mt-8 p-6 shadow-2xl space-y-3">
          <Link
            to={getHomeRoute()}
            className="w-full py-3 px-4 rounded-xl bg-primary text-surface font-bold text-sm shadow-glow hover:bg-primary-light transition-all flex items-center justify-center space-x-2"
          >
            <Home className="w-4 h-4" />
            <span>{isAuthenticated ? 'Return to Dashboard' : 'Go to Home'}</span>
          </Link>

          <div className="grid grid-cols-2 gap-2 pt-1">
            <button
              onClick={() => navigate(-1)}
              className="py-2.5 px-3 rounded-xl bg-white/5 hover:bg-white/10 text-on-surface text-xs font-semibold border border-white/10 transition-colors flex items-center justify-center space-x-1.5"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Go Back</span>
            </button>
            {!isAuthenticated ? (
              <Link
                to="/login"
                className="py-2.5 px-3 rounded-xl bg-white/5 hover:bg-white/10 text-primary text-xs font-semibold border border-white/10 transition-colors flex items-center justify-center space-x-1.5"
              >
                <LogIn className="w-3.5 h-3.5" />
                <span>Sign In</span>
              </Link>
            ) : (
              <Link
                to="/medicines"
                className="py-2.5 px-3 rounded-xl bg-white/5 hover:bg-white/10 text-primary text-xs font-semibold border border-white/10 transition-colors flex items-center justify-center space-x-1.5"
              >
                <span>Medications</span>
              </Link>
            )}
          </div>
        </GlassCard>

        <div className="mt-8 flex items-center justify-center space-x-4 text-xs text-on-surface-variant">
          <Link to="/privacy" className="hover:text-primary transition-colors">
            Privacy Policy
          </Link>
          <span>•</span>
          <Link to="/terms" className="hover:text-primary transition-colors">
            Terms & Conditions
          </Link>
        </div>
      </div>
    </div>
  );
};
