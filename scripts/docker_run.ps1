# ==============================================================================
# DeploySafe 1-Click Docker Launch Script (PowerShell)
# ==============================================================================

Write-Host "`n🚀 [DeploySafe] Checking Docker Engine..." -ForegroundColor Cyan

# Check if Docker Desktop service is running
$dockerStatus = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Docker daemon is not running. Attempting to start Docker Desktop..." -ForegroundColor Yellow
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe" -ErrorAction SilentlyContinue
    Write-Host "⏳ Waiting 25 seconds for Docker Desktop to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 25
}

# Verify Docker availability
docker info > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker Engine is not ready yet. Please open Docker Desktop from your Start menu and rerun this script." -ForegroundColor Red
    Exit 1
}

Write-Host "✅ Docker Engine is online!" -ForegroundColor Green

# Build and start containers
Write-Host "🔨 Building and launching DeploySafe containers via Docker Compose..." -ForegroundColor Cyan
docker compose -f docker-compose.yml up --build -d

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n========================================================" -ForegroundColor Green
    Write-Host "🎉 DeploySafe is running in Docker!" -ForegroundColor Green
    Write-Host "   Frontend UI:  http://localhost:5173 (or http://localhost:3000)" -ForegroundColor White
    Write-Host "   Backend API:  http://localhost:8000" -ForegroundColor White
    Write-Host "   API Docs:     http://localhost:8000/docs" -ForegroundColor White
    Write-Host "   Health Check: http://localhost:8000/api/v1/health" -ForegroundColor White
    Write-Host "========================================================`n" -ForegroundColor Green
    Write-Host "Tip: To view live container logs, run: docker compose logs -f" -ForegroundColor Gray
    Write-Host "Tip: To stop containers, run: docker compose down" -ForegroundColor Gray
} else {
    Write-Host "❌ Failed to start containers. Check docker logs above." -ForegroundColor Red
}
