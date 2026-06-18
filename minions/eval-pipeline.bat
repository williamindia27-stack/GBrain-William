@echo off
setlocal
set PATH=%USERPROFILE%\.bun\bin;%PATH%
set PYTHON=%USERPROFILE%\AppData\Local\Python\pythoncore-3.14-64\python.exe
if not exist "%PYTHON%" set PYTHON=python
set NODE_TLS_REJECT_UNAUTHORIZED=0

for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v DATABASE_URL 2^>nul')      do set DATABASE_URL=%%b
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v VOYAGE_API_KEY 2^>nul')    do set VOYAGE_API_KEY=%%b
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v ANTHROPIC_API_KEY 2^>nul') do set ANTHROPIC_API_KEY=%%b

"%PYTHON%" "C:\brain\minions\eval-pipeline.py" --save %*
