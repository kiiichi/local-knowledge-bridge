@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0lkb_index.ps1" %*
exit /b %ERRORLEVEL%
