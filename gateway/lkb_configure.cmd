@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0lkb_configure.ps1" %*
exit /b %ERRORLEVEL%
