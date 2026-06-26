@echo off
setlocal enabledelayedexpansion
set PATH=%USERPROFILE%\.bun\bin;%PATH%

for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v DATABASE_URL 2^>nul') do set DATABASE_URL=%%b
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v NVIDIA_API_KEY 2^>nul') do set NVIDIA_API_KEY=%%b
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v VOYAGE_API_KEY 2^>nul') do set VOYAGE_API_KEY=%%b
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v GROQ_API_KEY 2^>nul') do set GROQ_API_KEY=%%b

gbrain jobs work
