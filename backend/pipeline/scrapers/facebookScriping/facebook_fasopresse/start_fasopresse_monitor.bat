@echo off
echo ========================================
echo DEMARRAGE DU MONITORING FASOPRESSE
echo ========================================
echo.

REM Activer l'environnement virtuel si présent
if exist venv\Scripts\activate.bat (
    echo Activation de l'environnement virtuel...
    call venv\Scripts\activate.bat
)

REM Lancer le script Python
echo Lancement du monitoring...
python fasopresse_realtime_monitor.py

pause
