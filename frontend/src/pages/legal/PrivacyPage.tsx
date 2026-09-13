import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Shield, Lock, Eye, Database, UserCheck, Mail, ArrowLeft, HeartPulse, AlertCircle, FileText } from 'lucide-react';
import { GlassCard } from '../../components/GlassCard';
import { usePageMeta } from '../../hooks/usePageMeta';
import { Footer } from '../../components/Footer';

export const PrivacyPage: React.FC = () => {
  usePageMeta('Privacy Policy', 'Learn how Adhera collects, protects, and handles your health and medication data with end-to-end security.');
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
            <Shield className="w-3.5 h-3.5" />
            <span>Adhera Data Protection & Trust</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Privacy Policy
          </h1>
          <p className="mt-2 text-sm text-on-surface-variant">
            Last Updated: September 13, 2026 • Effective Immediately
          </p>
        </div>

        {/* Medical Disclaimer Banner */}
        <GlassCard className="p-4 sm:p-5 mb-8 border border-primary/30 bg-primary/5 flex items-start space-x-3.5">
          <HeartPulse className="w-5 h-5 text-primary shrink-0 mt-0.5" />
          <div className="text-xs text-on-surface leading-relaxed">
            <strong className="text-primary font-bold">Important Medical Notice:</strong> Adhera is an intelligent adherence tracking and clinical coordination tool. It is not an emergency response service or automated prescribing platform. In any life-threatening emergency, immediately call your local emergency services (911 / 112).
          </div>
        </GlassCard>

        {/* Content Sections */}
        <div className="space-y-6">
          {/* Section 1: Overview */}
          <GlassCard className="p-6 sm:p-8 space-y-4">
            <div className="flex items-center space-x-3 text-white">
              <div className="p-2 rounded-xl bg-primary/10 text-primary">
                <FileText className="w-5 h-5" />
              </div>
              <h2 className="text-lg font-bold">1. Overview & Commitment</h2>
            </div>
            <p className="text-sm text-on-surface-variant leading-relaxed">
              At Adhera, your health privacy and medical confidentiality are our foundational priorities. This Privacy Policy details how Adhera ("we", "our", or "the Platform") collects, utilizes, stores, and protects personal health information (PHI) and user profile information when you access our web application and connected healthcare services.
            </p>
          </GlassCard>

          {/* Section 2: Data Collected */}
          <GlassCard className="p-6 sm:p-8 space-y-4">
            <div className="flex items-center space-x-3 text-white">
              <div className="p-2 rounded-xl bg-primary/10 text-primary">
                <Database className="w-5 h-5" />
              </div>
              <h2 className="text-lg font-bold">2. Information We Collect</h2>
            </div>
            <p className="text-sm text-on-surface-variant leading-relaxed">
              To deliver intelligent medication reminders and clinical safety oversight, we collect only the data necessary for treatment adherence:
            </p>
            <ul className="list-disc pl-5 space-y-2 text-sm text-on-surface-variant">
              <li>
                <strong className="text-white">Medication & Prescription Data:</strong> Medicine names, dosages, administration forms, prescribed frequencies, refill quotas, and logged intake timestamps.
              </li>
              <li>
                <strong className="text-white">Adherence & Side Effect Feedback:</strong> Dose confirmation history, missed dose logs, reported symptoms, severity levels, and side effect descriptions.
              </li>
              <li>
                <strong className="text-white">Wellness & Clinical Vitals:</strong> Self-recorded blood pressure, heart rate, blood glucose readings, mood ratings, and general wellness markers.
              </li>
              <li>
                <strong className="text-white">Account & Profile Information:</strong> Full name, verified email address, date of birth, blood group, known drug allergies, underlying medical conditions, and local timezone.
              </li>
              <li>
                <strong className="text-white">Provider Credentials:</strong> For healthcare professionals, medical license numbers and clinical specialization areas.
              </li>
            </ul>
          </GlassCard>

          {/* Section 3: How We Use Data */}
          <GlassCard className="p-6 sm:p-8 space-y-4">
            <div className="flex items-center space-x-3 text-white">
              <div className="p-2 rounded-xl bg-primary/10 text-primary">
                <Lock className="w-5 h-5" />
              </div>
              <h2 className="text-lg font-bold">3. How Information Is Used</h2>
            </div>
            <p className="text-sm text-on-surface-variant leading-relaxed">
              We process your information exclusively to power healthcare adherence workflows:
            </p>
            <ul className="list-disc pl-5 space-y-2 text-sm text-on-surface-variant">
              <li>Scheduling and delivering automated dose reminder notifications via web push and in-app alerts.</li>
              <li>Calculating personal adherence scores, streaks, and risk stratification metrics.</li>
              <li>Powering the personalized AI health assistant to provide context-aware adherence coaching and side effect guidance based on your actual prescribed medications.</li>
              <li>Generating clinical summaries and escalation alerts for your assigned healthcare team when severe side effects or adherence gaps occur.</li>
            </ul>
            <div className="p-3.5 rounded-xl bg-status-success/10 border border-status-success/20 text-status-success text-xs font-semibold">
              🔒 Zero Data Monetization: We never sell, rent, monetize, or share your medical data with third-party advertisers or data brokers.
            </div>
          </GlassCard>

          {/* Section 4: Who Can See Your Data */}
          <GlassCard className="p-6 sm:p-8 space-y-4">
            <div className="flex items-center space-x-3 text-white">
              <div className="p-2 rounded-xl bg-primary/10 text-primary">
                <Eye className="w-5 h-5" />
              </div>
              <h2 className="text-lg font-bold">4. Access Control & Visibility</h2>
            </div>
            <p className="text-sm text-on-surface-variant leading-relaxed">
              Access to information within Adhera is enforced through strict cryptographic authentication and Row-Level Security (RLS):
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
              <div className="p-3.5 rounded-xl bg-surface-container border border-white/5 space-y-1.5">
                <span className="text-xs font-bold text-primary uppercase tracking-wide">Patients</span>
                <p className="text-xs text-on-surface-variant">Full access to your own personal profile, medication list, dose history, wellness records, and AI chat logs.</p>
              </div>
              <div className="p-3.5 rounded-xl bg-surface-container border border-white/5 space-y-1.5">
                <span className="text-xs font-bold text-primary uppercase tracking-wide">Assigned Providers</span>
                <p className="text-xs text-on-surface-variant">Access restricted strictly to patients explicitly assigned to their clinical care roster.</p>
              </div>
              <div className="p-3.5 rounded-xl bg-surface-container border border-white/5 space-y-1.5">
                <span className="text-xs font-bold text-primary uppercase tracking-wide">System Admins</span>
                <p className="text-xs text-on-surface-variant">Administrative directory and operational audit access. No arbitrary viewing of private medical records.</p>
              </div>
            </div>
          </GlassCard>

          {/* Section 5: Data Retention & Security */}
          <GlassCard className="p-6 sm:p-8 space-y-4">
            <div className="flex items-center space-x-3 text-white">
              <div className="p-2 rounded-xl bg-primary/10 text-primary">
                <Shield className="w-5 h-5" />
              </div>
              <h2 className="text-lg font-bold">5. Storage, Security & Retention</h2>
            </div>
            <p className="text-sm text-on-surface-variant leading-relaxed">
              Data is stored in HIPAA-ready PostgreSQL databases with AES-256 encryption at rest and TLS 1.3 encryption in transit. Session tokens are signed using high-entropy asymmetric cryptographic keys.
            </p>
            <p className="text-sm text-on-surface-variant leading-relaxed">
              Data is retained for the duration of your active account and care engagement. Inactive or deleted accounts are purged in accordance with standard medical archiving and regulatory guidelines.
            </p>
          </GlassCard>

          {/* Section 6: User Rights */}
          <GlassCard className="p-6 sm:p-8 space-y-4">
            <div className="flex items-center space-x-3 text-white">
              <div className="p-2 rounded-xl bg-primary/10 text-primary">
                <UserCheck className="w-5 h-5" />
              </div>
              <h2 className="text-lg font-bold">6. Your Rights (Export & Deletion)</h2>
            </div>
            <p className="text-sm text-on-surface-variant leading-relaxed">
              In accordance with international healthcare privacy standards (including HIPAA and GDPR data privacy principles), you have the right to:
            </p>
            <ul className="list-disc pl-5 space-y-1.5 text-sm text-on-surface-variant">
              <li>Request an export of your complete adherence and clinical history.</li>
              <li>Update, correct, or amend profile details, allergies, or vitals at any time.</li>
              <li>Request the complete deletion of your account and associated personal identifiers.</li>
            </ul>
          </GlassCard>

          {/* Section 7: Contact */}
          <GlassCard className="p-6 sm:p-8 space-y-4">
            <div className="flex items-center space-x-3 text-white">
              <div className="p-2 rounded-xl bg-primary/10 text-primary">
                <Mail className="w-5 h-5" />
              </div>
              <h2 className="text-lg font-bold">7. Privacy Inquiries & Support</h2>
            </div>
            <p className="text-sm text-on-surface-variant leading-relaxed">
              If you have any questions regarding this Privacy Policy, your medical data rights, or platform security practices, please contact our Data Protection Officer:
            </p>
            <div className="p-3.5 rounded-xl bg-white/5 border border-white/10 font-mono text-xs text-primary">
              <a href="mailto:24co35@aiemgoa.ac.in" style={{color:'var(--accent,#00dbe7)'}}>24co35@aiemgoa.ac.in</a>
              {' • '}
              <a href="mailto:ashwithshetty02012006@gmail.com" style={{color:'var(--accent,#00dbe7)'}}>ashwithshetty02012006@gmail.com</a>
            </div>
          </GlassCard>
        </div>
      </div>

      <Footer />
    </div>
  );
};
