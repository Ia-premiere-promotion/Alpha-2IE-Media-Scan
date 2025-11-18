@echo off
echo ========================================
echo   MONITORING ESIDWAYA - DEMARRAGE
echo ========================================
echo.
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
python esidwaya_realtime_monitor.py
pause
