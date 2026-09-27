@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "VENV=.venv"
set "VPY=%VENV%\Scripts\python.exe"

echo ========================================
echo DUIT - Windows verification
echo ========================================

if exist "%VPY%" goto venv_ready
echo [1/9] Creating virtual environment...
py -3 -c "import sys" >nul 2>&1
if not errorlevel 1 goto create_with_py
python -c "import sys" >nul 2>&1
if not errorlevel 1 goto create_with_python
goto python_missing

:create_with_py
py -3 -m venv "%VENV%"
if errorlevel 1 goto failed
goto venv_ready

:create_with_python
python -m venv "%VENV%"
if errorlevel 1 goto failed

:venv_ready
if not exist "%VPY%" goto failed
echo [2/9] Installing dependencies...
"%VPY%" -m pip install -r requirements.txt
if errorlevel 1 goto failed

echo [3/9] Caching curated demo media locally...
"%VPY%" tools\cache_demo_media.py
if errorlevel 1 goto failed

echo [4/9] Running Django system check...
"%VPY%" manage.py check
if errorlevel 1 goto failed

echo [5/9] Checking migrations...
"%VPY%" manage.py makemigrations --check --dry-run
if errorlevel 1 goto failed

echo [6/9] Applying migrations...
"%VPY%" manage.py migrate
if errorlevel 1 goto failed

echo [7/9] Preparing demo marketplace if needed...
"%VPY%" manage.py seed_demo --if-empty
if errorlevel 1 goto failed

echo [8/9] Auditing LOCAL demo photos and profiles...
"%VPY%" manage.py audit_demo_media
if errorlevel 1 goto failed

echo [9/9] Running tests...
"%VPY%" manage.py test
if errorlevel 1 goto failed

echo.
echo ========================================
echo DUIT verification PASSED.
echo Demo photos are cached locally.
echo ========================================
exit /b 0

:python_missing
echo ERROR: Python 3 was not found.
exit /b 1

:failed
echo.
echo ========================================
echo ERROR: DUIT verification failed.
echo Copy the error shown above for diagnosis.
echo ========================================
exit /b 1
