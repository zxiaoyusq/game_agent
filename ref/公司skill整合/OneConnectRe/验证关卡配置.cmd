@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "OC_LEVELS=%~1"
if not defined OC_LEVELS set "OC_LEVELS=%~dp0config\levels.json"
set "OC_PYTHON=C:\Users\nenghong.zhao\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not exist "%OC_PYTHON%" (
  echo Python runtime not found: %OC_PYTHON%
  pause
  exit /b 1
)
"%OC_PYTHON%" -X utf8 tools\board_solver.py "%OC_LEVELS%" --mode original --summary --max-nodes 10000 --fail-on invalid
if errorlevel 1 (
  echo Analysis failed. No game files were changed.
  pause
  exit /b 1
) else (
  echo Analysis complete. unknown is not proof of an unsolvable board.
  echo Results are advisory; verify in the game.
)
pause

