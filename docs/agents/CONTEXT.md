# Adhera — Agent Domain Context

This configuration file defines project context, standards, issue tracking, design system vocabulary, and documentation maps for AI coding agent workflows (Matt Pocock Skills framework).

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

## 3. ADHERA Design & Motion Vocabulary

### 3.1 Component Taxonomy
- **Care Team Card**: Assigned provider/care-team widget featuring 40px initials avatar, role badge, and contact action.
- **Stat Widget**: Metric display container (`p-5`, 20px padding) showing key performance indicators (adherence %, streak, missed count).
- **Risk Badge**: High-contrast solid-fill pill indicating risk tier (`Critical`, `High`, `Moderate`, `Low`) meeting WCAG AA 4.5:1 ratio.
- **Patient Card**: Provider dashboard patient overview card featuring circular 44px avatar, risk badge, adherence gauge, and quick actions.
- **Alert Banner**: High-priority feedback banner for Severity 3–4 alerts with distinct backdrop glow and emergency indicator.

### 3.2 Material System Terms
- **Glass Surface**: Translucent backdrop container (`background: rgba(255,255,255,0.05); backdrop-filter: blur(24px);`).
- **Specular Border**: Subtle top specular edge highlight (`border-t: 1px solid rgba(255,255,255,0.15);`).
- **Ambient Glow**: Soft colored depth shadow (`box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5), 0 0 20px rgba(0,219,231,0.08);`).
- **Depth Elevation**: Multi-layered shadow hierarchy (`card-primary`, `card-secondary`, `card-tertiary`).

### 3.3 Motion & Transition System
- **enter-spring**: Entrance transition using decelerated curve (`cubic-bezier(0.16, 1, 0.3, 1)`, 200–300ms) for modals and popovers.
- **exit-ease**: Exit transition using accelerated curve (`cubic-bezier(0.7, 0, 0.84, 0)`, 150–200ms) for closing elements.
- **press-feedback**: Interactive button press down transform (`active:scale-[0.98] transition-transform duration-100`).
- **stagger-reveal**: Sequential list item entrance animation with cascading delays (`delay-75`, `delay-150`).

---

## 4. Domain Documentation Map

- **Product Requirements**: [`PRD.md`](../../PRD.md)
- **Design System & Glassmorphism**: [`DESIGN_DOC.md`](../../DESIGN_DOC.md)
- **Technical Architecture & Stack**: [`TECH_STACK.md`](../../TECH_STACK.md)
- **Setup & Running**: [`README.md`](../../README.md)
- **Contribution Guidelines**: [`CONTRIBUTING.md`](../../CONTRIBUTING.md)

---

## 5. Engineering & Code Standards

- **Backend**: Python 3.13 / FastAPI, standard response models (`SuccessResponse`, `ErrorResponse`), pytest test suite.
- **Database & Auth**: Supabase (PostgreSQL), strict Row Level Security (RLS), PostgREST schema cache reloads after DDL (`NOTIFY pgrst, 'reload schema';`).
- **Frontend**: Glassmorphism dark UI (`#111318`), Alpine.js state management, Vanilla CSS (`adhera.css`), WCAG 2.1 AA contrast compliance (`axe_scan.js`).
- **Verification Requirement**: Always run `pytest` and `node tests/axe_scan.js` before declaring completion.
