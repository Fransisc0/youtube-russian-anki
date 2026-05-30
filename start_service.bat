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
  echo Double-click install.bat first, then add your DeepL key.
  pause
  exit /b 1
)

echo Starting YouTube-to-Anki service...
echo Leave this window open while using the Chrome extension.
echo.
".venv\Scripts\python.exe" -m yt_anki.service
pause
