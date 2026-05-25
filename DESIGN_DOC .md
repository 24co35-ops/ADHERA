# Adhera — Design Document

**Version:** 1.0  
**Status:** Draft  
**Authors:** Mehtab Shaikh, Ashwith Shetty  
**Last Updated:** 2025

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture](#2-architecture)
3. [Database Design](#3-database-design)
4. [Authentication and Security Design](#4-authentication-and-security-design)
5. [Notification System Design](#5-notification-system-design)
6. [API Design](#6-api-design)
7. [State Machines](#7-state-machines)
8. [Frontend Design](#8-frontend-design)
9. [Data Flow Diagrams](#9-data-flow-diagrams)
10. [Error Handling Strategy](#10-error-handling-strategy)
11. [Testing Strategy](#11-testing-strategy)
12. [Deployment Design](#12-deployment-design)

---

## 1. System Overview

Adhera is a three-tier web application with an independent notification subsystem. The system is built on Supabase as the data and auth platform, Python (FastAPI) as the API layer, and a responsive HTML/CSS/JS frontend.

### 1.1 High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                     ADHERA SYSTEM                           │
│                                                             │
│  ┌──────────────┐     HTTPS/REST      ┌──────────────────┐  │
│  │   Frontend   │ ──────────────────► │  FastAPI Backend  │  │
│  │ HTML/CSS/JS  │ ◄────────────────── │  (Python 3.10+)  │  │
│  │  (Browser)   │                     └────────┬─────────┘  │
│  └──────────────┘                              │            │
│                                                │ Supabase   │
│  ┌──────────────────────────────────────────────▼─────────┐  │
│  │                    SUPABASE PLATFORM                    │  │
│  │                                                         │  │
│  │  ┌───────────┐  ┌──────────┐  ┌──────────┐  ┌───────┐  │  │
│  │  │  Supabase │  │PostgreSQL│  │ Supabase │  │ Edge  │  │  │
│  │  │   Auth    │  │   15+    │  │ Realtime │  │  Fn.  │  │  │
│  │  └───────────┘  └──────────┘  └──────────┘  └───┬───┘  │  │
│  │                      ▲                           │      │  │
│  │              ┌───────┴────────┐                  │      │  │
│  │              │    pg_cron     │                  │      │  │
│  │              │  (scheduler)   │                  │      │  │
│  │              └────────────────┘                  │      │  │
│  └───────────────────────────────────────────────────┘  │  │
│                                                          │  │
│  ┌───────────────────────────────────────────────────────▼─┐  │
│  │              Email Provider (Resend / SendGrid)          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Architecture

### 2.1 Architecture Pattern

Adhera uses a **layered architecture** with strict separation between tiers:

| Tier | Technology | Responsibility |
|---|---|---|
| Presentation | HTML5, CSS3, JavaScript (Vanilla + Alpine.js) | UI rendering, user interaction, Supabase Realtime subscriptions |
| API | Python 3.10+, FastAPI | Business logic, request validation, orchestration |
| Data | Supabase (PostgreSQL 15+) | Data persistence, RLS enforcement, scheduled jobs |
| Notification | Supabase pg_cron + Edge Functions | Reminder dispatch, retry logic, email delivery |
| Auth | Supabase Auth | User authentication, token lifecycle, MFA |
| Storage | Supabase Storage | PDF/CSV export files, private bucket |

### 2.2 Why Supabase Over Raw PostgreSQL

| Capability | Raw PostgreSQL | Supabase |
|---|---|---|
| Authentication | Custom JWT system required | Built-in Auth with bcrypt, JWT, MFA |
| Row Level Security | Available but manual setup | First-class feature with dashboard UI |
| Realtime updates | Requires pg_notify + websocket server | Built-in Supabase Realtime |
| Scheduled jobs | Requires separate cron daemon | pg_cron built-in |
| Serverless functions | Not available | Edge Functions (Deno runtime) |
| Object storage | Not available | Supabase Storage |
| Backups | Manual setup | Automated daily backups on Pro+ |

### 2.3 Deployment Tiers

```
Tier 1 — Development / Small Pilot
├── Supabase Free → Supabase Pro
├── 1,000 registered users
├── 100 concurrent sessions
└── Vercel / Render free tier for FastAPI

Tier 2 — Production (Standard Operating Load)
├── Supabase Pro + 4 GB RAM compute add-on
├── 5,000 registered users
├── 500 concurrent sessions
└── Render or Railway (paid) for FastAPI

Tier 3 — Scale Target
├── Supabase Team / Enterprise
├── 10,000 registered users
├── 1,000 concurrent sessions
└── Horizontal scaling of FastAPI instances
```

---

## 3. Database Design

### 3.1 Schema Overview

Adhera uses Supabase (PostgreSQL 15+). The `auth.users` table is managed by Supabase Auth. All application tables reference it via foreign key.

> **Soft delete policy:**  
> Entity tables (`profiles`, `assignments`, `medicines`, `reminders`) use `is_active = false` for deletion.  
> Append-only tables (`adherence`, `feedback`, `audit_log`) are never soft-deleted or modified.

### 3.2 Table Definitions

#### `profiles` — extends Supabase `auth.users`

```sql
create table public.profiles (
  id           uuid primary key references auth.users(id) on delete cascade,
  full_name    text not null,
  role         text not null check (role in ('patient', 'provider', 'admin')),
  date_of_birth date,
  contact_number text,
  timezone     text not null default 'UTC',
  is_active    boolean not null default true,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);

-- Unique email is enforced by auth.users
```

#### `assignments` — patient-to-provider

```sql
create table public.assignments (
  id           uuid primary key default gen_random_uuid(),
  patient_id   uuid not null references auth.users(id),
  provider_id  uuid not null references auth.users(id),
  status       text not null check (status in ('active', 'inactive')) default 'active',
  assigned_on  timestamptz not null default now(),
  note         text,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now(),

  -- Enforce: patient has at most one active assignment
  constraint one_active_assignment unique nulls not distinct (patient_id, status)
    where (status = 'active')
);
```

#### `medicines`

```sql
create table public.medicines (
  id               uuid primary key default gen_random_uuid(),
  user_id          uuid not null references auth.users(id),
  name             text not null,
  dosage_amount    numeric not null,
  dosage_unit      text not null check (dosage_unit in ('mg', 'ml', 'units')),
  route            text not null check (route in ('oral', 'topical', 'injection', 'inhaled', 'other')),
  frequency_type   text not null check (frequency_type in ('daily', 'weekday', 'alternate', 'prn')),
  recurrence_params jsonb,        -- weekday bitmask or anchor_date for alternate-day
  start_date       date not null,
  end_date         date,
  instructions     text,
  is_active        boolean not null default true,
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now()
);
```

#### `reminders`

```sql
create table public.reminders (
  id               uuid primary key default gen_random_uuid(),
  medicine_id      uuid not null references public.medicines(id),
  user_id          uuid not null references auth.users(id),
  dose_label       text not null check (dose_label in ('morning', 'afternoon', 'evening', 'night')),
  dose_time_utc    time not null,
  timezone         text not null,
  recurrence_type  text not null,
  recurrence_params jsonb,
  is_active        boolean not null default true,
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now(),

  -- Uniqueness: no duplicate slots
  constraint unique_reminder_slot unique (
    medicine_id, dose_label, recurrence_type, recurrence_params, dose_time_utc
  )
);
```

#### `adherence` — append-only

```sql
create table public.adherence (
  id              uuid primary key default gen_random_uuid(),
  reminder_id     uuid not null references public.reminders(id),
  user_id         uuid not null references auth.users(id),
  scheduled_utc   timestamptz not null,
  status          text not null check (status in ('taken', 'missed', 'superseded')),
  outcome_utc     timestamptz not null default now(),
  supersedes_id   uuid references public.adherence(id),  -- for admin corrections
  correction_note text,
  created_at      timestamptz not null default now()
  -- No updated_at: append-only table
);

-- Prevent application-level UPDATE/DELETE via RLS + trigger
create or replace function prevent_adherence_modification()
returns trigger language plpgsql as $$
begin
  if tg_op = 'UPDATE' then
    raise exception 'adherence records are immutable';
  end if;
  return old;
end;
$$;
create trigger adherence_immutable
  before update or delete on public.adherence
  for each row execute function prevent_adherence_modification();
```

#### `feedback` — append-only

```sql
create table public.feedback (
  id              uuid primary key default gen_random_uuid(),
  user_id         uuid not null references auth.users(id),
  medicine_id     uuid not null references public.medicines(id),
  description     text not null check (char_length(description) <= 2000),
  severity        smallint not null check (severity between 1 and 4),
  occurred_at     timestamptz not null,
  references_id   uuid references public.feedback(id),  -- patient correction reference
  created_at      timestamptz not null default now()
);
```

#### `emergency_contacts`

```sql
create table public.emergency_contacts (
  id           uuid primary key default gen_random_uuid(),
  user_id      uuid not null references auth.users(id),
  full_name    text not null,
  relationship text not null,
  email        text not null,
  verified     boolean not null default false,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now(),

  -- One contact per patient regardless of verification state
  constraint one_contact_per_patient unique (user_id)
);
```

#### `reports` — read cache

```sql
create table public.reports (
  id           uuid primary key default gen_random_uuid(),
  user_id      uuid not null references auth.users(id),
  period_type  text not null check (period_type in ('daily', 'weekly', 'monthly')),
  period_start date not null,
  period_end   date not null,
  total_doses  integer not null,
  doses_taken  integer not null,
  doses_missed integer not null,
  adherence_rate numeric(5,1) not null,
  is_stale     boolean not null default false,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);
```

#### `audit_log` — append-only

```sql
create table public.audit_log (
  id          uuid primary key default gen_random_uuid(),
  actor_id    uuid references auth.users(id),
  action_code text not null,   -- e.g. 'LOGIN_FAILED', 'ASSIGNMENT_CHANGED'
  target_id   uuid,            -- affected user/record
  reason      text,            -- for authorised access events
  created_at  timestamptz not null default now()
  -- No PHI, no free-text medication data
);
```

#### `disclaimer_acceptances`

```sql
create table public.disclaimer_acceptances (
  id               uuid primary key default gen_random_uuid(),
  user_id          uuid not null references auth.users(id),
  disclaimer_version text not null,
  accepted_at      timestamptz not null default now()
  -- Retained for account lifetime; non-deletable
);
```

### 3.3 Row Level Security Policies

RLS is enabled on all tables. The core policies are:

```sql
-- PROFILES: patients see only their own row
alter table public.profiles enable row level security;

create policy "patients_own_profile"
  on public.profiles for all
  using (auth.uid() = id);

create policy "providers_see_assigned_profiles"
  on public.profiles for select
  using (
    exists (
      select 1 from public.assignments
      where patient_id = profiles.id
        and provider_id = auth.uid()
        and status = 'active'
    )
  );

-- ADHERENCE: patients see own; providers see assigned patients'
alter table public.adherence enable row level security;

create policy "patients_own_adherence"
  on public.adherence for select
  using (user_id = auth.uid());

create policy "providers_see_assigned_adherence"
  on public.adherence for select
  using (
    exists (
      select 1 from public.assignments
      where patient_id = adherence.user_id
        and provider_id = auth.uid()
        and status = 'active'
    )
  );

-- FEEDBACK: same pattern as adherence
-- AUDIT_LOG: admin service role only (bypasses RLS)
-- All admin operations use Supabase service_role key
```

### 3.4 Indexes

```sql
-- Most queried lookups
create index idx_medicines_user_active    on public.medicines(user_id) where is_active = true;
create index idx_reminders_user_active    on public.reminders(user_id) where is_active = true;
create index idx_adherence_user           on public.adherence(user_id, scheduled_utc desc);
create index idx_adherence_reminder       on public.adherence(reminder_id, scheduled_utc desc);
create index idx_feedback_user            on public.feedback(user_id, created_at desc);
create index idx_assignments_patient      on public.assignments(patient_id, status);
create index idx_assignments_provider     on public.assignments(provider_id, status);
create index idx_audit_log_actor          on public.audit_log(actor_id, created_at desc);
```

---

## 4. Authentication and Security Design

### 4.1 Supabase Auth Integration

Adhera delegates all authentication to Supabase Auth. The application does **not** implement its own token issuance, password hashing, or session management.

```
┌────────────────────────────────────────────────────────┐
│                  Authentication Flow                    │
│                                                         │
│  Browser ──► POST /auth/v1/token ──► Supabase Auth     │
│                                           │             │
│                                    ┌──────▼──────┐      │
│                                    │ access_token │      │
│                                    │ (JWT, 15min) │      │
│                                    │ refresh_token│      │
│                                    │  (7 days)   │      │
│                                    └──────┬──────┘      │
│                                           │             │
│  Browser stores tokens ◄──────────────────┘             │
│  (memory or httpOnly cookie)                            │
│                                                         │
│  API requests: Authorization: Bearer <access_token>    │
│  FastAPI validates JWT signature against Supabase JWKS │
└────────────────────────────────────────────────────────┘
```

### 4.2 Token Validation in FastAPI

```python
# auth/dependencies.py
from supabase import create_client
import jwt

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_ANON_KEY = os.environ["SUPABASE_ANON_KEY"]
SUPABASE_JWT_SECRET = os.environ["SUPABASE_JWT_SECRET"]

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"
        )
        user_id = payload.get("sub")
        role = payload.get("user_metadata", {}).get("role")
        return {"user_id": user_id, "role": role}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### 4.3 Role-Based Access Control

Three layers enforce access control:

| Layer | Mechanism | Covers |
|---|---|---|
| Network | Supabase RLS policies | All direct DB access |
| API | FastAPI role dependency | Business logic routes |
| Admin | Supabase service role key | Admin-only operations (bypasses RLS) |

```python
# Role guards in FastAPI
def require_role(*roles: str):
    async def dependency(user = Depends(get_current_user)):
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return dependency

# Usage
@router.get("/patients")
async def get_patients(user = Depends(require_role("provider", "admin"))):
    ...
```

### 4.4 Security Checklist

| Concern | Implementation |
|---|---|
| Password hashing | Supabase Auth (bcrypt internally) |
| Access token | JWT, 15-min expiry, verified via JWKS |
| Refresh token | Supabase Auth managed, 7-day expiry |
| Token replay | Supabase Auth: single-use refresh tokens; replay triggers session family invalidation |
| Rate limiting | Middleware: 10 auth requests/throttle key/min |
| Input sanitisation | Pydantic models on all API inputs |
| SQL injection | Supabase client parameterised queries; no raw SQL string concat |
| CORS | FastAPI CORS middleware: authorised frontend origin only |
| CSRF | `SameSite=Lax` on cookies + Authorization header for API calls |
| Secrets | Environment variables; never in source code |
| Audit log | Append-only; admin access logged with reason code |

---

## 5. Notification System Design

### 5.1 Architecture

Adhera uses Supabase-native scheduling instead of a separate job queue server:

```
pg_cron job (every minute)
    │
    ▼
SELECT * FROM reminders
WHERE next_dispatch_utc <= now()
  AND is_active = true
    │
    ▼
For each due reminder:
    ├── Call Supabase Edge Function: dispatch-reminder
    │       ├── Email via Resend API
    │       └── Browser Push via Web Push Protocol
    │
    └── Update operational state store
        (set status = 'pending', reset snooze counter)
```

### 5.2 Edge Function: `dispatch-reminder`

```typescript
// supabase/functions/dispatch-reminder/index.ts
import { serve } from "https://deno.land/std/http/server.ts"
import { Resend } from "npm:resend"

const resend = new Resend(Deno.env.get("RESEND_API_KEY"))

serve(async (req) => {
  const { reminder_id, user_id, medicine_name, dosage, scheduled_utc } = await req.json()

  const results = { email: "pending", push: "pending" }

  // Email dispatch
  try {
    await resend.emails.send({
      from: "Adhera <reminders@adhera.app>",
      to: user_email,
      subject: `Time to take ${medicine_name}`,
      html: buildReminderEmail({ medicine_name, dosage, reminder_id })
    })
    results.email = "sent"
  } catch (err) {
    results.email = `failed: ${err.message}`
    await scheduleRetry(reminder_id, attempt_number + 1)
  }

  // Browser push dispatch (if subscription exists)
  if (push_subscription) {
    try {
      await sendWebPush(push_subscription, { medicine_name, dosage, reminder_id })
      results.push = "sent"
    } catch {
      results.push = "failed"
      // Push failure falls back to email; no separate retry for push
    }
  }

  await logDispatch(reminder_id, results)
  return new Response(JSON.stringify(results))
})
```

### 5.3 Retry Strategy

```
Attempt 1 → fail → wait 5 min → Attempt 2 → fail → wait 5 min → Attempt 3 → fail
     └─────────────────────────────────────────────────────────────────┘
                                        │
                              Log failure to system_events
                              Set notification_failed = true on dashboard
```

All retry state is stored in `notification_retries` table, persisted in Supabase — no separate queue server required.

### 5.4 Auto-Expiry Job

```sql
-- pg_cron: runs every minute
select cron.schedule(
  'auto-expire-doses',
  '* * * * *',
  $$
  insert into public.adherence (reminder_id, user_id, scheduled_utc, status)
  select
    os.reminder_id,
    os.user_id,
    os.scheduled_utc,
    'missed'
  from operational_state os
  where os.status in ('pending', 'snoozed')
    and os.scheduled_utc + interval '2 hours' < now()
    and not exists (
      select 1 from public.adherence a
      where a.reminder_id = os.reminder_id
        and a.scheduled_utc = os.scheduled_utc
    );
  $$
);
```

---

## 6. API Design

### 6.1 Base URL Structure

```
Production:  https://api.adhera.app/v1
Development: http://localhost:8000/v1
```

### 6.2 Endpoint Map

#### Authentication

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register` | Register new user |
| `POST` | `/auth/login` | Login; returns Supabase tokens |
| `POST` | `/auth/logout` | Revoke session |
| `POST` | `/auth/forgot-password` | Send signed reset link |
| `POST` | `/auth/reset-password` | Submit new password via reset link |
| `GET` | `/auth/verify-email` | Verify email token |

#### Profile

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/profile` | Get authenticated user's profile |
| `PATCH` | `/profile` | Update profile fields |
| `PATCH` | `/profile/password` | Change password |
| `GET` | `/profile/emergency-contact` | Get emergency contact |
| `PUT` | `/profile/emergency-contact` | Set or update emergency contact |
| `DELETE` | `/profile/emergency-contact` | Remove emergency contact |

#### Medicines

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/medicines` | List active medicines |
| `POST` | `/medicines` | Add medicine |
| `GET` | `/medicines/{id}` | Get medicine detail |
| `PATCH` | `/medicines/{id}` | Update medicine |
| `DELETE` | `/medicines/{id}` | Soft-delete medicine |

#### Reminders

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/medicines/{id}/reminders` | List reminders for a medicine |
| `POST` | `/medicines/{id}/reminders` | Add reminder slot |
| `PATCH` | `/reminders/{id}` | Update reminder |
| `DELETE` | `/reminders/{id}` | Deactivate reminder |

#### Dose Tracking

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/doses/{reminder_id}/taken` | Mark dose Taken |
| `POST` | `/doses/{reminder_id}/missed` | Mark dose Missed |
| `POST` | `/doses/{reminder_id}/snooze` | Snooze reminder (body: `{minutes: 15|30|60}`) |
| `GET` | `/doses/history` | Permanent Medication History (filterable) |

#### Feedback

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/feedback` | Submit side-effect report |
| `GET` | `/feedback` | List patient's feedback history |

#### Analytics

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/analytics/dashboard` | Patient dashboard data |
| `GET` | `/analytics/adherence` | Adherence rates (daily/weekly/monthly) |
| `GET` | `/analytics/trend` | Adherence trend for chart |

#### Provider

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/provider/patients` | List assigned patients |
| `GET` | `/provider/patients/{id}` | Patient detail |
| `GET` | `/provider/patients/{id}/report` | Generate report (PDF/CSV) |

#### Admin

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/admin/users` | List all users |
| `PATCH` | `/admin/users/{id}` | Activate / deactivate user |
| `GET` | `/admin/providers/pending` | Pending provider registrations |
| `POST` | `/admin/providers/{id}/approve` | Approve provider |
| `POST` | `/admin/providers/{id}/reject` | Reject provider |
| `GET` | `/admin/assignments` | List assignments |
| `POST` | `/admin/assignments` | Create assignment |
| `PATCH` | `/admin/assignments/{id}` | Update assignment |

### 6.3 Standard Response Format

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

### 6.4 Error Codes

| Code | HTTP Status | Description |
|---|---|---|
| `VALIDATION_ERROR` | 400 | Request body fails validation |
| `UNAUTHORIZED` | 401 | Missing or expired token |
| `FORBIDDEN` | 403 | Insufficient role permissions |
| `NOT_FOUND` | 404 | Resource does not exist |
| `CONFLICT` | 409 | Duplicate resource (e.g., email, reminder slot) |
| `RATE_LIMITED` | 429 | Too many requests |
| `SERVICE_UNAVAILABLE` | 503 | Database or external service down |

---

## 7. State Machines

### 7.1 Dose Status State Machine

```
                    ┌─────────────────┐
                    │                 │
          ┌─────────►    PENDING      ◄───────────┐
          │         │                 │            │
          │         └────────┬────────┘            │
          │                  │                     │
          │         ┌────────┴────────┐            │
          │         │  patient action  │            │
          │         └─┬──────┬──────┬─┘            │
          │           │      │      │               │
          │     ┌─────▼─┐   │   ┌──▼────┐          │
          │     │ TAKEN │   │   │MISSED │          │
          │     │(final)│   │   │(final)│          │
          │     └───────┘   │   └───────┘          │
          │                 │                       │
          │           ┌─────▼──────┐                │
          │           │  SNOOZED   │                │
          │           │ (max 3×)   │                │
          │           └─────┬──────┘                │
          │                 │                       │
          │    ┌────────────┤ snooze interval       │
          │    │            │ elapses               │
          │    │   ┌────────▼──────────────────┐    │
          │    │   │ Back to PENDING           │────┘
          │    │   │ (follow-up reminder sent) │
          │    │   └───────────────────────────┘
          │    │
          │    └──► MISSED (if 3rd snooze unanswered)
          │
          └── auto-expiry (2 h from original schedule time, fires on PENDING or SNOOZED)
```

**Key rules:**
- `PENDING` → `SNOOZED` resets snooze counter iff count < 3
- Auto-expiry timer is fixed at original scheduled time + 2h; snooze does not extend it
- `TAKEN` and `MISSED` are final; only admin superseding entries are allowed

### 7.2 Healthcare Provider Registration State Machine

```
REGISTERED ──► PENDING_APPROVAL ──► APPROVED ──► ACTIVE
                      │
                      └──► REJECTED (mandatory reason stored)
```

### 7.3 Emergency Contact State Machine

```
NONE ──► UNVERIFIED ──► VERIFIED ──► ALERTS_ACTIVE
              │               │
              └───────────────┴──► REMOVED ──► NONE
```

---

## 8. Frontend Design

### 8.1 Technology Choices

| Concern | Choice | Rationale |
|---|---|---|
| Language | Vanilla JavaScript + Alpine.js | No build step; fast iteration; Alpine handles reactivity without bundler complexity |
| Styling | Tailwind CSS (CDN) | Utility-first; no custom CSS build pipeline needed |
| Charts | Chart.js | Accessible; supports `aria-label`; keyboard navigation; WCAG-compatible |
| Realtime | Supabase JS client | Native Supabase Realtime subscriptions |
| Icons | Heroicons (SVG inline) | Accessible; no font loading required |

### 8.2 Page Structure

```
/                   → Landing / Login
/register           → Registration flow
/dashboard          → Patient dashboard (protected)
/medicines          → Medicine list + CRUD
/medicines/new      → Add medicine form
/medicines/:id      → Medicine detail + reminders
/history            → Permanent Medication History
/feedback           → Feedback submission + history
/profile            → Profile settings, timezone, emergency contact
/provider/dashboard → Healthcare Provider dashboard (protected)
/provider/patients/:id → Patient detail
/admin/dashboard    → Admin dashboard (protected)
/admin/users        → User management
/admin/assignments  → Assignment management
```

### 8.3 Supabase Realtime Subscription

```javascript
// Dashboard real-time updates
const channel = supabase
  .channel('patient-dashboard')
  .on(
    'postgres_changes',
    {
      event: '*',
      schema: 'public',
      table: 'adherence',
      filter: `user_id=eq.${user.id}`
    },
    (payload) => {
      updateDashboardAdherence(payload.new)
    }
  )
  .subscribe()

// Clean up on page leave
window.addEventListener('beforeunload', () => channel.unsubscribe())
```

### 8.4 Accessibility Requirements

- All form inputs have associated `<label>` elements
- Error messages use `role="alert"` for screen reader announcement
- Charts include `aria-label` describing data range, trend direction, high/low values
- Chart data points are keyboard-focusable (Tab navigation)
- Warning indicators use icon + text label (never colour alone)
- Modal dialogs trap focus and restore it on close
- All interactive elements reachable by keyboard; visible focus ring

---

## 9. Data Flow Diagrams

### 9.1 Patient Registers a Medicine and Gets a Reminder

```
Patient Browser          FastAPI              Supabase DB           Edge Function
     │                      │                      │                      │
     │── POST /medicines ──►│                      │                      │
     │                      │── INSERT medicine ──►│                      │
     │                      │── INSERT reminders──►│                      │
     │◄── 201 Created ───── │                      │                      │
     │                      │                      │                      │
     │                      │          pg_cron fires every minute         │
     │                      │                      │── SELECT due ───────►│
     │                      │                      │                      │
     │                      │                      │◄── due reminders ─── │
     │◄──────────── Email notification ────────────────────────────────── │
     │◄──────────── Browser Push (if supported) ───────────────────────── │
```

### 9.2 Patient Marks a Dose as Taken

```
Patient Browser          FastAPI              Supabase DB
     │                      │                      │
     │── POST /doses/:id/taken ──►│               │
     │                      │── RLS check ────────►│
     │                      │── INSERT adherence──►│  (status='taken', utc timestamp)
     │                      │── UPDATE op_state ──►│  (remove pending entry)
     │                      │── UPSERT report.stale►│
     │◄── 200 OK ──────────│                      │
     │                      │                      │──► Realtime event
     │◄──────────────────── Realtime update ────────────────────────────
     │ (dashboard Adherence Rate updates live)
```

### 9.3 Severity 4 Emergency Feedback

```
Patient Browser          FastAPI              Supabase DB      Edge Function    Provider
     │                      │                      │                │              │
     │── POST /feedback ───►│                      │                │              │
     │  (severity=4)        │── INSERT feedback ──►│                │              │
     │                      │── Trigger Edge Fn ──►│────────────────►              │
     │◄── 200 + on-screen   │                      │                │── Email ────►│
     │    emergency prompt  │                      │                │── Email ────►│ (emergency contact)
     │                      │                      │                │── LOG ──────►│
```

---

## 10. Error Handling Strategy

### 10.1 API Layer

```python
# Global exception handler in FastAPI
@app.exception_handler(Exception)
async def global_handler(request: Request, exc: Exception):
    if isinstance(exc, ValueError):
        return JSONResponse(status_code=400, content={"error": {"code": "VALIDATION_ERROR", "message": str(exc)}})
    if isinstance(exc, PermissionError):
        return JSONResponse(status_code=403, content={"error": {"code": "FORBIDDEN", "message": "Access denied"}})
    # Log unexpected errors; return safe message
    logger.exception("Unhandled error", exc_info=exc)
    return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"}})
```

### 10.2 Notification Failure Handling

| Failure Type | Behaviour |
|---|---|
| SMTP rejection (permanent) | Log, skip retries, mark failed |
| SMTP timeout | Retry up to 3× at 5-min intervals |
| Push service error | Fall back to email immediately |
| All channels failed | Mark `notification_failed=true` on operational state; show dashboard indicator |

### 10.3 Database Unavailability

- FastAPI returns HTTP 503 with maintenance message
- All database calls wrapped in try/except with structured logging
- Supabase Pro includes automated failover

---

## 11. Testing Strategy

### 11.1 Testing Layers

| Layer | Framework | Coverage Target |
|---|---|---|
| Unit | pytest | ≥ 80% of business logic |
| Integration | pytest + Supabase test project | All API endpoints |
| Security | OWASP ZAP + manual pen test | No Critical/High findings |
| Performance | Locust | NFR-01–05 verified at Standard Operating Load |
| Accessibility | axe-core + manual screen reader | Zero WCAG 2.1 AA violations |
| Timezone regression | pytest (simulated DST) | DST spring + fall for all IANA zones in use |

### 11.2 Key Test Scenarios

```
ADH-TEST-051: Dose auto-expiry
  Precondition: A dose is in Pending state at T=0
  Action:       System clock advances to T + 2h + 1min
  Expected:     Dose status is Missed in adherence table;
                dashboard shows missed count incremented
  Pass:         Status = 'missed', outcome_utc ≈ T+2h

ADH-TEST-059: Emergency escalation
  Precondition: Patient has verified provider + verified emergency contact
  Action:       POST /feedback {severity: 4}
  Expected:     (a) On-screen emergency prompt returned in response
                (b) Provider email sent within 60 seconds
                (c) Emergency contact email sent within 60 seconds
                (d) Both dispatches logged in system_events
  Pass:         Both emails delivered; log entries present

ADH-TEST-NFR-01: API p95 latency
  Load:         500 concurrent authenticated sessions
  Duration:     5 minutes
  Expected:     p95 ≤ 2,000 ms; error rate < 1%
```

---

## 12. Deployment Design

### 12.1 Environment Configuration

```bash
# Required environment variables
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGci...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...   # admin operations only
SUPABASE_JWT_SECRET=your-jwt-secret
RESEND_API_KEY=re_...
CORS_ORIGIN=https://adhera.app
ENVIRONMENT=production
```

### 12.2 Deployment Pipeline

```
Developer pushes to main
        │
        ▼
GitHub Actions CI
├── Run pytest (unit + integration)
├── Run axe-core accessibility scan
├── Check for secrets in code (gitleaks)
└── Build passes?
        │
        ▼
Deploy FastAPI to Render / Railway
        │
        ▼
Deploy frontend to Vercel / Netlify
        │
        ▼
Run Supabase migrations
        │
        ▼
Smoke test (health check endpoint)
```

### 12.3 Supabase Migration Strategy

```bash
# Each increment creates a numbered migration file
supabase/migrations/
├── 20250101_001_create_profiles.sql
├── 20250101_002_create_medicines.sql
├── 20250101_003_create_reminders.sql
├── 20250101_004_create_adherence.sql
├── 20250101_005_enable_rls.sql
└── ...

# Apply migrations
supabase db push
```

---

*Adhera — Design Document*  
*For implementation questions, see the Tech Stack document and README.*
