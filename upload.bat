@echo off
REM Social Media Video Uploader - Quick Launch
REM Usage: upload.bat "C:\path\to\video.mp4" [options]

cd /d "%~dp0"
call venv\Scripts\activate.bat
python upload.py %*
