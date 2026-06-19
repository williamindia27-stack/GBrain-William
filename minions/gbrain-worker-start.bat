@echo off
setlocal enabledelayedexpansion
set PATH=%USERPROFILE%\.bun\bin;%PATH%
set LOG=C:\brain\gbrain-worker.log
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v DATABASE_URL 2^>nul') do set DATABASE_URL=%%b
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v NVIDIA_API_KEY 2^>nul') do set NVIDIA_API_KEY=%%b
set GBRAIN_POOL_SIZE=2
set GBRAIN_ALLOW_SHELL_JOBS=1

echo [%date% %time%] gbrain worker starting >> "%LOG%"
"%USERPROFILE%\.bun\bin\gbrain.cmd" jobs work >> "%LOG%" 2>&1
echo [%date% %time%] gbrain worker stopped (exit %errorlevel%) >> "%LOG%"
endlocal
