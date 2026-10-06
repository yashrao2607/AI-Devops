# ==============================================================================
# DeploySafe 1-Click Native Local Launch Script (PowerShell)
# ==============================================================================

Write-Host "`n🚀 [DeploySafe] Starting Local Native Services..." -ForegroundColor Cyan

# 1. Kill any stale processes on port 8000 and 5173
Write-Host "🧹 Checking and freeing ports 8000 and 5173..." -ForegroundColor Gray
$p8000 = (Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue).OwningProcess | Select-Object -Unique
if ($p8000) { Stop-Process -Id $p8000 -Force -ErrorAction SilentlyContinue }

$p5173 = (Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue).OwningProcess | Select-Object -Unique
if ($p5173) { Stop-Process -Id $p5173 -Force -ErrorAction SilentlyContinue }

# 2. Start Backend
Write-Host "🐍 Launching Backend API (FastAPI + Multi-Agent Engine)..." -ForegroundColor Cyan
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000"

# 3. Wait for backend health
Write-Host "⏳ Waiting for Backend to report healthy..." -ForegroundColor Gray
$healthy = $false
for ($i = 0; $i -lt 15; $i++) {
    try {
        $res = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/health" -TimeoutSec 2
        if ($res.status -eq "healthy") {
            $healthy = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 1
    }
}

if ($healthy) {
    Write-Host "✅ Backend is healthy on http://127.0.0.1:8000!" -ForegroundColor Green
} else {
    Write-Host "⚠️ Backend is still initializing..." -ForegroundColor Yellow
}

# 4. Start Frontend
Write-Host "⚛️ Launching Frontend UI (Vite React SPA)..." -ForegroundColor Cyan
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host "`n========================================================" -ForegroundColor Green
Write-Host "🎉 DeploySafe is running locally!" -ForegroundColor Green
Write-Host "   Frontend UI:  http://localhost:5173" -ForegroundColor White
Write-Host "   Backend API:  http://127.0.0.1:8000" -ForegroundColor White
Write-Host "   Interactive:  http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "========================================================`n" -ForegroundColor Green
