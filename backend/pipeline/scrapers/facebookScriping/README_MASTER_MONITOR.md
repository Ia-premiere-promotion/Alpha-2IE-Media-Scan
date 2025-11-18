# 🚀 Monitoring en Temps Réel - Tous les Médias

Ce projet permet de surveiller en temps réel tous les médias burkinabés simultanément.

## 📋 Médias Surveillés

1. **Burkina24** - `facebook_burkina24/`
2. **Lefaso.net** - `facebook_fasonet/`
3. **Fasopresse** - `facebook_fasopresse/`
4. **ESidwaya** - `faccebook_sidwaya/`
5. **Observateur Paalga** - `facebook_observateurpaalga/`

## 🎯 Utilisation

### Méthode Simple (Recommandée)

Double-cliquez sur le fichier :

```
START_ALL_MONITORS.bat
```

### Méthode Alternative (Ligne de commande)

```powershell
python master_realtime_monitor.py
```

## 📊 Fonctionnement

Le script `master_realtime_monitor.py` :

1. ✅ Vérifie que tous les dossiers et scripts existent
2. 🚀 Lance tous les monitors en parallèle dans des processus séparés
3. 📡 Affiche les logs de tous les médias en temps réel
4. 💾 Chaque monitor sauvegarde ses données dans son propre fichier JSON
5. ⏹️ Permet d'arrêter tous les monitors avec `Ctrl+C`

## 📁 Structure des Fichiers de Sortie

Chaque média génère son propre fichier JSON dans son dossier :

- `burkina24_realtime.json` (Burkina24)
- `lefaso_realtime.json` (Lefaso.net)
- `fasopresse_realtime.json` (Fasopresse)
- `esidwaya_realtime.json` (ESidwaya)
- `observateur_paalga_stream.json` (Observateur Paalga)

## ⚙️ Configuration

Chaque dossier de média contient :
- Un fichier `.env` avec les identifiants Facebook
- Un script de monitoring spécifique
- Un fichier `requirements.txt` avec les dépendances

## 🛑 Arrêt du Monitoring

Appuyez sur `Ctrl+C` dans la console pour arrêter proprement tous les monitors.

## 📝 Logs

Les logs de tous les médias sont affichés en temps réel dans la console, préfixés par le nom du média :

```
[Burkina24] 📊 Nouveau post détecté...
[Lefaso.net] ✅ Métriques mises à jour...
[Fasopresse] 🔄 Vérification en cours...
```

## 🔧 Dépannage

Si un monitor ne démarre pas :

1. Vérifiez que le dossier existe
2. Vérifiez que le fichier `.env` contient les identifiants
3. Vérifiez que les dépendances sont installées (`pip install -r requirements.txt`)
4. Consultez les logs d'erreur dans la console

## 📦 Installation des Dépendances

Pour installer les dépendances de tous les médias :

```powershell
cd facebook_burkina24
pip install -r requirements.txt

cd ../facebook_fasonet
pip install -r requirements.txt

cd ../facebook_fasopresse
pip install -r requirements.txt

cd ../faccebook_sidwaya
pip install -r requirements.txt

cd ../facebook_observateurpaalga
pip install -r requirements.txt
```

Ou utilisez le script d'installation automatique (si disponible).

## 💡 Conseils

- Laissez le monitoring tourner en continu pour ne manquer aucun post
- Vérifiez régulièrement les fichiers JSON pour voir les données collectées
- Chaque média a son propre intervalle de vérification (généralement 10 minutes)
- Les données sont sauvegardées automatiquement après chaque mise à jour

## 🎨 Personnalisation

Pour modifier l'intervalle de vérification d'un média, éditez le paramètre `check_interval` dans le script correspondant (valeur en secondes).

## ✅ Vérification

Le script vérifie automatiquement :
- ✅ Présence de tous les dossiers
- ✅ Présence de tous les scripts de monitoring
- ✅ Affiche un résumé avant de démarrer

---

**Auteur** : Script de monitoring centralisé  
**Date** : Novembre 2025  
**Version** : 1.0
