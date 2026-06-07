@echo off
setlocal

set "WORKBENCH=%~dp0tools\workbench"

start "IRIS Workbench Server" cmd /k "cd /d "%WORKBENCH%" && python proxy_server.py"

timeout /t 1 /nobreak >nul

start "" "http://localhost:8080"

echo IRIS Workbench running at http://localhost:8080
echo Close the server window to stop.
