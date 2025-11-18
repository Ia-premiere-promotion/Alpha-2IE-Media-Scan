@echo off
title Monitoring Temps Reel - Tous les Medias
color 0A

echo ================================================================================
echo.
echo           MONITORING EN TEMPS REEL - TOUS LES MEDIAS
echo.
echo ================================================================================
echo.
echo  Ce script lance le monitoring simultane de tous les medias :
echo.
echo    - Burkina24
echo    - Lefaso.net
echo    - Fasopresse
echo    - ESidwaya
echo    - Observateur Paalga
echo.
echo ================================================================================
echo.
echo  Demarrage en cours...
echo.

REM Lancer le script Python principal
python master_realtime_monitor.py

echo.
echo ================================================================================
echo  Monitoring termine
echo ================================================================================
echo.
pause
