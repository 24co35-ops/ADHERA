# Adhera — Medication Adherence Platform

> *Help patients stay on track with their medication and give doctors the data they need to intervene before non-adherence becomes a health crisis.*

**Version:** 1.0 · **Status:** Draft · **Authors:** Mehtab Shaikh, Ashwith Shetty  
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
14. [Contributing](#contributing)
15. [License](#license)

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
- Approve or reject Healthcare Provider registrations with a mandatory written reason
- Manage patient-to-provider assignments
- Create, deactivate, and reactivate accounts for all roles
- Audit log of all security-relevant events (retained ≥ 5 years)

---

## User Roles

| Role | Description |
|---|---|
| **Patient** | Self-registered; manages their own medication schedule and adherence records |
| **Healthcare Provider** | Administrator-verified medical professional; monitors assigned patients' compliance data |
| **Administrator** | System operator; manages accounts, verifies providers, handles assignments |
| **Caregiver** | *(v2.0 roadmap)* Delegated read-access for family members or professional carers |

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                        ADHERA SYSTEM                         │
│                                                              │
│  ┌──────────────┐     HTTPS / REST    ┌──────────────────┐   │
│  │   Frontend   │ ──────────────────► │  FastAPI Backend  │   │
│  │ HTML/CSS/JS  │ ◄────────────────── │  (Python 3.10+)  │   │
│  │  (Browser)   │                     └────────┬─────────┘   │
│  └──────────────┘                              │             │
│                                                │             │
│  ┌─────────────────────────────────────────────▼──────────┐  │
│  │                    SUPABASE PLATFORM                    │  │
│  │                                                         │  │
│  │  ┌───────────┐  ┌──────────┐  ┌──────────┐  ┌───────┐  │  │
│  │  │  Supabase │  │PostgreSQL│  │ Realtime │  │ Edge  │  │  │
│  │  │   Auth    │  │   15+    │  │  (WS)    │  │  Fn.  │  │  │
│  │  └───────────┘  └──────────┘  └──────────┘  └───┬───┘  │  │
│  │                      ▲                           │      │  │
│  │              ┌───────┴────────┐                  │      │  │
│  │              │    pg_cron     │                  │      │  │
│  │              │  (scheduler)   │                  │      │  │
│  │              └────────────────┘                  │      │  │
│  └───────────────────────────────────────────────────┘  │  │
│                                                          │  │
│  ┌───────────────────────────────────────────────────────▼─┐  │
│  │           Email Provider (Resend / SendGrid)             │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

The system is built on three tiers:

| Tier | Technology | Responsibility |
|---|---|---|
| **Presentation** | HTML5, CSS3, JS + Alpine.js | UI rendering, Supabase Realtime subscriptions |
| **API** | Python 3.10+, FastAPI | Business logic, request validation, orchestration |
| **Data** | Supabase (PostgreSQL 15+) | Persistence, RLS enforcement, scheduled jobs |
| **Notification** | pg_cron + Edge Functions | Reminder dispatch, retry logic, email delivery |
| **Auth** | Supabase Auth | Token lifecycle, MFA, password hashing |

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- A [Supabase](https://supabase.com) project (free tier works for development)
- Node.js (only if using the Supabase CLI locally)
- A [Resend](https://resend.com) or SendGrid account for transactional email

### Clone the Repository

```bash
git clone https://github.com/your-org/adhera.git
cd adhera
```

### Install Python Dependencies

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file in the project root. **Never commit this file.**

```bash
# Supabase
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=eyJhbGci...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...   # Used for admin operations only
SUPABASE_JWT_SECRET=your-jwt-secret

# Email
RESEND_API_KEY=re_...

# App
CORS_ORIGIN=http://localhost:3000        # Set to your frontend origin in production
ENVIRONMENT=development                  # development | production
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

Migrations are stored in `supabase/migrations/` and run in order:

```
supabase/migrations/
├── 20250101_001_create_profiles.sql
├── 20250101_002_create_medicines.sql
├── 20250101_003_create_reminders.sql
├── 20250101_004_create_adherence.sql
├── 20250101_005_enable_rls.sql
└── ...
```

---

## Running the Application

### Backend (FastAPI)

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.  
Interactive API docs (Swagger UI) at `http://localhost:8000/docs`.

### Frontend

Open `frontend/index.html` directly in your browser, or serve it via any static file server:

```bash
# Python quick server
python -m http.server 3000 --directory frontend
```

### Supabase Edge Functions (local)

```bash
supabase functions serve dispatch-reminder --env-file .env
```

---

## API Reference

All endpoints are versioned under `/v1`. Full interactive documentation is available at `/docs` when the server is running.

| Group | Base Path | Description |
|---|---|---|
| Auth | `/v1/auth` | Registration, login, logout, password reset |
| Profile | `/v1/profile` | Profile management, emergency contact |
| Medicines | `/v1/medicines` | Medicine CRUD |
| Reminders | `/v1/medicines/{id}/reminders` | Reminder slot management |
| Doses | `/v1/doses` | Mark Taken / Missed / Snooze, view history |
| Feedback | `/v1/feedback` | Side-effect reports |
| Analytics | `/v1/analytics` | Dashboard data, adherence rates, trends |
| Provider | `/v1/provider` | Patient monitoring, report export |
| Admin | `/v1/admin` | User management, assignments, approvals |

### Standard Response Format

```json
{
  "success": true,
  "data": { },
  "meta": {
    "timestamp": "2025-01-01T10:00:00Z",
    "version": "1.0"
  }
}
```

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Email address is already registered",
    "field": "email"
  }
}
```

---

## Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=term-missing

# Run a specific test group
pytest tests/test_doses.py
pytest tests/test_auth.py
```

### Test Coverage Targets

| Layer | Framework | Target |
|---|---|---|
| Unit | pytest | ≥ 80% of business logic |
| Integration | pytest + Supabase test project | All API endpoints |
| Security | OWASP ZAP + manual | No Critical/High findings |
| Performance | Locust | NFR targets at Standard Operating Load |
| Accessibility | axe-core + manual screen reader | Zero WCAG 2.1 AA violations |
| Timezone regression | pytest (simulated DST) | DST spring-forward and fall-back |

---

## Deployment

### CI/CD Pipeline

```
Push to main
    │
    ▼
GitHub Actions
├── pytest (unit + integration)
├── axe-core accessibility scan
├── gitleaks (secrets scan)
└── Build passes?
        │
        ▼
Deploy FastAPI → Render / Railway
        │
        ▼
Deploy Frontend → Vercel / Netlify
        │
        ▼
Run Supabase migrations (supabase db push)
        │
        ▼
Smoke test (GET /v1/health)
```

### Deployment Tiers

| Tier | Users | Concurrent Sessions | Infrastructure |
|---|---|---|---|
| **Tier 1** — Development / Pilot | 1,000 | 100 | Supabase Free → Pro · Render/Vercel free |
| **Tier 2** — Production | 5,000 | 500 | Supabase Pro + compute add-on · Render paid |
| **Tier 3** — Scale Target | 10,000 | 1,000 | Supabase Team/Enterprise · Horizontal FastAPI scaling |

---

## Project Structure

```
adhera/
├── app/
│   ├── main.py                  # FastAPI app entry point
│   ├── auth/
│   │   └── dependencies.py      # JWT validation, role guards
│   ├── routers/
│   │   ├── auth.py
│   │   ├── profile.py
│   │   ├── medicines.py
│   │   ├── reminders.py
│   │   ├── doses.py
│   │   ├── feedback.py
│   │   ├── analytics.py
│   │   ├── provider.py
│   │   └── admin.py
│   ├── models/                  # Pydantic request/response schemas
│   ├── services/                # Business logic layer
│   └── db/                      # Supabase client setup
├── supabase/
│   ├── migrations/              # Numbered SQL migrations
│   └── functions/
│       └── dispatch-reminder/   # Edge Function for notification dispatch
├── frontend/
│   ├── index.html               # Landing / Login
│   ├── dashboard.html           # Patient dashboard
│   ├── medicines.html
│   ├── provider/
│   ├── admin/
│   ├── css/
│   └── js/
├── tests/
│   ├── test_auth.py
│   ├── test_medicines.py
│   ├── test_doses.py
│   ├── test_feedback.py
│   ├── test_analytics.py
│   └── test_timezone.py
├── .env.example                 # Template — copy to .env and fill in values
├── requirements.txt
├── DESIGN_DOC.md
├── PRD.md
├── TECH_STACK.md
└── README.md
```

---

## Roadmap

| Version | Planned Additions |
|---|---|
| **v1.0** | Core platform: registration, medicine management, reminders, dose tracking, feedback, analytics, provider and admin modules |
| **v2.0** | Caregiver delegated access, multi-language (i18n), native iOS/Android app |
| **Future** | EHR integration, drug interaction checking, telemedicine messaging |

---

## Verified Stable State

All core functionalities have been fixed and verified locally:
* **Auth & Schema**: Fixed `profiles.email` query errors by retrieving emails directly from Supabase Auth admin API. Admin login and credentials restored.
* **UI**: Resolved Chart.js infinite recursion (`Maximum call stack size exceeded`) in dashboards by moving chart instances out of Alpine.js reactive proxies.
* **Testing**: 27/27 backend unit tests passing.

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

This project is developed as an academic software engineering project.  
© 2025 Mehtab Shaikh, Ashwith Shetty. All rights reserved.

---

> **Disclaimer:** Adhera is a reminder and tracking tool only. It does not provide medical advice, replace clinical supervision, or guarantee medication safety or efficacy.
