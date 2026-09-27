@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ========================================
echo DUIT - Docker launcher
echo ========================================
docker info >nul 2>&1
if errorlevel 1 (
  echo ERROR: Docker Desktop is not running.
  exit /b 1
)
docker compose up --build -d
if errorlevel 1 exit /b 1
echo.
echo Site:  http://127.0.0.1:8000/
echo Admin: http://127.0.0.1:8000/admin/
echo Client: demo_client / duit12345
echo Provider: demo_provider_00_00 / duit12345
echo Admin: admin / admin123
docker compose ps
