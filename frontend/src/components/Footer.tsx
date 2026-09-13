import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldAlert, HeartHandshake } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="w-full mt-auto border-t border-white/10 bg-surface/80 backdrop-blur-xl py-6 px-4 sm:px-6 lg:px-8 text-xs text-on-surface-variant">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Brand & Copyright */}
        <div className="flex items-center space-x-2">
          <img src="/assets/favicons/logo.svg" alt="Adhera logo" className="w-6 h-6 rounded-lg" />
          <span className="font-bold text-white tracking-tight">Adhera</span>
          <span className="text-on-surface-variant">© {new Date().getFullYear()} All rights reserved.</span>
        </div>

        {/* Disclaimer snippet */}
        <div className="flex items-center gap-1.5 text-[11px] text-on-surface-variant max-w-md text-center md:text-left">
          <ShieldAlert className="w-3.5 h-3.5 text-primary shrink-0" />
          <span>Informational adherence support only. Not a substitute for professional medical advice or emergency care.</span>
        </div>

        {/* Links */}
        <div className="flex items-center space-x-5 text-xs font-medium">
          <Link to="/privacy" className="hover:text-primary transition-colors">
            Privacy Policy
          </Link>
          <span className="text-on-surface-variant/50">•</span>
          <Link to="/terms" className="hover:text-primary transition-colors">
            Terms & Conditions
          </Link>
          <span className="text-on-surface-variant/50">•</span>
          <a
            href="https://github.com/24co35-ops/ADHERA"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-primary transition-colors inline-flex items-center gap-1"
          >
            <HeartHandshake className="w-3 h-3" />
            <span>GitHub</span>
          </a>
        </div>
      </div>
    </footer>
  );
};
