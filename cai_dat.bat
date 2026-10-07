@echo off
setlocal
cd /d "%~dp0"
call uv run --locked python tools_tai_video.py
exit /b %errorlevel%
