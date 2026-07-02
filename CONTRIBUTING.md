# Contributing to Adhera

## Local Development Setup

### 1. Repository & Virtual Environment
```bash
git clone https://github.com/24co35-ops/ADHERA.git
cd ADHERA
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Configuration
Copy `.env.example` to `.env` and populate:
```bash
cp .env.example .env
```

### 3. Database & Migrations
Install [Supabase CLI](https://supabase.com/docs/guides/cli):
```bash
npm install -g supabase
supabase link --project-ref your-project-ref
supabase db push
```

### 4. Seed Demo Data
```bash
python scripts/seed_demo.py
```

### 5. Running App locally
* **Backend:** `uvicorn app.main:app --reload --port 8000`
* **Frontend:** `python -m http.server 8080 --directory frontend`

---

## Running Tests & Quality Checks

### 1. Pytest (Unit & Integration Tests)
```bash
# Run all tests
pytest
# Run with coverage report (required: >= 50% coverage)
pytest --cov=app --cov-report=term-missing --cov-fail-under=50
```

### 2. Linting (Ruff)
```bash
ruff check app/
```

### 3. Type Checking (Mypy)
```bash
mypy app/ --ignore-missing-imports --no-strict-optional --follow-imports=skip
```

### 4. Accessibility Check
Run axe-core scan on altered HTML:
```bash
npm install -g @axe-core/cli
axe frontend/dashboard.html frontend/medicines.html --exit
```

---

## PR & Commit Conventions

### Commit Messages
Use [Conventional Commits](https://www.conventionalcommits.org/):
* `feat:` new features
* `fix:` bug fixes
* `chore:` build, config, dependencies
* `ci:` integration changes

### PR Checklist
1. All linting (`ruff`) and type checks (`mypy`) pass cleanly.
2. Pytest suite passes; backend coverage does not drop below 50%.
3. UI changes verified with `axe-core` accessibility checks.
4. `.env` secrets or `SUPABASE_SERVICE_ROLE_KEY` are never committed.
