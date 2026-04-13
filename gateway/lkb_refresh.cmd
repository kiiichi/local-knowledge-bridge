@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0lkb_refresh.ps1" %*
exit /b %ERRORLEVEL%
