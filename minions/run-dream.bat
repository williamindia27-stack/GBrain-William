@echo off
set PATH=%USERPROFILE%\.bun\bin;%PATH%
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v DATABASE_URL 2^>nul') do set DATABASE_URL=%%b
set GBRAIN_POOL_SIZE=2
gbrain.cmd dream
