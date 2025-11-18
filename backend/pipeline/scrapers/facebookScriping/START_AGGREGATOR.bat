@echo off
title Agregation Automatique - Tous les Medias
color 0E

echo ================================================================================
echo.
echo           AGREGATION AUTOMATIQUE - TOUS LES MEDIAS
echo.
echo ================================================================================
echo.
echo  Ce script consolide automatiquement tous les fichiers JSON des medias
echo  dans un seul fichier : all_media_consolidated.json
echo.
echo  Le fichier se met a jour automatiquement toutes les 60 secondes
echo.
echo ================================================================================
echo.
echo  Demarrage de l'agregateur...
echo  Appuyez sur Ctrl+C pour arreter
echo.

REM Configurer l'encodage UTF-8
chcp 65001 > nul

REM Lancer l'agrégateur en mode continu
python aggregate_all_media.py

echo.
echo ================================================================================
echo  Agregation arretee
echo ================================================================================
echo.
pause
