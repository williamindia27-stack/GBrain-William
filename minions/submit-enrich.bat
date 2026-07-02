@echo off
set PATH=%USERPROFILE%\.bun\bin;%PATH%
set GBRAIN_ALLOW_SHELL_JOBS=1
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v DATABASE_URL 2^>nul') do set DATABASE_URL=%%b
gbrain.cmd jobs submit shell --params "{\"argv\":[\"C:\\Windows\\System32\\cmd.exe\",\"/c\",\"C:\\brain\\minions\\enrich-researchers.bat\"],\"cwd\":\"C:\\brain\"}" --follow
