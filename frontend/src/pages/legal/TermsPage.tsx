import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Scale, HeartHandshake, AlertTriangle, FileCheck, ShieldX, ArrowLeft, HeartPulse } from 'lucide-react';
import { GlassCard } from '../../components/GlassCard';
import { usePageMeta } from '../../hooks/usePageMeta';
import { Footer } from '../../components/Footer';

export const TermsPage: React.FC = () => {
  usePageMeta('Terms & Conditions', 'Read the terms and conditions governing the use of the Adhera intelligent medication adherence platform.');
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-surface flex flex-col justify-between text-on-surface">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 w-full">
        {/* Top bar navigation */}
        <div className="flex items-center justify-between mb-8">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center space-x-2 text-xs font-semibold text-on-surface-variant hover:text-primary transition-colors py-2 px-3 rounded-xl bg-white/5 border border-white/10 hover:border-primary/30"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back</span>
          </button>
          <Link
            to="/login"
            className="text-xs font-semibold text-primary hover:underline"
          >
            Sign In to Adhera
          </Link>
        </div>

        {/* Page Header */}
        <div className="text-center sm:text-left mb-8">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-semibold mb-3">
            <Scale className="w-3.5 h-3.5" />
            <span>Legal Agreement</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Terms & Conditions
          </h1>
          <p className="mt-2 text-sm text-on-surface-variant">
            Last Updated: September 13, 2026 • Please read carefully before using the service
          </p>
        </div>

        {/* High-visibility Medical Disclaimer Box */}
        <GlassCard className="p-5 sm:p-6 mb-8 border border-status-error/40 bg-status-error/5 shadow-glow-error/10">
          <div className="flex items-start space-x-3.5">
            <AlertTriangle className="w-6 h-6 text-status-error shrink-0 mt-0.5" />
            <div className="space-y-2 text-xs leading-relaxed">
              <h3 className="text-sm font-bold text-status-error uppercase tracking-wider">
                Critical Medical Disclaimer — Not Medical Advice
              </h3>
              <p className="text-on-surface font-medium">
                ADHERA IS AN ADHERENCE MANAGEMENT AND EDUCATIONAL TOOL. IT IS NOT A HEALTHCARE PROVIDER, MEDICAL DIAGNOSTIC SYSTEM, OR EMERGENCY DISPATCH SERVICE.
              </p>
              <p className="text-on-surface-variant">
                The content, reminder schedules, insights, and AI-generated assistant responses provided through Adhera are for informational and coordination support only. Never disregard, delay, or modify professional medical advice or prescribed treatment plans based on information within the platform. If you believe you are experiencing a medical emergency, immediately call <strong>911 / 112</strong> or your local emergency department.
              </p>
            </div>
          </div>
        </GlassCard>

        {/* Content Sections */}
        <div className="space-y-6">
          {/* 1. Acceptance of Terms */}
          <GlassCard className="p-6 sm:p-8 space-y-4">
            <div className="flex items-center space-x-3 text-white">
              <div className="p-2 rounded-xl bg-primary/10 text-primary">
                <FileCheck className="w-5 h-5" />
              </div>
              <h2 className="text-lg font-bold">1. Acceptance of Terms</h2>
            </div>
            <p className="text-sm text-on-surface-variant leading-relaxed">
              By registering an account, logging in, or accessing any part of Adhera ("the Service"), you confirm that you have read, understood, and agreed to be bound by these Terms & Conditions and our Privacy Policy. If you do not agree, you must immediately discontinue use of the platform.
            </p>
          </GlassCard>

          {/* 2. Description of Service */}
          <GlassCard className="p-6 sm:p-8 space-y-4">
            <div className="flex items-center space-x-3 text-white">
              <div className="p-2 rounded-xl bg-primary/10 text-primary">
                <HeartHandshake className="w-5 h-5" />
              </div>
              <h2 className="text-lg font-bold">2. Service Description</h2>
            </div>
            <p className="text-sm text-on-surface-variant leading-relaxed">
              Adhera provides digital tools for medication scheduling, reminder alerts, adherence logging, patient-reported side effect tracking, wellness logging, and clinical coordination between patients and verified healthcare providers.
            </p>
          </GlassCard>

          {/* 3. User Responsibilities */}
          <GlassCard className="p-6 sm:p-8 space-y-4">
            <div className="flex items-center space-x-3 text-white">
              <div className="p-2 rounded-xl bg-primary/10 text-primary">
                <HeartPulse className="w-5 h-5" />
              </div>
              <h2 className="text-lg font-bold">3. User Responsibilities & Account Security</h2>
            </div>
            <ul className="list-disc pl-5 space-y-2 text-sm text-on-surface-variant">
              <li>
                <strong className="text-white">Accurate Information:</strong> You agree to provide accurate, up-to-date medication and health information. Providing inaccurate dosage or scheduling details may affect reminder reliability.
              </li>
              <li>
                <strong className="text-white">Account Confidentiality:</strong> You are solely responsible for safeguarding your login credentials and for all activities that occur under your account.
              </li>
              <li>
                <strong className="text-white">Provider Verification:</strong> Healthcare providers registering on Adhera represent and warrant that they possess an active, unencumbered medical license in their practicing jurisdiction.
              </li>
            </ul>
          </GlassCard>

          {/* 4. Termination & Suspension */}
          <GlassCard className="p-6 sm:p-8 space-y-4">
            <div className="flex items-center space-x-3 text-white">
              <div className="p-2 rounded-xl bg-primary/10 text-primary">
                <ShieldX className="w-5 h-5" />
              </div>
              <h2 className="text-lg font-bold">4. Account Termination & Suspension</h2>
            </div>
            <p className="text-sm text-on-surface-variant leading-relaxed">
              We reserve the right to suspend or terminate accounts that violate security protocols, attempt unauthorized penetration, or misrepresent healthcare credentials. You may terminate your account at any time via your profile settings or by contacting our support team.
            </p>
          </GlassCard>

          {/* 5. Limitation of Liability */}
          <GlassCard className="p-6 sm:p-8 space-y-4">
            <div className="flex items-center space-x-3 text-white">
              <div className="p-2 rounded-xl bg-primary/10 text-primary">
                <Scale className="w-5 h-5" />
              </div>
              <h2 className="text-lg font-bold">5. Limitation of Liability & Warranty</h2>
            </div>
            <p className="text-sm text-on-surface-variant leading-relaxed">
              Adhera is provided on an "AS IS" and "AS AVAILABLE" basis without warranties of any kind, whether express or implied. We do not guarantee uninterrupted connectivity or that notification delivery will be instantaneous across all third-party carrier networks and operating systems.
            </p>
            <p className="text-sm text-on-surface-variant leading-relaxed">
              To the maximum extent permitted by applicable law, Adhera and its operators shall not be liable for any indirect, incidental, consequential, or punitive damages resulting from your use of or inability to use the platform.
            </p>
          </GlassCard>
        </div>
      </div>

      <Footer />
    </div>
  );
};
