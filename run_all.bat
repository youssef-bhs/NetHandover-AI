@echo off
setlocal

set ROOT=%~dp0
set MAIN_PY=%ROOT%.venv\Scripts\python.exe

if /i "%1"=="clean" (
  for %%P in (8001 3000) do (
    for /f "tokens=5" %%A in ('netstat -ano ^| findstr :%%P ^| findstr LISTENING') do taskkill /F /PID %%A >nul 2>&1
  )
)

if not exist "%MAIN_PY%" (
  echo Missing %MAIN_PY%. Create the main venv first.
  exit /b 1
)

start "backend" "%MAIN_PY%" "%ROOT%run_backend.py"
start "frontend" cmd /c "cd /d %ROOT%frontend && npm run dev"

echo Started backend (8001), frontend (3000).
endlocal
