@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\lkb_setup.ps1"
set "LKB_EXIT=%ERRORLEVEL%"
if not "%LKB_EXIT%"=="0" (
  echo.
  echo Local Knowledge Bridge setup failed with exit code %LKB_EXIT%.
  pause
)
exit /b %LKB_EXIT%
