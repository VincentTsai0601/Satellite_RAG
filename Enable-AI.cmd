@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Please run Setup.cmd first.
  pause
  exit /b 1
)
echo This command sends extracted PDF passages to OpenAI to create embeddings.
echo API usage is billed to the key configured in your local .env file.
".venv\Scripts\python.exe" -m satellite.ingest --embed
set "APP_EXIT=%ERRORLEVEL%"
pause
exit /b %APP_EXIT%
