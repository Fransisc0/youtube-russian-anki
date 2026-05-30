@echo off
setlocal
cd /d "%~dp0"

echo.
echo YouTube Russian-to-Anki installer
echo =================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install.ps1"
set EXIT_CODE=%ERRORLEVEL%

echo.
if "%EXIT_CODE%"=="0" (
  echo Install finished. You can now double-click start_service.bat.
) else (
  echo Install did not finish successfully. See the message above.
)
echo.
pause
exit /b %EXIT_CODE%
