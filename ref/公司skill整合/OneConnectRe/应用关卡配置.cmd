@echo off
cd /d "%~dp0"
"C:\Users\nenghong.zhao\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" tools\compile_levels.py
set "OC_COMPILE_STATUS=%ERRORLEVEL%"
if not "%OC_COMPILE_STATUS%"=="0" (echo Build failed. Check the error and verify the previous files; rollback may fail if storage is unavailable.) else (echo Build complete.)
if /I not "%~1"=="--no-pause" pause
exit /b %OC_COMPILE_STATUS%

