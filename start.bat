@echo off
setlocal
cd /d "%~dp0"
title Notification System launcher

set PY=
py -3 --version >nul 2>&1 && set PY=py -3
if not defined PY python --version >nul 2>&1 && set PY=python
if not defined PY goto nopython
call npm --version >nul 2>&1
if errorlevel 1 goto nonode

echo === Backend setup ===
cd /d "%~dp0backend"
if not exist .venv\Scripts\activate.bat %PY% -m venv .venv
if errorlevel 1 goto fail
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if errorlevel 1 goto fail
if not exist .env copy .env.example .env >nul
python manage.py migrate
if errorlevel 1 goto fail
python manage.py seed_defaults
if errorlevel 1 goto fail

echo === Frontend setup ===
cd /d "%~dp0frontend"
if not exist .env copy .env.example .env >nul
if not exist node_modules call npm install
if errorlevel 1 goto fail

echo === Starting servers ===
start "Backend - Django :8000" cmd /k "cd /d %~dp0backend && call .venv\Scripts\activate.bat && python manage.py runserver"
start "Frontend - Vite :5173" cmd /k "cd /d %~dp0frontend && npm run dev"
timeout /t 10 /nobreak >nul
start "" http://localhost:5173
echo.
echo App running at http://localhost:5173   (login: admin / admin12345)
echo Close the two server windows to stop it.
pause
exit /b 0

:nopython
echo Python 3.10+ was not found. Install it from https://www.python.org/downloads/ and tick "Add python.exe to PATH".
pause
exit /b 1

:nonode
echo Node.js was not found. Install the LTS version from https://nodejs.org/
pause
exit /b 1

:fail
echo.
echo Something failed - see the error above. Copy it and send it to Claude.
pause
exit /b 1
