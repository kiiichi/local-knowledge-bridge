@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0lkb_ask.ps1" %*
exit /b %ERRORLEVEL%
