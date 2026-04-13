@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0lkb_bootstrap_runtime.ps1" %*
exit /b %ERRORLEVEL%
