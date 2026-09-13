import React, { useEffect, Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './stores/authStore';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Navbar } from './components/Navbar';

// Auth Pages — eager (needed immediately)
import { LoginPage } from './pages/auth/LoginPage';
import { RegisterPage } from './pages/auth/RegisterPage';
import { ForgotPasswordPage } from './pages/auth/ForgotPasswordPage';
import { ResetPasswordPage } from './pages/auth/ResetPasswordPage';
import { ConfirmAuthPage } from './pages/auth/ConfirmAuthPage';

// All other pages — lazy loaded (split into separate async chunks)
const PatientDashboard = lazy(() => import('./pages/patient/PatientDashboard').then(m => ({ default: m.PatientDashboard })));
const MedicinesPage = lazy(() => import('./pages/patient/MedicinesPage').then(m => ({ default: m.MedicinesPage })));
const FeedbackPage = lazy(() => import('./pages/patient/FeedbackPage').then(m => ({ default: m.FeedbackPage })));
const WellnessPage = lazy(() => import('./pages/patient/WellnessPage').then(m => ({ default: m.WellnessPage })));
const ProfilePage = lazy(() => import('./pages/patient/ProfilePage').then(m => ({ default: m.ProfilePage })));
const ChatPage = lazy(() => import('./pages/chat/ChatPage').then(m => ({ default: m.ChatPage })));
const ProviderDashboard = lazy(() => import('./pages/provider/ProviderDashboard').then(m => ({ default: m.ProviderDashboard })));
const ProviderPatientDetail = lazy(() => import('./pages/provider/ProviderPatientDetail').then(m => ({ default: m.ProviderPatientDetail })));
const AdminDashboard = lazy(() => import('./pages/admin/AdminDashboard').then(m => ({ default: m.AdminDashboard })));
const DirectoryPage = lazy(() => import('./pages/admin/DirectoryPage').then(m => ({ default: m.DirectoryPage })));
const DirectoryUserDetail = lazy(() => import('./pages/admin/DirectoryUserDetail').then(m => ({ default: m.DirectoryUserDetail })));

const PageLoader = () => (
  <div className="min-h-screen bg-surface flex items-center justify-center">
    <div className="w-10 h-10 border-4 border-primary/20 border-t-primary rounded-full animate-spin shadow-glow" />
  </div>
);


const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="min-h-screen bg-surface flex flex-col">
      <Navbar />
      <main className="flex-1 pb-16">{children}</main>
    </div>
  );
};

const RootRedirect: React.FC = () => {
  const { isAuthenticated, role, isLoading } = useAuthStore();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center">
        <div className="w-10 h-10 border-4 border-primary/20 border-t-primary rounded-full animate-spin shadow-glow" />
      </div>
    );
  }

  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (role === 'admin') return <Navigate to="/admin" replace />;
  if (role === 'provider') return <Navigate to="/provider" replace />;
  return <Navigate to="/dashboard" replace />;
};

export const App: React.FC = () => {
  const { initialize } = useAuthStore();

  useEffect(() => {
    initialize();

    // Register Service Worker for PWA / Web Push if available
    if ('serviceWorker' in navigator && !import.meta.env.SSR) {
      navigator.serviceWorker
        .register('/sw.js')
        .then((reg) => console.log('[Adhera] ServiceWorker registered with scope:', reg.scope))
        .catch((err) => console.warn('[Adhera] ServiceWorker registration failed:', err));
    }
  }, [initialize]);

  return (
    <BrowserRouter>
      <Suspense fallback={<PageLoader />}>
      <Routes>
        {/* Public Auth Routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="/auth/confirm" element={<ConfirmAuthPage />} />

        {/* Patient Routes */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute allowedRoles={['patient']}>
              <AppLayout>
                <PatientDashboard />
              </AppLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/medicines"
          element={
            <ProtectedRoute allowedRoles={['patient']}>
              <AppLayout>
                <MedicinesPage />
              </AppLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/feedback"
          element={
            <ProtectedRoute allowedRoles={['patient']}>
              <AppLayout>
                <FeedbackPage />
              </AppLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/patient/wellness"
          element={
            <ProtectedRoute allowedRoles={['patient']}>
              <AppLayout>
                <WellnessPage />
              </AppLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/patient/chat"
          element={
            <ProtectedRoute allowedRoles={['patient']}>
              <AppLayout>
                <ChatPage />
              </AppLayout>
            </ProtectedRoute>
          }
        />

        {/* Provider Routes */}
        <Route
          path="/provider"
          element={
            <ProtectedRoute allowedRoles={['provider']}>
              <AppLayout>
                <ProviderDashboard />
              </AppLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/provider/chat"
          element={
            <ProtectedRoute allowedRoles={['provider']}>
              <AppLayout>
                <ChatPage />
              </AppLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/provider/patient/:id"
          element={
            <ProtectedRoute allowedRoles={['provider']}>
              <AppLayout>
                <ProviderPatientDetail />
              </AppLayout>
            </ProtectedRoute>
          }
        />

        {/* Admin Routes */}
        <Route
          path="/admin"
          element={
            <ProtectedRoute allowedRoles={['admin']}>
              <AppLayout>
                <AdminDashboard />
              </AppLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/directory"
          element={
            <ProtectedRoute allowedRoles={['admin']}>
              <AppLayout>
                <DirectoryPage />
              </AppLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/directory/:userId"
          element={
            <ProtectedRoute allowedRoles={['admin']}>
              <AppLayout>
                <DirectoryUserDetail />
              </AppLayout>
            </ProtectedRoute>
          }
        />

        {/* Shared Profile Route for all logged in users */}
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <AppLayout>
                <ProfilePage />
              </AppLayout>
            </ProtectedRoute>
          }
        />

        {/* Root Fallback */}
        <Route path="/" element={<RootRedirect />} />
        <Route path="*" element={<RootRedirect />} />
      </Routes>
      </Suspense>
    </BrowserRouter>
  );
};
