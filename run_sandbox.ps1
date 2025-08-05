# Phase 5B: Docker-Based Sandbox for Web/OS Automation
# Build and run script for Windows PowerShell

Write-Host "Phase 5B: Building Jarvis Sandbox Container..." -ForegroundColor Cyan

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Docker is not running. Please start Docker Desktop and try again." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "`nStep 1: Building Docker image..." -ForegroundColor Yellow
docker build -t jarvis-sandbox sandbox/
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to build Docker image" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "`nStep 2: Stopping any existing container..." -ForegroundColor Yellow
docker stop jarvis-sb 2>$null
docker rm jarvis-sb 2>$null

Write-Host "`nStep 3: Starting sandbox container..." -ForegroundColor Yellow
$currentDir = (Get-Location).Path
docker run -d --name jarvis-sb -p 8000:8000 -v "${currentDir}:/data:ro" jarvis-sandbox
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to start container" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "`n✅ Sandbox container is running!" -ForegroundColor Green

Write-Host "`nContainer details:" -ForegroundColor Cyan
docker ps -f name=jarvis-sb --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

Write-Host "`nTesting sandbox health..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 10
    if ($response.status -eq "healthy") {
        Write-Host "✅ Sandbox is healthy and ready for web automation!" -ForegroundColor Green
        Write-Host "Driver active: $($response.driver_active)" -ForegroundColor Cyan
    } else {
        Write-Host "⚠️ Sandbox responded but status is: $($response.status)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️ Sandbox may still be starting up. Check logs with: docker logs jarvis-sb" -ForegroundColor Yellow
}

Write-Host "`nUseful commands:" -ForegroundColor Cyan
Write-Host "To stop the sandbox: docker stop jarvis-sb" -ForegroundColor White
Write-Host "To view logs: docker logs jarvis-sb" -ForegroundColor White
Write-Host "To restart: docker start jarvis-sb" -ForegroundColor White
Write-Host "To check health: Invoke-RestMethod http://localhost:8000/health" -ForegroundColor White

Read-Host "`nPress Enter to continue"
