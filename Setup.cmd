@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Setup.ps1"
set "APP_EXIT=%ERRORLEVEL%"
pause
exit /b %APP_EXIT%
