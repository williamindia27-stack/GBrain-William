@echo off
set PATH=%USERPROFILE%\.bun\bin;%PATH%
set GBRAIN_ALLOW_SHELL_JOBS=1
gbrain jobs submit shell --params "{\"argv\":[\"C:\\Windows\\System32\\cmd.exe\",\"/c\",\"C:\\brain\\check-new-papers.bat\"],\"cwd\":\"C:\\brain\"}" --follow
