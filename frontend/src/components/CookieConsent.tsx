import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, Cookie, X } from 'lucide-react';
import { GlassCard } from './GlassCard';

export const CookieConsent: React.FC = () => {
  const [show, setShow] = useState(false);

  useEffect(() => {
    try {
      const consent = localStorage.getItem('adhera_cookie_consent');
      if (!consent) {
        // Slight delay to avoid layout shift on initial mount
        const timer = setTimeout(() => setShow(true), 800);
        return () => clearTimeout(timer);
      }
    } catch {
      // Safe fallback if localStorage is unavailable
    }
  }, []);

  const handleConsent = (choice: 'accepted' | 'essential') => {
    try {
      localStorage.setItem('adhera_cookie_consent', choice);
    } catch {}
    setShow(false);
  };

  if (!show) return null;

  return (
    <div
      role="region"
      aria-label="Privacy and Cookie Preferences"
      className="fixed bottom-4 left-4 right-4 sm:left-auto sm:right-6 sm:max-w-md z-50 animate-fade-in"
    >
      <GlassCard className="p-4 sm:p-5 border border-primary/20 shadow-2xl backdrop-blur-2xl bg-surface-container/95">
        <div className="flex items-start justify-between gap-3">
          <div className="w-8 h-8 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0 mt-0.5">
            <Cookie className="w-4 h-4" />
          </div>
          <div className="flex-1 text-xs">
            <h4 className="font-semibold text-white flex items-center gap-1.5 text-sm">
              <span>Privacy & Storage Notice</span>
              <ShieldCheck className="w-3.5 h-3.5 text-primary" />
            </h4>
            <p className="mt-1 text-on-surface-variant leading-relaxed text-[11px]">
              Adhera uses local storage and privacy-friendly telemetry strictly to secure your session and optimize medication schedule delivery. We never sell your health data.
            </p>
            <div className="mt-2 text-[11px]">
              <Link to="/privacy" className="text-primary hover:underline font-medium">
                Read our Privacy Policy
              </Link>
            </div>
          </div>
          <button
            onClick={() => handleConsent('essential')}
            aria-label="Dismiss cookie notice"
            className="text-on-surface-variant hover:text-white p-1 rounded-lg transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="mt-4 flex items-center justify-end gap-2 pt-2 border-t border-white/5">
          <button
            onClick={() => handleConsent('essential')}
            className="px-3 py-1.5 rounded-lg text-xs font-medium text-on-surface hover:text-white hover:bg-white/5 transition-colors"
          >
            Essential Only
          </button>
          <button
            onClick={() => handleConsent('accepted')}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-primary text-surface shadow-glow hover:bg-primary-light transition-all"
          >
            Accept All
          </button>
        </div>
      </GlassCard>
    </div>
  );
};
