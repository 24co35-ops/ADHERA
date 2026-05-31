# Local Development Guide - Adhera

## Prerequisites
- **Python**: 3.10+ (tested on Python 3.13)
- **Supabase**: Account and database instance
- **Git**: For source control

## First-Time Setup
1. Clone repository:
   ```bash
   git clone <repository_url>
   cd stitch_adhera_glassmorphism_design_system
   ```
2. Create and activate virtual environment:
   - **Windows**:
     ```powershell
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```
   - **Mac/Linux**:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
5. Configure environment variables in `.env`:
   - `SUPABASE_URL`: Supabase Project URL (Settings > API)
   - `SUPABASE_ANON_KEY`: Supabase API Client Anonymous Key (Settings > API)
   - `SUPABASE_SERVICE_ROLE_KEY`: Supabase Service Role Key (Settings > API)
   - `SUPABASE_JWT_SECRET`: Supabase JWT Secret (Settings > API)
   - `RESEND_API_KEY`: API Key from Resend for emails
   - `CORS_ORIGIN`: Set to `http://localhost:8080` (or frontend origin)
   - `ENVIRONMENT`: Set to `development`

## Supabase Setup
1. Collect keys from your Supabase Dashboard under **Project Settings > API**.
2. Run database migrations by running the SQL files under `supabase/migrations/` in the Supabase SQL Editor.
3. Enable Realtime on the `adherence` table:
   - Go to **Database > Replication** in Supabase Dashboard.
   - Enable replication for source tables and select the `adherence` table.

## Seed Demo Data
Run the seeding script to populate users and mock data:
```bash
python scripts/seed_demo.py
```
Seeded demo credentials:
- **Patient**: `patient1@demo.adhera.app` / `Demo@1234`
- **Provider**: `provider1@demo.adhera.app` / `Demo@1234`
- **Admin**: `admin@demo.adhera.app` / `Admin@1234`

## Run the Project
Start the backend and frontend servers in separate terminals.

### Terminal 1: Backend Server
- **Windows**:
  ```powershell
  C:\Users\ASHWITH\AppData\Local\Programs\Python\Python313\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
  ```
- **Mac/Linux**:
  ```bash
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
  ```

### Terminal 2: Frontend Server
- **Windows**:
  ```powershell
  C:\Users\ASHWITH\AppData\Local\Programs\Python\Python313\python.exe -m http.server 8080 --directory frontend
  ```
- **Mac/Linux**:
  ```bash
  python3 -m http.server 8080 --directory frontend
  ```

Access the app via: `http://localhost:8080`

## Verify Running Status
- **Backend Health**: Visit `http://localhost:8000/v1/health`. Should return `{"success":true,"data":{"status":"ok"}}`.
- **Frontend Page**: Visit `http://localhost:8080/index.html`. Should render the login page.

## Testing Flows
- **Patient**: Login with `patient1@demo.adhera.app` -> Redirects to `dashboard.html`.
- **Provider**: Login with `provider1@demo.adhera.app` -> Redirects to `provider-dashboard.html`.
- **Admin**: Login with `admin@demo.adhera.app` -> Redirects to `admin-dashboard.html`.

## Run Tests
- **Unit/Integration Tests**:
  ```bash
  pytest tests/ -v --tb=short
  ```
- **E2E Browser Tests**:
  ```bash
  python run_e2e.py
  ```

## Common Issues & Fixes
- **Port 8000 already in use**:
  - *Windows*: `Get-Process -Name python | Stop-Process -Force`
  - *Mac/Linux*: `kill $(lsof -t -i:8000)`
- **CORS error**: Verify `CORS_ORIGIN=http://localhost:8080` matches the frontend server URL in `.env`.
- **Invalid login credentials**: Re-run the seed script: `python scripts/seed_demo.py`.
- **Chart.js crash/rendering issues**: Perform a hard refresh in the browser (`Ctrl + Shift + R`).
- **Admin panel shows no users**: Restart backend uvicorn server to re-verify authentication client context.

## Project Structure
- `app/`: FastAPI backend applications, routers, and configurations.
- `frontend/`: UI files (HTML, CSS, JS assets).
- `supabase/`: Database schemas, edge functions, and policies.
- `tests/`: End-to-end and pytest suite.
- `scripts/`: Utilities and mock data generation.
- `run_e2e.py`: Playwright integration tests runner.
