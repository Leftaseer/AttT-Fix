@echo off
rem Generic bisection: toggle_bisect.bat [-Scenario mybug.txt] [-Exe ATThrone_debug.exe]
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0toggle_bisect.ps1" %*
pause
