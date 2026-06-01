@echo off
cd /d "%~dp0.."
powershell -ExecutionPolicy Bypass -File "scripts\flash_t40.ps1"
pause
