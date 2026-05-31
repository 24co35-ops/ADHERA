# ADHERA Local Runner
# Run this file: Right-click start.ps1 → Run with PowerShell

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = "C:\Users\ASHWITH\AppData\Local\Programs\Python\Python313\python.exe"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   ADHERA — Starting Local Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1 — Kill anything on ports 8000 and 8080
Write-Host "[1/5] Clearing ports 8000 and 8080..." -ForegroundColor Yellow
$ports = @(8000, 8080)
foreach ($port in $ports) {
    $pids = (Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue).OwningProcess
    foreach ($procId in $pids) {
        if ($procId -and $procId -ne 0) {
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        }
    }
}
Start-Sleep -Seconds 1
Write-Host "   Ports cleared." -ForegroundColor Green

# Step 2 — Check .env exists
Write-Host "[2/5] Checking .env file..." -ForegroundColor Yellow
$envFile = Join-Path $ProjectRoot ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "   ERROR: .env file not found." -ForegroundColor Red
    Write-Host "   Copy .env.example to .env and fill in your Supabase values." -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "   .env found." -ForegroundColor Green

# Step 3 — Check Python
Write-Host "[3/5] Checking Python..." -ForegroundColor Yellow
if (-not (Test-Path $Python)) {
    Write-Host "   ERROR: Python not found at $Python" -ForegroundColor Red
    Write-Host "   Install Python 3.13 or update the path in start.ps1" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "   Python found." -ForegroundColor Green

# Step 4 — Start backend
Write-Host "[4/5] Starting backend on port 8000..." -ForegroundColor Yellow
$backendArgs = "-m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
Start-Process -FilePath $Python `
    -ArgumentList $backendArgs `
    -WorkingDirectory $ProjectRoot `
    -WindowStyle Normal

# Wait for backend to be ready
Write-Host "   Waiting for backend..." -ForegroundColor Yellow
$ready = $false
for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Seconds 1
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8000/v1/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($r.StatusCode -eq 200) {
            $ready = $true
            break
        }
    } catch {}
    Write-Host "   Still waiting... ($($i+1)s)" -ForegroundColor DarkGray
}

if (-not $ready) {
    Write-Host "   WARNING: Backend did not respond in 20s. It may still be starting." -ForegroundColor Yellow
} else {
    Write-Host "   Backend ready." -ForegroundColor Green
}

# Step 5 — Start frontend
Write-Host "[5/5] Starting frontend on port 8080..." -ForegroundColor Yellow
$frontendArgs = "-m http.server 8080 --directory frontend"
Start-Process -FilePath $Python `
    -ArgumentList $frontendArgs `
    -WorkingDirectory $ProjectRoot `
    -WindowStyle Normal

Start-Sleep -Seconds 1

# Open browser
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   ADHERA is running!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "   Frontend:  http://localhost:8080" -ForegroundColor White
Write-Host "   Backend:   http://localhost:8000/v1/health" -ForegroundColor White
Write-Host ""
Write-Host "   Demo accounts:" -ForegroundColor White
Write-Host "   Patient:   patient1@demo.adhera.app / Demo@1234" -ForegroundColor Gray
Write-Host "   Provider:  provider1@demo.adhera.app / Demo@1234" -ForegroundColor Gray
Write-Host "   Admin:     admin@demo.adhera.app / Admin@1234" -ForegroundColor Gray
Write-Host ""
Write-Host "   Opening browser..." -ForegroundColor Yellow

Start-Process "http://localhost:8080"

Write-Host ""
Write-Host "   Close this window to STOP both servers." -ForegroundColor Red
Write-Host ""

# Keep window open so closing it is obvious
Read-Host "Press Enter to stop servers and exit"

# Cleanup on exit
Write-Host "Stopping servers..." -ForegroundColor Yellow
$ports = @(8000, 8080)
foreach ($port in $ports) {
    $pids = (Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue).OwningProcess
    foreach ($procId in $pids) {
        if ($procId -and $procId -ne 0) {
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        }
    }
}
Write-Host "Servers stopped. Goodbye." -ForegroundColor Green
