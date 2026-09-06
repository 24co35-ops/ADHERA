# Adhera — Medication Adherence Platform

> *Help patients stay on track with their medication and give doctors the data they need to intervene before non-adherence becomes a health crisis.*

**Version:** 1.0 · **Status:** Active Development · **Live:** [https://adhera-seven.vercel.app](https://adhera-seven.vercel.app)  
**Domain:** Healthcare / Web Application / Health Informatics  
**Project Type:** Software Engineering Academic Project

---

## Table of Contents

1. [What is Adhera?](#what-is-adhera)
2. [Key Features](#key-features)
3. [User Roles](#user-roles)
4. [Architecture Overview](#architecture-overview)
5. [Getting Started](#getting-started)
6. [Environment Variables](#environment-variables)
7. [Database Setup](#database-setup)
8. [Running the Application](#running-the-application)
9. [API Reference](#api-reference)
10. [Testing](#testing)
11. [Deployment](#deployment)
12. [Project Structure](#project-structure)
13. [Roadmap](#roadmap)
14. [Verified Stable State](#verified-stable-state)
15. [Contributing](#contributing)
16. [License](#license)

---

## What is Adhera?

Medication non-adherence affects an estimated **50% of patients** with chronic conditions. Patients rely on paper prescriptions, memory, and generic phone alarms — none of which provide structured tracking, feedback loops, or provider visibility.

Adhera is a web-based medication adherence platform that:

- Sends patients **automated dose reminders** via email and browser notifications
- Lets patients respond in one tap: **Taken, Missed, or Snooze**
- Maintains an **append-only, tamper-proof** medication history
- Gives healthcare providers **real-time adherence dashboards** and emergency side-effect alerts
- Escalates **Severity 4 emergency reports** to providers and emergency contacts within 60 seconds

---

## Key Features

### For Patients

- Register medications with flexible schedules (daily, specific weekdays, alternate days, or PRN)
- Receive email and browser push reminders per dose slot (Morning / Afternoon / Evening / Night)
- Mark doses as Taken, Missed, or Snooze (up to 3× per dose; auto-expires after 2 hours)
- Submit side-effect reports with severity grading (1 = Mild → 4 = Emergency)
- View daily, weekly (ISO 8601), and monthly adherence rates on a live dashboard
- Export personal data at any time (JSON / CSV)

### For Healthcare Providers

- Dashboard showing all assigned patients with overall adherence rates
- Critical alert indicator for any patient with weekly adherence below 70%
- Full per-patient drill-down: medication history, adherence breakdown, feedback records
- Emergency email alert within 60 seconds of a patient submitting a Severity 4 report
- Export patient adherence reports as PDF or CSV

### For Administrators

- **Platform Identity Directory**: Full searchable, filterable registry of all platform patients and providers with 6-tab deep-dive views (Profile & Demographics, Medications, Adherence History with CSV export, Side-Effect Feedback, Doctor Assignments, and Audit Trail) with reason-audited status toggle
- Approve or reject Healthcare Provider registrations with a mandatory written reason
- Manage patient-to-provider assignments
- Create, deactivate, and reactivate accounts for all roles
- Audit log of all security-relevant events (retained ≥ 5 years)

---

## User Roles

| Role | Description |
| --- | --- |
| **Patient** | Self-registered; manages their own medication schedule and adherence records |
| **Healthcare Provider** | Administrator-verified medical professional; monitors assigned patients' compliance data |
| **Administrator** | System operator; manages accounts, verifies providers, handles assignments |
| **Caregiver** | *(v2.0 roadmap)* Delegated read-access for family members or professional carers |

---

## Architecture Overview

The system is deployed on three tiers:

- **Frontend:** deployed on Vercel (static)
- **Backend:** FastAPI deployed as Vercel Serverless Functions via `api/index.py`
- **Database:** Supabase (PostgreSQL 15+)
- **Email:** Resend via custom SMTP
- **Notifications:** Web Push API with VAPID keys + Supabase Edge Functions

| Tier | Technology | Responsibility |
| --- | --- | --- |
| **Presentation** | React 18, Vite, TypeScript, Vanilla CSS | SPA UI rendering, client-side routing, state management |
| **API** | Python 3.10+, FastAPI | Business logic, request validation, orchestration |
| **Data** | Supabase (PostgreSQL 15+) | Persistence, RLS enforcement, scheduled jobs |
| **Notification** | pg_cron + Edge Functions | Reminder dispatch, retry logic, email delivery |
| **Auth** | Supabase Auth | Token lifecycle, MFA, password hashing |
| **AI Chat** | Gemini API | In-app health assistant with medication context |

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- A [Supabase](https://supabase.com) project (free tier works for development)
- Node.js (only if using the Supabase CLI locally)
- A [Resend](https://resend.com) account for transactional email

### Local Setup Steps

```bash
git clone https://github.com/24co35-ops/ADHERA.git
cd ADHERA
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

1. Fill in `.env` with your Supabase and Resend credentials
2. Run backend: `uvicorn app.main:app --reload --port 8000`
3. Run frontend: `cd frontend && npm install && npm run dev`

---

## Environment Variables

Create a `.env` file in the project root. **Never commit this file.**

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGci...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...   # Used for admin operations only
SUPABASE_JWT_SECRET=your-jwt-secret

# Email
RESEND_API_KEY=re_...

# VAPID Keys for Web Push
VAPID_PUBLIC_KEY=your-vapid-public-key
VAPID_PRIVATE_KEY=your-vapid-private-key
VAPID_CLAIMS_EMAIL=mailto:your@email.com

# App
CORS_ORIGIN=http://localhost:8080        # Set to your frontend origin in production
ENVIRONMENT=development                  # development | production
REDIS_URL=redis://...                    # Optional connection string for Redis / Upstash serverless rate limit storage
```

> All credentials are loaded from environment variables. Secrets are **never** stored in source code or committed to version control.

---

## Database Setup

Adhera uses Supabase migrations. Each increment adds a numbered migration file.

```bash
# Install Supabase CLI (if not already installed)
npm install -g supabase

# Link to your Supabase project
supabase link --project-ref your-project-ref

# Apply all migrations
supabase db push
```

Migrations are stored in `supabase/migrations/` and run in order.

---

## Running the Application

### Backend (FastAPI)

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.  
Interactive API docs (Swagger UI) at `http://localhost:8000/docs`.

### Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:3000`.

---

## API Reference

All endpoints are versioned under `/v1`. Full interactive documentation is available at `/docs` when the server is running.

| Group | Base Path | Description |
| --- | --- | --- |
| Auth | `/v1/auth` | Registration, login, logout, password reset |
| Profile | `/v1/profile` | Profile management, emergency contact, VAPID |
| Medicines | `/v1/medicines` | Medicine CRUD |
| Reminders | `/v1/medicines/{id}/reminders` | Reminder slot management |
| Doses | `/v1/doses` | Mark Taken / Missed / Snooze, view history |
| Feedback | `/v1/feedback` | Side-effect reports |
| Analytics | `/v1/analytics` | Dashboard data, adherence rates, trends |
| Insights | `/v1/insights` | AI-generated adherence insights and alerts |
| Wellness | `/v1/wellness` | Wellness sessions and lifestyle tracking |
| Chat | `/v1/chat` | In-app AI health assistant (Gemini) |
| Provider | `/v1/provider` | Patient monitoring, report export |
| Admin | `/v1/admin` | User management, assignments, approvals |

---

## Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=term-missing
```

---

## Deployment

The app is deployed on Vercel at [https://adhera-seven.vercel.app](https://adhera-seven.vercel.app)

- **Frontend:** React + Vite SPA (Vercel Static Build)
- **Backend:** Vercel Serverless Functions (Python)
- **Entry point:** `api/index.py`
- **CI/CD:** GitHub Actions → auto-deploys to Vercel on push to `main`

### Deploy your own instance

1. Fork the repository
2. Import into Vercel
3. Add all environment variables in Vercel dashboard > Settings > Environment Variables
4. Push to `main` to trigger a deployment

---

## Project Structure

```text
adhera/
├── api/
│   └── index.py                 # Vercel Serverless entry point
├── app/
│   ├── main.py                  # FastAPI app entry point
│   ├── auth/                    # JWT validation, login, registration
│   ├── medicines/               # Medicine CRUD, schemas, validators
│   ├── reminders/               # Reminder slot management
│   ├── doses/                   # Dose logging and adherence calc
│   ├── feedback/                # Side-effect report submission
│   ├── analytics/               # Dashboard stats, trend computation
│   ├── insights/                # AI-generated adherence insights
│   ├── wellness/                # Wellness session tracking
│   ├── chat/                    # Gemini-powered health assistant
│   ├── profile/                 # Profile management, emergency contacts
│   ├── provider/                # Provider patient views and exports
│   ├── admin/                   # Admin directory, approvals, audit log
│   ├── services/                # Shared services (email, audit, push)
│   ├── core/                    # Shared utils, response models
│   └── db/                      # Supabase client setup
├── supabase/
│   ├── migrations/              # Numbered SQL migrations
│   └── functions/               # Edge Functions (reminders, emergency alerts)
├── frontend/
│   ├── src/
│   │   ├── components/          # Reusable UI & layout components
│   │   ├── pages/               # Patient, Provider, Admin & Auth pages
│   │   ├── stores/              # Zustand auth & app state
│   │   ├── lib/                 # API client, config loader
│   │   └── types/               # TypeScript interfaces & API types
│   ├── public/                  # Static assets, service worker
│   └── index.html               # Vite SPA entry point
├── tests/                       # 306 pytest unit & integration tests
├── .env.example
├── requirements.txt
├── DESIGN_DOC.md
├── PRD.md
├── TECH_STACK.md
└── README.md
```

---

## Roadmap

| Version | Status | Additions |
| --- | --- | --- |
| v1.0 | ✅ Live | Core platform, all modules, Vercel deployment |
| v1.1 | ✅ Live | Gemini AI health assistant, wellness tracking, adherence insights |
| v1.2 | 🔧 In Progress | Push notification stability, email confirmation via Resend |
| v2.0 | 📋 Planned | Caregiver access, multi-language, native iOS/Android |
| Future | 📋 Planned | EHR integration, drug interaction checking, telemedicine |

---

## Verified Stable State

✅ **Authentication & Session Management**: Supabase Auth integration with registration (`/auth/register`), login (`/auth/login`), silent refresh (`/auth/refresh`), and Two-Step TOTP Multi-Factor Authentication (MFA) step support. Resilient session handling against background transient 401s.
✅ **Patient Dashboard & Health Tracking**: Real-time adherence rate calculations, medication scheduling, and Chart.js adherence trend visualization.
✅ **Medicine Management**: Full CRUD (add, edit, soft delete) with dosage, frequencies, and reminder time slots.
✅ **Dose & Adherence Tracking**: Log dose states (Taken, Missed, Snooze) with timestamp tracking and adherence percentage calculation.
✅ **Side-Effect Feedback**: Log side-effect records with 1–4 severity grading linked to specific medications and patient records.
✅ **Provider & Admin Dashboards**: Provider patient list with compliance alerts and admin user role approval workflows.
✅ **Data Export**: Direct JSON and CSV streaming for patient health and adherence records.
✅ **Testing & Quality Assurance**: 306/306 passing pytest unit and integration tests across auth, medicines, doses, feedback, analytics, admin, insights, wellness, and chat modules; automated frontend build and type-checking.
✅ **Accessibility & Design Standards**: Dark-themed UI with glassmorphism styling, high-contrast cyan accents, and WCAG 2.1 AA compliant accessibility foundations.
✅ **Live Deployment**: Hosted on Vercel at [https://adhera-seven.vercel.app](https://adhera-seven.vercel.app).

---

## Contributing

1. Fork the repository and create a feature branch from `main`.
2. Follow the incremental development model (see `PRD.md` — Section 10, Timeline).
3. Ensure all tests pass and coverage does not drop below 80%.
4. Run `axe-core` or equivalent on any changed UI pages before submitting a PR.
5. Never commit secrets, `.env` files, or `SUPABASE_SERVICE_ROLE_KEY` to version control.
6. All production deployments must be traceable to a specific tagged release commit.

---

## License

This project is licensed under the [MIT License](LICENSE).

Copyright (c) 2026 24co35-ops

---

> **Disclaimer:** Adhera is a reminder and tracking tool only. It does not provide medical advice, replace clinical supervision, or guarantee medication safety or efficacy.
