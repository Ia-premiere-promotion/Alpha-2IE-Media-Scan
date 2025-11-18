# 🔴 Monitoring Temps Réel - Facebook Observateur Paalga

Script de surveillance automatique qui vérifie la page Facebook **toutes les 10 minutes** et détecte les nouveaux posts en temps réel.

## 🎯 Fonctionnalités

- ✅ **Vérification automatique** toutes les 10 minutes (configurable)
- ✅ **Détection des nouveaux posts** en temps réel
- ✅ **Sauvegarde incrémentale** dans un seul fichier JSON
- ✅ **Mode headless** (invisible, pas de fenêtre)
- ✅ **Statistiques en temps réel**
- ✅ **Arrêt propre** avec Ctrl+C
- ✅ **Reprise automatique** des posts existants

## 📦 Fichiers

- `facebook_realtime_monitor.py` - Script de monitoring
- `observateur_paalga_stream.json` - Flux en temps réel des posts
- `.env` - Configuration (intervalle, identifiants)

## ▶️ Démarrage

```powershell
# Lancer le monitoring
python facebook_realtime_monitor.py
```

Le script va :
1. 🔍 Vérifier immédiatement les nouveaux posts
2. ⏰ Attendre 10 minutes
3. 🔄 Vérifier à nouveau
4. 💾 Sauvegarder automatiquement chaque nouveau post
5. ♾️ Répéter indéfiniment jusqu'à Ctrl+C

## ⚙️ Configuration

Modifiez `.env` pour changer l'intervalle :

```bash
# Vérification toutes les 5 minutes
CHECK_INTERVAL=300

# Vérification toutes les 30 minutes
CHECK_INTERVAL=1800

# Vérification toutes les heures
CHECK_INTERVAL=3600
```

## 📊 Sortie JSON

Le fichier `observateur_paalga_stream.json` contient :

```json
{
  "posts": [
    {
      "post_id": "...",
      "url": "...",
      "source": "Facebook - Observateur Paalga",
      "date_post": "2025-11-17T04:00:00",
      "contenu": "...",
      "type_post": "status",
      "likes": 59,
      "comments": 7,
      "shares": 0,
      "engagement_total": 66,
      "commentaires": [...]
    }
  ],
  "metadata": {
    "total_posts": 10,
    "last_update": "2025-11-17T04:00:00",
    "total_engagement": 500,
    "monitoring_started": "2025-11-17T03:00:00"
  }
}
```

## 🎬 Exemple d'utilisation

```
============================================================
🔴 MONITORING TEMPS RÉEL - Observateur Paalga
============================================================
📍 Page: https://web.facebook.com/lobspaalgaBF
⏱️  Intervalle: 10 minutes
💾 Fichier: observateur_paalga_stream.json
============================================================

🚀 Première vérification immédiate...
🔍 Vérification de nouveaux posts... (03:45:00)
✅ Aucun nouveau post

⏳ Prochaine vérification dans 10 minutes...
   (Appuyez sur Ctrl+C pour arrêter)
   ⏰ 10 minute(s) restante(s)...

======================================================================
🔄 Vérification #2 - 2025-11-17 03:55:00
======================================================================
🔍 Vérification de nouveaux posts... (03:55:00)

🎉 1 NOUVEAU(X) POST(S) DÉTECTÉ(S) ! 🎉

📌 Post #1
   📝 Contenu: Breaking news : Incident majeur à Ouagadougou...
   🔗 URL: https://web.facebook.com/lobspaalgaBF/posts/...
   📅 Date: 2025-11-17T03:50:00
   👍 12 likes | 💬 3 commentaires | 🔄 5 partages
   📊 Engagement total: 20

✅ Nouveaux posts sauvegardés !

📊 STATISTIQUES GLOBALES:
   Total posts collectés: 2
   Engagement total: 86
   Vérifications effectuées: 2
```

## ⏹️ Arrêter le monitoring

Appuyez sur **Ctrl+C** pour arrêter proprement :

```
⏹️  MONITORING ARRÊTÉ PAR L'UTILISATEUR
======================================================================
📊 Résumé final:
   ✅ 15 posts collectés au total
   ✅ 48 vérifications effectuées
   💾 Données sauvegardées dans: observateur_paalga_stream.json
======================================================================
```

## 🔄 Reprise après arrêt

Le script charge automatiquement les posts existants au redémarrage. Il ne collectera que les **nouveaux** posts, sans doublons.

## 📈 Avantages

- ✅ **Temps réel** : Ne rate aucun nouveau post
- ✅ **Efficace** : Vérifications espacées (pas de spam)
- ✅ **Persistant** : Sauvegarde automatique
- ✅ **Intelligent** : Détection des doublons
- ✅ **Discret** : Mode headless (invisible)
- ✅ **Robuste** : Gestion des erreurs

## 🛠️ Conseils

- Laissez tourner **24/7** sur un serveur pour une surveillance continue
- Ajustez `CHECK_INTERVAL` selon vos besoins
- Consultez `observateur_paalga_stream.json` pour voir tous les posts collectés
- Le fichier JSON est mis à jour en temps réel

## 🔒 Sécurité

- Vos identifiants sont dans `.env` (pas partagés)
- Ajoutez `.env` au `.gitignore`
- Mode headless ne laisse pas de traces visuelles
