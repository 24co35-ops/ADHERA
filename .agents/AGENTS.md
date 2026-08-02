# Workspace Rules & Skills — Adhera Project

## Core Workflow Rules
1. **Repository**: [24co35-ops/ADHERA](https://github.com/24co35-ops/ADHERA)
2. **Issue Tracker**: GitHub Issues with labels `needs-triage` and `ready-for-agent`.
3. **Domain Documentation**:
   - [`PRD.md`](file:///c:/Users/ASHWITH/Desktop/Adhera/PRD.md)
   - [`DESIGN_DOC.md`](file:///c:/Users/ASHWITH/Desktop/Adhera/DESIGN_DOC.md)
   - [`TECH_STACK.md`](file:///c:/Users/ASHWITH/Desktop/Adhera/TECH_STACK.md)
   - [`CONTEXT.md`](file:///c:/Users/ASHWITH/Desktop/Adhera/docs/agents/CONTEXT.md)

## Coding Standards
- **Backend (Python / FastAPI)**:
  - Enforce standard response models (`SuccessResponse`, `ErrorResponse`).
  - Use `datetime.now(timezone.utc)` for all UTC timestamp handling.
  - Test with `pytest`.
- **Database (Supabase / PostgreSQL)**:
  - Keep Row Level Security (RLS) enabled on all tables.
  - After executing any DDL schema change, always invoke `NOTIFY pgrst, 'reload schema';`.
- **Frontend (Vanilla CSS + Alpine.js)**:
  - Maintain dark theme (`#111318`) with glassmorphism cards and cyan (`#00dbe7`) accents.
  - Enforce WCAG 2.1 AA color contrast (minimum 4.5:1 ratio).
  - Verify accessibility using `node tests/axe_scan.js`.
