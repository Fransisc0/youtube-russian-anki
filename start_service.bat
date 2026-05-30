@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo The local Python environment is missing.
  echo Double-click install.bat first.
  pause
  exit /b 1
)

if not exist ".env" (
  echo The .env file is missing.
  echo Double-click install.bat first.
  pause
  exit /b 1
)

echo Starting YouTube-to-Anki service...
echo This window keeps the local service alive for the Chrome extension.
echo You can minimize it. Close it only if you want to stop the service.
echo.

:service_loop
".venv\Scripts\python.exe" -m yt_anki.service
echo.
echo The service stopped. Restarting in 5 seconds...
echo Press Ctrl+C or close this window to stop it.
timeout /t 5 /nobreak >nul
goto service_loop
