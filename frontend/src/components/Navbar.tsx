import React, { useState } from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { useI18n } from '../lib/i18n';
import {
  Activity,
  Pill,
  MessageSquareWarning,
  User as UserIcon,
  LogOut,
  Users,
  Shield,
  Globe,
  Bell,
  Menu,
  X,
  Wind,
  Bot,
} from 'lucide-react';
import clsx from 'clsx';

export const Navbar: React.FC = () => {
  const { user, role, logout } = useAuthStore();
  const { locale, setLocale, t } = useI18n();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [langDropdownOpen, setLangDropdownOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const patientLinks = [
    { to: '/dashboard', label: t('nav.dashboard'), icon: Activity },
    { to: '/medicines', label: t('nav.medicines'), icon: Pill },
    { to: '/patient/wellness', label: t('nav.wellness'), icon: Wind },
    { to: '/patient/chat', label: t('nav.chat'), icon: Bot },
    { to: '/feedback', label: t('nav.feedback'), icon: MessageSquareWarning },
    { to: '/profile', label: t('nav.profile'), icon: UserIcon },
  ];

  const providerLinks = [
    { to: '/provider', label: t('nav.provider'), icon: Users },
    { to: '/provider/chat', label: t('nav.clinical_ai'), icon: Bot },
    { to: '/profile', label: t('nav.profile'), icon: UserIcon },
  ];

  const adminLinks = [
    { to: '/admin', label: t('nav.admin'), icon: Shield },
    { to: '/profile', label: t('nav.profile'), icon: UserIcon },
  ];

  const links = role === 'admin' ? adminLinks : role === 'provider' ? providerLinks : patientLinks;

  const languages = [
    { code: 'en', label: 'English' },
    { code: 'es', label: 'Español' },
    { code: 'hi', label: 'हिन्दी' },
  ];

  return (
    <nav className="sticky top-0 z-40 backdrop-blur-xl bg-surface/80 border-b border-white/10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => navigate('/')}>
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-primary-dark via-primary to-primary-light flex items-center justify-center shadow-glow">
              <Activity className="w-5 h-5 text-surface font-black" />
            </div>
            <div className="flex flex-col">
              <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-on-surface to-primary bg-clip-text text-transparent">
                Adhera
              </span>
              <span className="text-[10px] uppercase font-semibold tracking-wider text-primary/80 -mt-1">
                {role}
              </span>
            </div>
          </div>

          {/* Desktop Navigation Links */}
          <div className="hidden md:flex items-center space-x-1">
            {links.map((link) => {
              const Icon = link.icon;
              const isActive = location.pathname === link.to;
              return (
                <NavLink
                  key={link.to}
                  to={link.to}
                  className={clsx(
                    'flex items-center space-x-2 px-3 py-2 rounded-xl text-sm font-medium transition-all duration-150',
                    isActive
                      ? 'bg-primary/10 text-primary border border-primary/20 shadow-glow'
                      : 'text-on-surface-variant hover:text-white hover:bg-white/5'
                  )}
                >
                  <Icon className={clsx('w-4 h-4', isActive ? 'text-primary' : 'text-on-surface-variant')} />
                  <span>{link.label}</span>
                </NavLink>
              );
            })}
          </div>

          {/* Right Actions: Language, User details, Logout */}
          <div className="hidden md:flex items-center space-x-3">
            {/* Language Switcher */}
            <div className="relative">
              <button
                onClick={() => setLangDropdownOpen(!langDropdownOpen)}
                className="flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-xs font-medium text-on-surface-variant border border-white/10"
              >
                <Globe className="w-3.5 h-3.5" />
                <span className="uppercase">{locale}</span>
              </button>
              {langDropdownOpen && (
                <div className="absolute right-0 mt-2 w-32 rounded-xl glass-card p-1 shadow-2xl z-50">
                  {languages.map((l) => (
                    <button
                      key={l.code}
                      onClick={() => {
                        setLocale(l.code);
                        setLangDropdownOpen(false);
                      }}
                      className={clsx(
                        'w-full text-left px-3 py-1.5 text-xs rounded-lg transition-colors',
                        locale === l.code ? 'bg-primary/20 text-primary font-semibold' : 'text-on-surface hover:bg-white/5'
                      )}
                    >
                      {l.label}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* User Pill */}
            <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-surface-container border border-white/5">
              <div className="w-6 h-6 rounded-full bg-primary/20 text-primary flex items-center justify-center text-xs font-bold uppercase">
                {user?.full_name?.charAt(0) || user?.email?.charAt(0) || 'U'}
              </div>
              <span className="text-xs font-medium text-on-surface max-w-[120px] truncate">
                {user?.full_name || user?.email || 'Account'}
              </span>
            </div>

            {/* Logout Button */}
            <button
              onClick={handleLogout}
              title={t('nav.logout')}
              className="p-2 rounded-xl text-on-surface-variant hover:text-error hover:bg-error/10 transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>

          {/* Mobile menu button */}
          <div className="flex md:hidden items-center space-x-2">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-xl text-on-surface hover:bg-white/5"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden glass-panel border-b border-white/10 px-4 pt-2 pb-4 space-y-1">
          {links.map((link) => {
            const Icon = link.icon;
            const isActive = location.pathname === link.to;
            return (
              <NavLink
                key={link.to}
                to={link.to}
                onClick={() => setMobileMenuOpen(false)}
                className={clsx(
                  'flex items-center space-x-3 px-3 py-2.5 rounded-xl text-sm font-medium',
                  isActive ? 'bg-primary/10 text-primary font-semibold' : 'text-on-surface-variant hover:bg-white/5'
                )}
              >
                <Icon className="w-5 h-5" />
                <span>{link.label}</span>
              </NavLink>
            );
          })}
          {/* Mobile Language Switcher */}
          <div className="pt-2 pb-1 border-t border-white/10 flex items-center justify-between">
            <span className="text-xs text-on-surface-variant flex items-center gap-1">
              <Globe className="w-3.5 h-3.5" /> Language:
            </span>
            <div className="flex gap-1">
              {languages.map((l) => (
                <button
                  key={l.code}
                  onClick={() => setLocale(l.code)}
                  className={clsx(
                    'px-2 py-1 text-xs rounded-lg font-medium transition-colors',
                    locale === l.code ? 'bg-primary/20 text-primary font-bold' : 'text-on-surface hover:bg-white/5'
                  )}
                >
                  {l.label}
                </button>
              ))}
            </div>
          </div>

          <div className="pt-2 border-t border-white/10 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-7 h-7 rounded-full bg-primary/20 text-primary flex items-center justify-center text-xs font-bold">
                {user?.full_name?.charAt(0) || 'U'}
              </div>
              <span className="text-xs text-on-surface truncate">{user?.email}</span>
            </div>
            <button
              onClick={handleLogout}
              className="px-3 py-1.5 rounded-lg text-xs font-medium text-error bg-error/10"
            >
              {t('nav.logout')}
            </button>
          </div>
        </div>
      )}
    </nav>
  );
};
