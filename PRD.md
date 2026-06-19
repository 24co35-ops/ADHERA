# Adhera — Product Requirements Document

**Version:** 1.0  
**Status:** Draft  
**Authors:** Mehtab Shaikh, Ashwith Shetty  
**Last Updated:** 2025  
**Project Type:** Software Engineering Academic Project  
**Domain:** Healthcare / Web Application / Health Informatics

---

## Table of Contents

1. [Overview](#1-overview)
2. [Problem Statement](#2-problem-statement)
3. [Goals and Non-Goals](#3-goals-and-non-goals)
4. [User Personas](#4-user-personas)
5. [User Stories](#5-user-stories)
6. [Feature Requirements](#6-feature-requirements)
7. [Non-Functional Requirements](#7-non-functional-requirements)
8. [Success Metrics](#8-success-metrics)
9. [Constraints and Assumptions](#9-constraints-and-assumptions)
10. [Timeline and Milestones](#10-timeline-and-milestones)
11. [Risks](#11-risks)
12. [Out of Scope](#12-out-of-scope)

---

## 1. Overview

Adhera is a web-based medication adherence platform that helps patients remember their medication schedules, track whether doses were taken, and report side effects — while giving verified healthcare providers real-time visibility into patient compliance.

### 1.1 Mission Statement

> Help patients stay on track with their medication and give doctors the data they need to intervene before non-adherence becomes a health crisis.

### 1.2 Background

Medication non-adherence affects an estimated 50% of patients with chronic conditions. Patients currently rely on paper prescriptions, memory, and generic phone alarms — none of which provide structured tracking, feedback loops, or provider visibility. Adhera replaces this fragmented approach with a centralised, automated system.

### 1.3 Target Platform

Web application (mobile-responsive). Built with Python backend, Supabase (PostgreSQL 15+) database, and HTML/CSS/JavaScript frontend. Extendable to a native mobile app in a future phase.

---

## 2. Problem Statement

### 2.1 Current State

| Patient's Current Approach | Pain Point |
|---|---|
| Paper prescriptions | Doses forgotten; no record |
| Memory | Unreliable; no structure |
| Generic phone alarms | No dose-level tracking or history |
| Manual charts | No automation; abandoned quickly |

### 2.2 Impact of Non-Adherence

- **Clinical:** Treatment failure, disease progression, poor chronic disease control
- **Economic:** Increased hospitalisation, repeat prescriptions, higher healthcare costs
- **Provider:** Inability to distinguish non-adherence from treatment failure between appointments

### 2.3 The Gap

No single tool currently:
- Sends structured, actionable dose reminders with Taken / Missed / Snooze responses
- Maintains a verified, append-only medication history
- Surfaces side-effect feedback with emergency escalation
- Gives healthcare providers real-time adherence dashboards

---

## 3. Goals and Non-Goals

### 3.1 Goals

| Priority | Goal |
|---|---|
| P0 | Patients can register medications and receive automated dose reminders by email and browser notification |
| P0 | Patients can mark doses Taken, Missed, or Snoozed; history is permanent and append-only |
| P0 | Healthcare providers can see assigned patients' adherence rates and receive emergency side-effect alerts |
| P1 | Patients can submit structured side-effect feedback with severity grading |
| P1 | Adherence analytics are displayed on daily / weekly / monthly dashboards |
| P1 | Administrators can manage user accounts and patient-to-provider assignments |
| P2 | Reports are exportable as PDF or CSV |
| P2 | Optional multi-factor authentication per account |

### 3.2 Non-Goals (Version 1.0)

- Native iOS or Android application
- Integration with hospital EHR systems
- Pharmacy ordering or prescription management
- Drug interaction checking or medical advice
- Insurance or billing integration
- Hardware medical device or wearable sensor integration
- Caregiver delegated access *(planned for v2.0)*

---

## 4. User Personas

### 4.1 Patient — Priya, 52

> "I take four different medications at different times of day. I forget the afternoon one constantly, and my doctor has no idea."

- **Goals:** Never miss a dose; understand her own adherence trends; feel reassured that her doctor is informed
- **Technical comfort:** Basic smartphone and web browser user
- **Key needs:** Simple reminders, easy one-tap dose response, no medical jargon

### 4.2 Healthcare Provider — Dr. Rahul, 41

> "Half my patients say they're taking their medication but their outcomes suggest otherwise. I need data, not self-reports."

- **Goals:** Real-time compliance dashboard; side-effect alerts before appointments; actionable reports
- **Technical comfort:** Comfortable with clinical dashboards
- **Key needs:** Patient list with adherence rates, drill-down per patient, emergency alerts

### 4.3 Administrator — Neha, 34

> "I manage the accounts for a 20-doctor clinic. I need to assign patients to the right doctor and verify credentials quickly."

- **Goals:** Efficient user lifecycle management; auditable access records
- **Technical comfort:** Technically literate
- **Key needs:** Provider verification workflow, patient assignment management, audit log

### 4.4 Caregiver — Rohan, 28 *(Future Phase — v2.0)*

> "My grandmother can't manage her own medication app. I want to see her schedule and get alerted if she misses something."

---

## 5. User Stories

### 5.1 Patient Stories

```
As a patient, I want to register my medications with a daily schedule
so that I receive automated reminders at the right times.

As a patient, I want to mark a dose as Taken, Missed, or Snoozed
so that my adherence history is accurate.

As a patient, I want the app to automatically mark unanswered doses as Missed
after 2 hours, so my record is complete even when I forget to respond.

As a patient, I want to report a side effect with a severity level
so that my doctor is informed about my medication experience.

As a patient, I want to see my weekly adherence percentage on a dashboard
so that I can understand my own compliance trends.

As a patient, I want to receive an emergency prompt on screen
when I report a Severity 4 side effect, directing me to call emergency services.
```

### 5.2 Healthcare Provider Stories

```
As a healthcare provider, I want to see all my assigned patients'
adherence rates on a single dashboard so I can identify who needs follow-up.

As a healthcare provider, I want to receive an email alert immediately
when a patient submits a Severity 4 (Emergency) side-effect report.

As a healthcare provider, I want to export a patient's adherence report
as PDF or CSV for use during appointments.

As a healthcare provider, I want to see a critical alert indicator
for patients whose weekly adherence falls below 50%.
```

### 5.3 Administrator Stories

```
As an administrator, I want to approve or reject Healthcare Provider
registration requests with a mandatory written reason so accountability is maintained.

As an administrator, I want to assign patients to providers
so that healthcare providers can monitor the right patients.

As an administrator, I want to view an audit log of all access events
so that I can investigate security incidents.
```

---

## 6. Feature Requirements

### 6.1 User Account Management

#### 6.1.1 Registration

| ID | Requirement | Priority |
|---|---|---|
| ADH-FR-01 | Self-registration for Patients and Healthcare Providers with: full name, email, password, role, DOB, contact number, timezone, and disclaimer acceptance | P0 |
| ADH-FR-02 | Email verification required for Patient accounts before activation | P0 |
| ADH-FR-03 | Healthcare Provider registrations require Administrator approval with a mandatory approval note | P0 |
| ADH-FR-04 | Administrator role is not self-registerable | P0 |
| ADH-FR-05 | Legal disclaimer accepted via explicit unchecked checkbox; acceptance stored permanently | P0 |

#### 6.1.2 Authentication

| ID | Requirement | Priority |
|---|---|---|
| ADH-FR-06 | Email + password login via Supabase Auth | P0 |
| ADH-FR-07 | Access token validity: 15 minutes. Refresh token validity: 7 days (Supabase Auth managed) | P0 |
| ADH-FR-08 | 5 failed login attempts on the same throttle key triggers a 15-minute lockout, audit-logged | P0 |
| ADH-FR-09 | Forgot Password: single-use signed reset link, expires 30 min, rate-limited 3/account/hour, no email enumeration | P0 |
| ADH-FR-10 | Session expires after 30 minutes of inactivity | P0 |
| ADH-FR-11 | Optional TOTP-based MFA configurable per account | P2 |

### 6.2 Medicine Management

| ID | Requirement | Priority |
|---|---|---|
| ADH-FR-12 | Add medicine: name, dosage, unit, route, frequency (daily / specific weekdays / alternate days / PRN), start/end date, instructions | P0 |
| ADH-FR-13 | PRN medicines: no reminders, excluded from adherence calculations, shown with 'PRN — no reminders' label | P0 |
| ADH-FR-14 | Edit any field of an active medicine; schedule changes update all future reminders and are audit-logged | P0 |
| ADH-FR-15 | Delete medicine (soft delete); all future reminders cancelled; history preserved | P0 |

### 6.3 Reminder Scheduling

| ID | Requirement | Priority |
|---|---|---|
| ADH-FR-16 | Dose time slots labelled Morning / Afternoon / Evening / Night | P0 |
| ADH-FR-17 | Recurrence: Daily, Specific weekdays, Alternate days (with stored anchor date) | P0 |
| ADH-FR-18 | All times stored in UTC; converted to patient's IANA timezone for display and delivery | P0 |
| ADH-FR-19 | Advisory conflict warning when a new reminder falls within 30 minutes of an existing one (non-blocking) | P1 |
| ADH-FR-20 | Duplicate reminder slots rejected at database level | P0 |
| ADH-FR-21 | Optional advance notification 10 minutes before dose time (disabled by default) | P2 |

### 6.4 Notification Dispatch

| ID | Requirement | Priority |
|---|---|---|
| ADH-FR-22 | Reminder sent via email (Supabase Edge Function + transactional email provider) | P0 |
| ADH-FR-23 | Reminder sent via browser Push API where supported; graceful fallback to email-only | P0 |
| ADH-FR-24 | Each notification includes: medicine name, dosage, Mark as Taken / Mark as Missed / Snooze actions | P0 |
| ADH-FR-25 | Failed notifications retried up to 3 times at 5-minute intervals; failure logged and shown on dashboard | P0 |
| ADH-FR-26 | Retry queue persists across process restarts (Supabase pg_cron + Edge Functions) | P0 |

### 6.5 Dose Tracking

| ID | Requirement | Priority |
|---|---|---|
| ADH-FR-27 | Dose statuses: Pending → Taken / Missed / Snoozed → Pending → Taken / Missed | P0 |
| ADH-FR-28 | Auto-expiry: 2 hours after scheduled time, Pending or Snoozed doses auto-marked Missed | P0 |
| ADH-FR-29 | Maximum 3 snoozes per dose; third unresolved snooze auto-marks Missed | P0 |
| ADH-FR-30 | Finalised outcomes (Taken / Missed) are logically immutable; correction via Administrator creates superseding entry | P0 |
| ADH-FR-31 | Permanent Medication History is append-only; contains only final outcomes (Taken / Missed) | P0 |

### 6.6 Feedback and Side Effects

| ID | Requirement | Priority |
|---|---|---|
| ADH-FR-32 | Patient registers at most one emergency contact (name, relationship, email); verified before use | P0 |
| ADH-FR-33 | Side-effect report: medicine, description (max 2,000 chars), severity (1–4), occurrence datetime | P0 |
| ADH-FR-34 | Severity 4 (Emergency): immediate on-screen emergency services prompt + email alert to provider + emergency contact within 60 seconds | P0 |
| ADH-FR-35 | Feedback records are append-only; patient corrections submitted as new records referencing the original | P0 |

### 6.7 Adherence Analytics

| ID | Requirement | Priority |
|---|---|---|
| ADH-FR-36 | Adherence Rate = (Doses Taken / Total Scheduled Doses) × 100, rounded to 1 decimal place | P0 |
| ADH-FR-37 | Computed for daily, weekly (ISO 8601), and monthly periods in patient's timezone | P0 |
| ADH-FR-38 | Warning indicator (icon + text label, not colour alone) for weekly adherence < 70% | P0 |
| ADH-FR-39 | Patient dashboard: today's schedule with statuses, week/month adherence rates, missed dose trend, 3 most recent feedback entries | P0 |
| ADH-FR-40 | Dashboard updates in real time via Supabase Realtime subscriptions | P1 |
| ADH-FR-41 | Adherence trend charts: line (trend over time) + bar (period comparison), keyboard-navigable with text alternatives | P1 |

### 6.8 Healthcare Provider Module

| ID | Requirement | Priority |
|---|---|---|
| ADH-FR-42 | Patient list with overall adherence rate and last activity date | P0 |
| ADH-FR-43 | Per-patient drill-down: adherence breakdown, Permanent Medication History, feedback records | P0 |
| ADH-FR-44 | Critical alert indicator for patients with weekly adherence < 50% | P0 |
| ADH-FR-45 | Per-patient report export: PDF or CSV, selectable date range | P1 |

### 6.9 Administrator Module

| ID | Requirement | Priority |
|---|---|---|
| ADH-FR-46 | Create, deactivate, and reactivate user accounts for all roles | P0 |
| ADH-FR-47 | Approve / reject Healthcare Provider registrations; rejection includes mandatory written reason | P0 |
| ADH-FR-48 | Manage patient-to-provider assignments (create, update, deactivate) | P0 |
| ADH-FR-49 | RBAC + Supabase RLS: patients see only their data; providers see only Active-assigned patients' data; admins use service role | P0 |

---

## 7. Non-Functional Requirements

| Category | Requirement | Target |
|---|---|---|
| Performance | API p95 response time | ≤ 2,000 ms at Standard Operating Load |
| Performance | Reminder dispatch latency | ≤ 60 s from scheduled time for ≥ 95% of dispatches |
| Performance | Dashboard API p95 | ≤ 3,000 ms |
| Performance | Throughput | ≥ 200 req/s, error rate < 1% |
| Availability | Monthly uptime | ≥ 99.5% (≤ 3.6 h unplanned downtime/month) |
| Security | Passwords | Stored as adaptive memory-hard hashes via Supabase Auth |
| Security | Transit encryption | TLS 1.2+ on all connections |
| Security | Rate limiting | ≤ 10 auth requests/throttle key/minute |
| Security | Audit log | Append-only; retained ≥ 5 years |
| Security | Encryption at rest | All Supabase storage volumes |
| Reliability | RPO | ≤ 24 hours |
| Reliability | RTO | ≤ 4 hours |
| Reliability | Backup retention | 30 days minimum |
| Scalability | Tier 1 | 1,000 users / 100 concurrent sessions (Supabase Pro) |
| Scalability | Tier 2 | 5,000 users / 500 sessions (Supabase Pro + compute add-on) |
| Scalability | Tier 3 | 10,000 users / 1,000 sessions (Supabase Team/Enterprise) |
| Accessibility | WCAG conformance | 2.1 Level AA on all core workflows |
| Privacy | Data retention | Adherence/feedback ≥ 3 years; audit log ≥ 5 years |
| Privacy | Account deletion | Personal identifiers anonymised within 30 days |

---

## 8. Success Metrics

### 8.1 Adoption Metrics

| Metric | Target (End of v1.0 Pilot) |
|---|---|
| Registered patients | ≥ 50 |
| Active Healthcare Providers | ≥ 5 |
| Patient DAU/MAU ratio | ≥ 60% |

### 8.2 Adherence Metrics

| Metric | Target |
|---|---|
| Average patient adherence rate (Adhera users) | ≥ 75% |
| Reminder response rate (Taken or Missed within 2 h) | ≥ 80% |
| Dashboard visit frequency | ≥ 3× per week per active patient |

### 8.3 Quality Metrics

| Metric | Target |
|---|---|
| Reminder delivery success rate | ≥ 95% |
| System uptime | ≥ 99.5%/month |
| Emergency alert delivery latency | ≤ 60 seconds |
| WCAG 2.1 AA violations in core workflows | 0 |

---

## 9. Constraints and Assumptions

### 9.1 Constraints

- Backend must be implemented in Python (FastAPI or Django)
- Database must be Supabase (PostgreSQL 15+)
- Authentication must use Supabase Auth (no parallel auth system)
- All secrets stored outside source code in environment variables or Supabase Vault
- Frontend must be mobile-responsive without requiring a native mobile app

### 9.2 Assumptions

- Patients have access to a stable internet connection and a supported browser
- Registered email addresses are valid and accessible
- Healthcare Providers submit accurate professional information for admin review
- The IANA timezone database is accessible to the server environment
- Development follows the Incremental Process Model

---

## 10. Timeline and Milestones

| Increment | Scope | Target |
|---|---|---|
| Increment 1 | User registration, login (Supabase Auth), profile management, disclaimer | Week 1–2 |
| Increment 2 | Medicine management (CRUD), PRN support, soft delete | Week 3–4 |
| Increment 3 | Reminder scheduling (all recurrence types), conflict detection | Week 5–6 |
| Increment 4 | Notification dispatch (email + browser), retry logic, dose tracking state machine | Week 7–8 |
| Increment 5 | Adherence calculations, patient dashboard, Supabase Realtime integration | Week 9–10 |
| Increment 6 | Feedback module, emergency escalation, emergency contact management | Week 11–12 |
| Increment 7 | Healthcare Provider module, Administrator module, RBAC + RLS | Week 13–14 |
| Increment 8 | Report export (PDF/CSV, Supabase Storage), polish, accessibility audit | Week 15–16 |

---

## 11. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Supabase Auth limitations for custom workflows | Medium | High | Prototype auth flow in Increment 1; use Supabase service role for admin overrides |
| pg_cron reliability for reminder dispatch | Medium | High | Supplement with Supabase Edge Function scheduled invocations; test thoroughly in Increment 4 |
| Browser Push API permission denial by users | High | Medium | Email fallback is mandatory (ADH-FR-23); display persistent enable-notifications prompt |
| DST edge cases causing missed reminders | Low | High | Comprehensive timezone regression tests; document behaviour in Privacy Impact Assessment |
| WCAG 2.1 AA compliance difficulty for charts | Medium | Medium | Use accessible charting library (Chart.js with aria-label support) from the start |
| Healthcare Provider verification bottleneck | Low | Medium | Admin dashboard surfaces pending approvals prominently; email notification sent on new submission |

---

## 12. Out of Scope

The following are explicitly excluded from Version 1.0 of Adhera:

- Native iOS or Android mobile application
- Hospital EHR system integration
- Pharmacy ordering or prescription management
- Drug interaction checking or clinical decision support
- Insurance billing or claims processing
- Wearable device or IoT sensor integration
- Caregiver delegated access *(v2.0 roadmap)*
- Multi-language / i18n support *(v2.0 roadmap)*
- Telemedicine or in-app messaging with providers

---

*Adhera — Medication Adherence Platform*  
*This document is version-controlled. All changes must be reflected in the Revision History.*
