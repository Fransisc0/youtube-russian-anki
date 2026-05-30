@echo off
setlocal
cd /d "%~dp0"

echo.
echo YouTube Russian-to-Anki
echo ======================
echo.
echo This will install/update the app, copy the Chrome extension folder
echo path to your clipboard, open Chrome's extension page, and start
echo the local service.
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_here.ps1"
set EXIT_CODE=%ERRORLEVEL%

echo.
if not "%EXIT_CODE%"=="0" (
  echo START_HERE did not finish successfully. See the message above.
  echo.
  pause
  exit /b %EXIT_CODE%
)

if not exist ".venv\Scripts\python.exe" (
  echo The local Python environment is missing. Run install.bat and try again.
  echo.
  pause
  exit /b 1
)

echo.
echo Starting the local service now.
echo Keep this window open while using the Chrome extension.
echo.
".venv\Scripts\python.exe" -m yt_anki.service
pause
