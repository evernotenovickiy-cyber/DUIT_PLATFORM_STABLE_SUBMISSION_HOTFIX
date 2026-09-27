@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "VENV=.venv"
set "VPY=%VENV%\Scripts\python.exe"

echo ========================================
echo DUIT - prepare submission package
echo ========================================

if exist "%VPY%" goto python_ready
py -3 -c "import sys" >nul 2>&1
if not errorlevel 1 goto create_py
python -c "import sys" >nul 2>&1
if not errorlevel 1 goto create_python
echo ERROR: Python 3 was not found.
exit /b 1

:create_py
py -3 -m venv "%VENV%"
if errorlevel 1 exit /b 1
goto python_ready

:create_python
python -m venv "%VENV%"
if errorlevel 1 exit /b 1

:python_ready
echo [1/8] Installing dependencies...
"%VPY%" -m pip install -r requirements.txt
if errorlevel 1 goto failed

echo [2/8] Downloading curated demo media...
"%VPY%" tools\cache_demo_media.py
if errorlevel 1 goto failed

echo [3/8] Running Django system check...
"%VPY%" manage.py check
if errorlevel 1 goto failed

echo [4/8] Checking migrations...
"%VPY%" manage.py makemigrations --check --dry-run
if errorlevel 1 goto failed

echo [5/8] Applying migrations and preparing demo data...
"%VPY%" manage.py migrate
if errorlevel 1 goto failed
"%VPY%" manage.py seed_demo --if-empty
if errorlevel 1 goto failed

echo [6/8] Auditing demo photos and profiles...
"%VPY%" manage.py audit_demo_media
if errorlevel 1 goto failed

echo [7/8] Running full test suite...
"%VPY%" manage.py test
if errorlevel 1 goto failed

echo [8/8] Building teacher-ready ZIP...
"%VPY%" tools\build_submission_zip.py
if errorlevel 1 goto failed

echo.
echo ========================================
echo SUBMISSION package is READY.
echo Look one folder above for:
echo DUIT_PLATFORM_OFFLINE_SUBMISSION.zip
echo ========================================
exit /b 0

:failed
echo.
echo ========================================
echo ERROR: submission preparation failed.
echo Fix the error above before sending the project.
echo ========================================
exit /b 1
