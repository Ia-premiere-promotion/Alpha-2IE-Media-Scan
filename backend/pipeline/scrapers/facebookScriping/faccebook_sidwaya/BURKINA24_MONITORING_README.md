# 🔴 Monitoring en Temps Réel - Burkina24

Système de surveillance en temps réel de la page Facebook Burkina24 pour détecter les nouveaux posts et mettre à jour les métriques automatiquement.

## 📋 Fonctionnalités

✅ **Détection automatique des nouveaux posts**
✅ **Mise à jour en temps réel des métriques** (likes, commentaires, partages)
✅ **Extraction des commentaires** avec auteur et contenu
✅ **Sauvegarde automatique** des données en JSON
✅ **Surveillance continue** avec intervalle configurable
✅ **Visualiseur de données** en temps réel

## 🚀 Démarrage Rapide

### 1. Configuration

Assurez-vous que votre fichier `.env` contient :

```env
FB_EMAIL=votre_email@example.com
FB_PASSWORD=votre_mot_de_passe
CHECK_INTERVAL=60          # Intervalle en secondes (optionnel, défaut: 60)
HEADLESS=False             # True pour mode invisible (optionnel)
```

### 2. Lancer le Monitoring

**Option A - Via le fichier batch (Windows) :**
```bash
start_burkina24_monitor.bat
```

**Option B - Via Python :**
```bash
python burkina24_realtime_monitor.py
```

### 3. Visualiser les Données

**En temps réel :**
```bash
python view_burkina24_data.py
```

Puis choisissez l'option 2 pour le mode surveillance.

## 📊 Structure des Données

Les données sont sauvegardées dans `burkina24_realtime.json` :

```json
{
  "posts": [
    {
      "post_id": "burkina24_abc123",
      "url": "https://web.facebook.com/Burkina24/posts/...",
      "source": "Facebook - Burkina24",
      "date_post": "2025-11-17T14:30:00",
      "contenu": "Contenu du post...",
      "likes": 150,
      "comments": 25,
      "shares": 10,
      "engagement_total": 185,
      "commentaires": [
        {
          "numero": 1,
          "auteur": "Nom de l'utilisateur",
          "texte": "Contenu du commentaire..."
        }
      ],
      "last_update": "2025-11-17T14:35:00"
    }
  ],
  "metadata": {
    "total_posts": 10,
    "last_update": "2025-11-17T14:35:00",
    "total_engagement": 1850,
    "page": "Burkina24"
  }
}
```

## 🔧 Configuration Avancée

### Modifier l'intervalle de vérification

Dans le fichier `.env` :
```env
CHECK_INTERVAL=30  # Vérifier toutes les 30 secondes
```

Ou directement dans le code (`burkina24_realtime_monitor.py`) :
```python
monitor.start_monitoring(email, password, interval=30)
```

### Mode Headless (invisible)

Pour exécuter sans afficher le navigateur :
```env
HEADLESS=True
```

## 📈 Fonctionnement

1. **Connexion** à Facebook avec vos identifiants
2. **Navigation** vers la page Burkina24
3. **Scan initial** de tous les posts visibles
4. **Boucle de surveillance** :
   - Rafraîchit la page toutes les X secondes
   - Détecte les nouveaux posts
   - Met à jour les métriques des posts existants
   - Extrait les commentaires
   - Sauvegarde les données

## 🛑 Arrêt du Monitoring

Appuyez sur **Ctrl+C** dans le terminal pour arrêter proprement le monitoring.

## 📝 Fichiers Créés

- `burkina24_realtime_monitor.py` - Script principal de monitoring
- `burkina24_realtime.json` - Données en temps réel
- `view_burkina24_data.py` - Visualiseur de données
- `start_burkina24_monitor.bat` - Lanceur rapide (Windows)

## ⚠️ Notes Importantes

- Le monitoring consomme des ressources (navigateur ouvert en permanence)
- Respectez les limites d'utilisation de Facebook
- Les données sont écrasées à chaque sauvegarde (versionnage recommandé si nécessaire)
- Un intervalle trop court (< 30 secondes) peut être détecté comme suspect par Facebook

## 🎯 Cas d'Usage

- **Veille médiatique** : Suivre l'actualité en temps réel
- **Analyse d'engagement** : Voir comment les métriques évoluent
- **Modération** : Détecter rapidement les nouveaux commentaires
- **Archivage** : Conserver l'historique complet des posts

## 🔍 Dépannage

**Problème : Le monitoring ne détecte pas de nouveaux posts**
- Vérifiez que la page charge correctement
- Augmentez le délai de scroll dans le code
- Vérifiez votre connexion Internet

**Problème : Les commentaires ne sont pas extraits**
- Les commentaires sont extraits uniquement s'ils sont visibles
- Le script clique automatiquement pour les afficher
- Certains posts peuvent ne pas avoir de commentaires

**Problème : Erreur de connexion Facebook**
- Vérifiez vos identifiants dans le `.env`
- Facebook peut demander une vérification (désactivez le mode headless pour voir)
- Essayez de vous connecter manuellement d'abord

## 📞 Support

Pour toute question ou problème, consultez les logs affichés dans le terminal.
