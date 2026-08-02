# Adhera — Agent Domain Context

This configuration file defines project context, standards, issue tracking, and documentation maps for AI coding agent workflows (Matt Pocock Skills framework).

---

## 1. Issue Tracker & Repository

- **Repository**: `24co35-ops/ADHERA`
- **URL**: [https://github.com/24co35-ops/ADHERA](https://github.com/24co35-ops/ADHERA)
- **Primary Branch**: `main`
- **Issue Tracker**: GitHub Issues

---

## 2. Triage & Workflow Labels

| Label | Description |
|---|---|
| `needs-triage` | Newly created issues awaiting review and specification |
| `ready-for-agent` | Fully specified issues ready for automated agent execution |
| `bug` | Software defects or regressions needing fix and test verification |
| `enhancement` | New features or UI refinements |
| `accessibility` | WCAG 2.1 AA accessibility checks and fixes |
| `documentation` | Updates to PRD, Design Docs, or README |

---

## 3. Domain Documentation Map

- **Product Requirements**: [`PRD.md`](../../PRD.md)
- **Design System & Glassmorphism**: [`DESIGN_DOC.md`](../../DESIGN_DOC.md)
- **Technical Architecture & Stack**: [`TECH_STACK.md`](../../TECH_STACK.md)
- **Setup & Running**: [`README.md`](../../README.md)
- **Contribution Guidelines**: [`CONTRIBUTING.md`](../../CONTRIBUTING.md)

---

## 4. Engineering & Code Standards

- **Backend**: Python 3.13 / FastAPI, standard response models (`SuccessResponse`, `ErrorResponse`), pytest test suite.
- **Database & Auth**: Supabase (PostgreSQL), strict Row Level Security (RLS), PostgREST schema cache reloads after DDL (`NOTIFY pgrst, 'reload schema';`).
- **Frontend**: Glassmorphism dark UI (`#111318`), Alpine.js state management, Vanilla CSS (`adhera.css`), WCAG 2.1 AA contrast compliance (`axe_scan.js`).
- **Verification Requirement**: Always run `pytest` and `node tests/axe_scan.js` before declaring completion.
