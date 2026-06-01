@echo off
cd /d "%~dp0.."
powershell -ExecutionPolicy Bypass -File "scripts\flash_t41.ps1"
pause
