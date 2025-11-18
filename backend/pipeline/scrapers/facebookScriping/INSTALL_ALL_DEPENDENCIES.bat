@echo off
title Installation des Dependances - Tous les Medias
color 0B

echo ================================================================================
echo.
echo           INSTALLATION DES DEPENDANCES - TOUS LES MEDIAS
echo.
echo ================================================================================
echo.
echo  Ce script installe les dependances Python pour tous les medias
echo.
echo ================================================================================
echo.

REM Liste des dossiers à traiter
set folders=Jesus_aide_moi_burkina24 Jesus_aide_moi_fasonet Jesus_aide_moi_fasopresse Jesus_aide_moi_sidwaya Jesus_aide_moi_observateurpaalga

echo [1/5] Installation des dependances pour Burkina24...
echo.
cd Jesus_aide_moi_burkina24
if exist requirements.txt (
    pip install -r requirements.txt
    echo.
    echo ✅ Burkina24 - Dependances installees
) else (
    echo ⚠️  Fichier requirements.txt non trouve
)
cd ..
echo.
echo ================================================================================
echo.

echo [2/5] Installation des dependances pour Lefaso.net...
echo.
cd Jesus_aide_moi_fasonet
if exist requirements.txt (
    pip install -r requirements.txt
    echo.
    echo ✅ Lefaso.net - Dependances installees
) else (
    echo ⚠️  Fichier requirements.txt non trouve
)
cd ..
echo.
echo ================================================================================
echo.

echo [3/5] Installation des dependances pour Fasopresse...
echo.
cd Jesus_aide_moi_fasopresse
if exist requirements.txt (
    pip install -r requirements.txt
    echo.
    echo ✅ Fasopresse - Dependances installees
) else (
    echo ⚠️  Fichier requirements.txt non trouve
)
cd ..
echo.
echo ================================================================================
echo.

echo [4/5] Installation des dependances pour ESidwaya...
echo.
cd Jesus_aide_moi_sidwaya
if exist requirements.txt (
    pip install -r requirements.txt
    echo.
    echo ✅ ESidwaya - Dependances installees
) else (
    echo ⚠️  Fichier requirements.txt non trouve
)
cd ..
echo.
echo ================================================================================
echo.

echo [5/5] Installation des dependances pour Observateur Paalga...
echo.
cd Jesus_aide_moi_observateurpaalga
if exist requirements.txt (
    pip install -r requirements.txt
    echo.
    echo ✅ Observateur Paalga - Dependances installees
) else (
    echo ⚠️  Fichier requirements.txt non trouve
)
cd ..
echo.
echo ================================================================================
echo.
echo ✅ Installation terminee pour tous les medias !
echo.
echo Vous pouvez maintenant lancer : START_ALL_MONITORS.bat
echo.
echo ================================================================================
echo.
pause
