@echo off
setlocal enabledelayedexpansion
set PATH=%USERPROFILE%\.bun\bin;%PATH%
set LOG=C:\brain\gbrain-worker.log
set GBRAIN_ALLOW_SHELL_JOBS=1
set GBRAIN_POOL_SIZE=2

for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v DATABASE_URL 2^>nul') do set DATABASE_URL=%%b
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v VOYAGE_API_KEY 2^>nul') do set VOYAGE_API_KEY=%%b
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v GROQ_API_KEY 2^>nul') do set GROQ_API_KEY=%%b
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v NVIDIA_API_KEY 2^>nul') do set NVIDIA_API_KEY=%%b

:restart
echo [%date% %time%] gbrain worker starting >> "%LOG%"
gbrain.cmd jobs work --concurrency 2 >> "%LOG%" 2>&1
echo [%date% %time%] gbrain worker exited (code %errorlevel%) – restarting in 5s >> "%LOG%"
timeout /t 5 /nobreak >nul
goto restart
