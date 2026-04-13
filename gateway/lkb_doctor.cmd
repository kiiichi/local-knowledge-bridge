@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0lkb_doctor.ps1" %*
exit /b %ERRORLEVEL%
