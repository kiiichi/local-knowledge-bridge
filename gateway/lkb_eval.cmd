@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0lkb_eval.ps1" %*
exit /b %ERRORLEVEL%
