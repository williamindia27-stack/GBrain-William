@echo off
setlocal enabledelayedexpansion
set PATH=%USERPROFILE%\.bun\bin;%PATH%
set PYTHON=C:\Users\wprozenko\AppData\Local\Python\pythoncore-3.14-64\python.exe

for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v DATABASE_URL 2^>nul') do set DATABASE_URL=%%b
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v VOYAGE_API_KEY 2^>nul') do set VOYAGE_API_KEY=%%b
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v GROQ_API_KEY 2^>nul') do set GROQ_API_KEY=%%b
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v NVIDIA_API_KEY 2^>nul') do set NVIDIA_API_KEY=%%b
set GBRAIN_ALLOW_SHELL_JOBS=1
set GBRAIN_POOL_SIZE=2

echo [%date% %time%] Starting gbrain worker...
start "gbrain-worker" /min cmd /c "C:\brain\minions\gbrain-worker.bat"

echo [%date% %time%] Starting paper watcher...
start "paper-watcher" /min "%PYTHON%" "C:\brain\paper-watcher.py"

echo.
echo GBrain daemon started.
echo   - Job worker:    gbrain jobs work (handles import, embed, extract)
echo   - Paper watcher: watching C:\brain\papers every 10 seconds
echo.
echo Drop a PDF into C:\brain\papers and it will be in the brain within ~30 seconds.
echo Close this window to stop all daemons, or close the individual windows.
