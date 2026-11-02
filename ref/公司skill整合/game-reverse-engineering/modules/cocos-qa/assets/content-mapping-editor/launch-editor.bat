@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
if not exist editor.config.json (
  echo 找不到 editor.config.json。
  echo 请先复制 editor.config.example.json，并按当前项目修改三个文件路径。
  pause
  exit /b 1
)
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 server.py --open
) else (
  python server.py --open
)
if errorlevel 1 pause
