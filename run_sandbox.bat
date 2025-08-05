@echo off
REM Phase 5B: Docker-Based Sandbox for Web/OS Automation
REM Build and run script for Windows

echo Phase 5B: Building Jarvis Sandbox Container...

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running. Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo Step 1: Building Docker image...
docker build -t jarvis-sandbox sandbox/
if %errorlevel% neq 0 (
    echo ERROR: Failed to build Docker image
    pause
    exit /b 1
)

echo Step 2: Stopping any existing container...
docker stop jarvis-sb >nul 2>&1
docker rm jarvis-sb >nul 2>&1

echo Step 3: Starting sandbox container...
docker run -d --name jarvis-sb -p 8000:8000 -v "%cd%:/data:ro" jarvis-sandbox
if %errorlevel% neq 0 (
    echo ERROR: Failed to start container
    pause
    exit /b 1
)

echo.
echo ✅ Sandbox container is running!
echo.
echo Container details:
docker ps -f name=jarvis-sb --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo.
echo Testing sandbox health...
timeout /t 5 /nobreak >nul 2>&1
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Sandbox is healthy and ready for web automation!
) else (
    echo ⚠️ Sandbox may still be starting up. Check logs with: docker logs jarvis-sb
)

echo.
echo To stop the sandbox: docker stop jarvis-sb
echo To view logs: docker logs jarvis-sb
echo To restart: docker start jarvis-sb
echo.
pause
