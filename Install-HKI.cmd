@echo off
setlocal
powershell -ExecutionPolicy Bypass -File "%~dp0Install-HKI.ps1" -StartAfterInstall
endlocal
