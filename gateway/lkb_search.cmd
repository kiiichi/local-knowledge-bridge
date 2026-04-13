@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0lkb_search.ps1" %*
exit /b %ERRORLEVEL%
