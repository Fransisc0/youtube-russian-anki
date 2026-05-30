@echo off
setlocal
cd /d "%~dp0"

echo.
echo Updating YouTube-to-Anki
echo ========================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\update_and_restart.ps1"
set EXIT_CODE=%ERRORLEVEL%

echo.
if "%EXIT_CODE%"=="0" (
  echo Update finished.
  echo If Chrome was already open, click the extension icon and choose Reload Extension.
) else (
  echo Update did not finish successfully. See the message above.
)
echo.
pause
exit /b %EXIT_CODE%
