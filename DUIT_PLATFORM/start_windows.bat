@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "VENV=.venv"
set "VPY=%VENV%\Scripts\python.exe"

echo ========================================
echo DUIT - Windows launcher

echo ========================================

if exist "%VPY%" goto venv_ready
echo [1/7] Creating virtual environment...
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
echo [2/7] Installing dependencies...
"%VPY%" -m pip install -r requirements.txt
if errorlevel 1 goto failed

echo [3/7] Ensuring demo media is local...
"%VPY%" tools\cache_demo_media.py
if errorlevel 1 goto failed

echo [4/7] Running Django system check...
"%VPY%" manage.py check
if errorlevel 1 goto failed

echo [5/7] Applying migrations...
"%VPY%" manage.py migrate
if errorlevel 1 goto failed

echo [6/7] Preparing demo marketplace if needed...
"%VPY%" manage.py seed_demo --if-empty
if errorlevel 1 goto failed

echo [7/7] Starting DUIT...
echo.
echo Site:     http://127.0.0.1:8000/
echo Admin:    http://127.0.0.1:8000/admin/
echo Journal:  http://127.0.0.1:8000/journal/
echo.
echo Client:   demo_client / duit12345
echo Provider: demo_provider_00_00 / duit12345
echo Admin:    admin / admin123
echo.
echo Stop the server with Ctrl+C.
echo.
"%VPY%" manage.py runserver 127.0.0.1:8000
exit /b %errorlevel%

:python_missing
echo ERROR: Python 3 was not found.
echo Install Python 3 and enable Add python.exe to PATH.
exit /b 1

:failed
echo.
echo ========================================
echo ERROR: DUIT could not start.
echo Copy the error shown above for diagnosis.
echo ========================================
exit /b 1
