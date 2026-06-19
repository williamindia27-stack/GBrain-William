@echo off
set PATH=%USERPROFILE%\.bun\bin;%PATH%
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v DATABASE_URL 2^>nul') do set DATABASE_URL=%%b
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v NVIDIA_API_KEY 2^>nul') do set NVIDIA_API_KEY=%%b
set GBRAIN_POOL_SIZE=2
set GBRAIN_ALLOW_SHELL_JOBS=1
echo [%date% %time%] Worker starting >> "C:\brain\minions\worker-test.log"
gbrain.cmd jobs work >> "C:\brain\minions\worker-test.log" 2>&1
echo [%date% %time%] Worker exited with code %errorlevel% >> "C:\brain\minions\worker-test.log"
