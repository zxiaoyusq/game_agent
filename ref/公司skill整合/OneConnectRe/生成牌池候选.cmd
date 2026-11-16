@echo off
if "%~1"=="" (
  echo Drag a candidate tile pool JSON file onto this script.
  pause
  exit /b 1
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\build_pool_candidate.ps1" -PoolFile "%~1"
if errorlevel 1 echo Candidate build failed.
pause
