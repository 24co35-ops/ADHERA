# Adhera - Project Instructions

## Architecture & Tech Stack
- **Backend:** FastAPI (Python 3.10+), Pydantic v2, Uvicorn.
- **Frontend:** Vanilla JS, Alpine.js 3.x, Tailwind CSS (CDN).
- **Database:** Supabase (PostgreSQL 15+), RLS, pg_cron.
- **Notifications:** Supabase Edge Functions (Deno), Resend (Email).

## Key Conventions
- **Design System:** Glassmorphism (Futuristic Minimalist). Dark mode by default. Vibrant cyan accents.
- **API Versioning:** All API endpoints should be prefixed with `/v1`.
- **Database:** Use UUIDs for all primary keys. Use RLS for all tables.
- **Authentication:** Delegate all auth to Supabase Auth. Use FastAPI dependency injection for user verification.
- **Testing:** Use `pytest` for backend tests.

## Development Workflow
- Follow the Incremental Process Model as defined in the PRD.
- Ensure WCAG 2.1 Level AA conformance for all UI components.
- All code changes must be verified with tests.
