# Adhera — Tech Stack

**Version:** 1.0 · **Authors:** Mehtab Shaikh, Ashwith Shetty

This document describes every technology, library, and service used in the Adhera platform, with the rationale for each choice.

---

## Table of Contents

1. [Overview](#overview)
2. [Backend](#backend)
3. [Database and Platform](#database-and-platform)
4. [Authentication](#authentication)
5. [Notification System](#notification-system)
6. [Frontend](#frontend)
7. [Testing](#testing)
8. [DevOps and Deployment](#devops-and-deployment)
9. [Security Libraries](#security-libraries)
10. [Full Dependency List](#full-dependency-list)
11. [Architecture Decisions](#architecture-decisions)

---

## Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│  Layer              Technology                  Version / Notes       │
│──────────────────────────────────────────────────────────────────────│
│  Language           Python                      3.10+                 │
│  API Framework      FastAPI                     0.110+                │
│  ASGI Server        Uvicorn                     0.29+                 │
│  Database           PostgreSQL (via Supabase)   15+                   │
│  BaaS Platform      Supabase                    latest                │
│  Auth               Supabase Auth               (JWT / bcrypt)        │
│  Scheduling         Supabase pg_cron            built-in              │
│  Serverless Fn.     Supabase Edge Functions     (Deno runtime)        │
│  Email              Resend                      (or SendGrid)         │
│  Push Notif.        Web Push Protocol           W3C standard          │
│  Frontend JS        Alpine.js                   3.x                   │
│  Frontend CSS       Tailwind CSS                (CDN)                 │
│  Charts             Chart.js                    4.x                   │
│  Realtime           Supabase Realtime           (WebSocket)           │
│  Deployment         Render / Railway            (FastAPI)             │
│  Frontend Host      Vercel / Netlify            (static)              │
│  CI/CD              GitHub Actions              —                     │
│  Migrations         Supabase CLI                —                     │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Backend

### Python 3.10+

The primary implementation language. Python 3.10 is the minimum due to use of structural pattern matching and modern type annotation syntax.

### FastAPI

**Why FastAPI over Flask or Django:**

| Criterion | Flask | Django | FastAPI |
|---|---|---|---|
| Async support | Limited (Flask-Async) | Limited (ASGI add-on) | Native async/await |
| Request validation | Manual / Marshmallow | Django Forms / DRF | Built-in via Pydantic |
| API docs | Flask-RESTX / Flasgger | DRF Spectacular | Auto-generated (OpenAPI 3.0) |
| Performance | Moderate | Moderate | High (Starlette core) |
| Type safety | Optional | Optional | First-class |
| Boilerplate | Low | High | Low |

FastAPI auto-generates OpenAPI 3.0 documentation (Swagger UI at `/docs`, ReDoc at `/redoc`), enforces Pydantic schema validation on every request, and runs on the Starlette ASGI framework for full async compatibility.

### Uvicorn

ASGI server for running FastAPI in production. Used with Gunicorn workers for multi-process deployment.

```bash
# Development
uvicorn app.main:app --reload

# Production
gunicorn app.main:app -k uvicorn.workers.UvicornWorker --workers 4
```

### Pydantic v2

All API request bodies and response models are defined as Pydantic models. This enforces type validation, automatic serialisation, and generates accurate OpenAPI schemas. Replaces manual validation code entirely.

### python-jose / PyJWT

Used for JWT signature verification against Supabase's JWKS endpoint. FastAPI dependency injection (`Depends`) wraps the token validation so every protected route is automatically guarded.

### supabase-py

Official Python client for Supabase. Used for all database reads and writes, Storage access, and calling Edge Functions. Parameterised queries via the client prevent SQL injection.

```python
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
```

### python-dotenv

Loads environment variables from `.env` during local development. Not used in production (environment variables injected by the host platform).

---

## Database and Platform

### Supabase

Supabase is the data and operations platform. It provides PostgreSQL with a managed services layer.

**Why Supabase over raw PostgreSQL:**

| Capability | Raw PostgreSQL | Supabase |
|---|---|---|
| Authentication | Custom JWT system | Built-in Auth (bcrypt, JWT, MFA, email verification) |
| Row Level Security | Available, manual | First-class, dashboard-configurable |
| Realtime updates | Custom pg_notify + WebSocket server | Built-in Supabase Realtime |
| Scheduled jobs | Separate cron daemon | pg_cron built-in |
| Serverless functions | Not available | Edge Functions (Deno) |
| Object storage | Not available | Supabase Storage |
| Automated backups | Manual setup | Daily backups on Pro+ (30-day retention) |
| Connection pooling | External PgBouncer needed | Built-in PgBouncer |

### PostgreSQL 15+

The underlying relational database. Key features used:

- **Row Level Security (RLS):** Enforces RBAC at the database level. Patients can only see their own rows; providers can only see rows belonging to their Active-assigned patients.
- **UUID primary keys:** All tables use `gen_random_uuid()` as primary key.
- **JSONB columns:** Used for flexible `recurrence_params` (weekday bitmasks, alternate-day anchor dates) on the `reminders` table.
- **Partial unique indexes:** Enforces `one active assignment per patient` via a conditional unique constraint.
- **Triggers:** Used on `adherence` table to prevent application-level `UPDATE` or `DELETE`, enforcing logical immutability.
- **pg_cron:** Runs the auto-expiry job every minute to mark unanswered doses as Missed after 2 hours.

### Supabase Edge Functions (Deno)

Serverless TypeScript functions running on the Deno runtime, deployed and managed by Supabase. Used for:

- `dispatch-reminder` — sends email and push notifications per scheduled dose
- Retry logic stored in `notification_retries` table in Supabase (no external queue server needed)

### Supabase Storage

Private bucket for PDF and CSV report exports. Access is controlled via RLS policies on the bucket.

---

## Authentication

### Supabase Auth

Adhera delegates all authentication to Supabase Auth. The application does **not** implement its own token issuance, password hashing, or session management.

| Feature | Implementation |
|---|---|
| Password hashing | bcrypt (Supabase Auth internal) |
| Access token | JWT (HS256), 15-minute expiry |
| Refresh token | Supabase-managed, 7-day expiry, single-use |
| Token replay protection | Supabase Auth: replay triggers session family invalidation |
| Email verification | Supabase Auth built-in flow |
| Password reset | Supabase Auth: signed single-use link, 30-minute expiry |
| MFA | Supabase Auth TOTP (optional per account) |

FastAPI validates incoming JWTs by verifying the signature against the `SUPABASE_JWT_SECRET`:

```python
payload = jwt.decode(
    token,
    SUPABASE_JWT_SECRET,
    algorithms=["HS256"],
    audience="authenticated"
)
```

---

## Notification System

### Reminder Dispatch Architecture

No external job queue server (no Celery, Redis, or RabbitMQ). The full notification pipeline runs inside Supabase:

```
pg_cron (every 1 minute)
    │
    └─► SELECT due reminders from operational_state
            │
            └─► Call Edge Function: dispatch-reminder
                    ├── Resend API (email)
                    └── Web Push Protocol (browser push)
```

### Resend (transactional email)

Primary email provider. Resend offers a developer-friendly API, high deliverability, and generous free tier. SendGrid is a supported alternative.

```typescript
// Inside Edge Function
const resend = new Resend(Deno.env.get("RESEND_API_KEY"))
await resend.emails.send({ from, to, subject, html })
```

### Web Push Protocol (W3C)

Browser push notifications use the W3C Push API. Push subscriptions are stored per-user; if the push service returns an error, the system falls back to email immediately. Push delivery failure does not trigger a separate retry cycle.

### Retry Strategy

All retry state persists in the `notification_retries` table in Supabase (not in process memory), so retries survive server restarts.

```
Attempt 1 → fail → +5 min → Attempt 2 → fail → +5 min → Attempt 3 → fail
                                                                    │
                                               Log failure to audit_log
                                               Set notification_failed = true
```

---

## Frontend

### Vanilla JavaScript + Alpine.js 3.x

**Why no React/Vue/Next.js:**

- No build step or bundler required — the frontend can be opened as static HTML
- Alpine.js provides reactive UI (x-data, x-bind, x-on) without a virtual DOM
- Significantly reduces project setup complexity for an academic project
- Full Supabase Realtime subscriptions work natively in vanilla JS

### Tailwind CSS (CDN)

Utility-first CSS framework loaded via CDN — no build pipeline. All standard base-stylesheet utility classes are available. Used for responsive layout, component styling, and dark/light theming.

### Chart.js 4.x

**Why Chart.js:**

- Supports `aria-label` and `aria-describedby` for WCAG 2.1 AA compliance
- Chart data points are keyboard-navigable (Tab + Arrow keys)
- Active community; well-documented; no build dependency
- Renders line charts (adherence trend) and bar charts (period comparison) with the same API

### Supabase JS Client

Used in the browser for:

- Supabase Realtime subscriptions (dashboard live updates on dose events)
- Uploading push subscription objects

All data reads and writes that require business logic validation go through the FastAPI backend, not directly from the browser to Supabase, except for Realtime subscriptions.

### Heroicons (inline SVG)

SVG icon set from Tailwind Labs. Inlined directly into HTML — no external font loading, full accessible `aria-label` support, no render-blocking request.

---

## Testing

### pytest

Primary testing framework for all backend unit and integration tests.

```bash
pytest --cov=app --cov-report=term-missing
```

### pytest-asyncio

Extension for testing `async` FastAPI route handlers and service functions.

### httpx

Async HTTP client used in integration tests to make requests against a running FastAPI `TestClient`.

### Locust

Load testing tool for verifying non-functional performance requirements:

- p95 API response time ≤ 2,000 ms at 500 concurrent sessions
- Reminder dispatch latency ≤ 60 seconds for ≥ 95% of dispatches

### OWASP ZAP

Security scanning for CSRF, XSS, injection, and other OWASP Top 10 vulnerabilities.

### axe-core

Automated WCAG 2.1 AA accessibility scanning, integrated into the CI pipeline. Zero Level A or AA violations required to pass.

---

## DevOps and Deployment

### GitHub Actions

CI/CD pipeline triggered on push to `main`:

1. Run pytest (unit + integration)
2. Run axe-core accessibility scan
3. Run gitleaks (secret scanning)
4. Deploy FastAPI to Render / Railway
5. Deploy frontend to Vercel / Netlify
6. Apply Supabase migrations (`supabase db push`)
7. Smoke test (`GET /v1/health`)

### Render / Railway (FastAPI hosting)

Managed PaaS platforms for hosting the FastAPI backend. Both support Python natively, environment variable injection, and zero-downtime deploys. Render is the default choice; Railway is the alternative.

### Vercel / Netlify (Frontend hosting)

Static file hosting for the HTML/CSS/JS frontend. Both offer global CDN, instant deploys from GitHub, and HTTPS by default.

### Supabase CLI

Used for local development and migration management:

```bash
supabase start             # Start local Supabase stack
supabase db push           # Apply migrations to remote project
supabase functions deploy  # Deploy Edge Functions
```

### gitleaks

Secret scanning tool run in CI to prevent accidental commitment of API keys, JWT secrets, or service role keys.

---

## Security Libraries

| Library | Purpose |
|---|---|
| `python-jose` / `PyJWT` | JWT decode and signature verification |
| `slowapi` | Rate limiting middleware for FastAPI (wraps limits) |
| `python-multipart` | Required by FastAPI for form data / file upload parsing |
| Supabase RLS | Database-level access control enforced on every query |
| `SameSite=Lax` cookies | CSRF mitigation for cookie-based token storage |
| Pydantic | Input sanitisation — all user input validated before any DB operation |

---

## Full Dependency List

### `requirements.txt`

```
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
gunicorn>=21.2.0
supabase>=2.0.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-jose[cryptography]>=3.3.0
python-multipart>=0.0.9
python-dotenv>=1.0.0
httpx>=0.27.0
slowapi>=0.1.9

# Testing
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-cov>=5.0.0
httpx>=0.27.0
locust>=2.28.0
```

### Edge Functions (Deno / `package.json`)

```json
{
  "imports": {
    "resend": "npm:resend@latest",
    "web-push": "npm:web-push@latest"
  }
}
```

### Frontend (CDN — no npm)

```html
<!-- Tailwind CSS -->
<script src="https://cdn.tailwindcss.com"></script>

<!-- Alpine.js -->
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>

<!-- Chart.js -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.x.x/dist/chart.umd.min.js"></script>

<!-- Supabase JS client -->
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
```

---

## Architecture Decisions

### Why not Celery + Redis for notifications?

Celery and Redis add operational complexity: a separate broker service, worker processes, and persistence configuration. Supabase pg_cron + Edge Functions achieve the same result (persistent, restartable job queue) entirely within the Supabase platform — one fewer infrastructure component to manage and monitor.

### Why not a SPA (React / Vue / Next.js)?

An academic project with a team familiar with vanilla JS does not benefit from the added complexity of a build pipeline, bundler, and component lifecycle management. Alpine.js provides the necessary reactivity (conditional rendering, form binding, fetch-and-render) without a compilation step.

### Why Supabase Auth instead of a custom JWT system?

Custom JWT systems require implementing password hashing, token issuance, refresh rotation, replay detection, email verification, and password reset flows — all with security correctness at each step. Supabase Auth provides all of these battle-tested, off the shelf, and integrates natively with the rest of the Supabase stack (RLS uses `auth.uid()` directly in policies).

### Why FastAPI instead of Flask or Django?

Django is optimised for full-stack web applications with server-side rendering — its ORM, templates, and admin panel are largely irrelevant when the frontend is a separate static HTML layer and the database is managed by Supabase. Flask lacks native async support and request validation. FastAPI provides native async/await, Pydantic validation, and auto-generated OpenAPI documentation with minimal configuration overhead.

### Why two token stores (stateless access + stateful refresh)?

Stateless access tokens (15-minute JWT) enable API requests without a database lookup on every call. Stateful refresh tokens (stored in Supabase's token store) enable logout, session revocation, and replay detection — capabilities that require server state. This matches the architecture specified in the MRFS SRS (MRFS-SRS-100 / SRS-101).

---

*Adhera — Tech Stack Document*  
*For implementation details, see `DESIGN_DOC.md`. For product requirements, see `PRD.md`.*
