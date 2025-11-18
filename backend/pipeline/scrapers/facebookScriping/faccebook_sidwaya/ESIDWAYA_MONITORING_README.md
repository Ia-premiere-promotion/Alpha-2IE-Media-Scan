# MONITORING TEMPS RÉEL ESIDWAYA

## Fichiers créés

### 1. `esidwaya_realtime_monitor.py`
Script principal de monitoring en temps réel. 

**Fonctionnalités:**
- Détecte le **dernier post** automatiquement
- Met à jour les métriques de tous les posts
- Sauvegarde dans un fichier **JSON** (pas de doublons)
- Vérifie toutes les 10 minutes (configurable)

**Lancement:**
```bash
python esidwaya_realtime_monitor.py
```

Ou utiliser le fichier batch:
```bash
start_esidwaya_monitor.bat
```

### 2. `esidwaya_scraper_single.py`
Scraping ponctuel (une seule fois)

```bash
python esidwaya_scraper_single.py
```

### 3. Fichier de sortie: `esidwaya_realtime.json`

Structure du JSON:
```json
{
  "posts": [
    {
      "post_id": "pfbid...",
      "url": "https://web.facebook.com/ESidwaya/posts/...",
      "date_post": "2025-11-17T08:23:02.548009",
      "contenu": "Contenu du post...",
      "likes": 19,
      "comments": 0,
      "shares": 0,
      "engagement_total": 19,
      "last_update": "2025-11-17T08:30:00.000000"
    }
  ],
  "metadata": {
    "total_posts": 1,
    "last_update": "2025-11-17T08:30:00.000000",
    "total_engagement": 19,
    "total_likes": 19,
    "total_comments": 0,
    "total_shares": 0,
    "page": "ESidwaya",
    "page_url": "https://web.facebook.com/ESidwaya"
  }
}
```

### 4. Visualisation des données

```bash
python view_esidwaya_data.py
```

Affiche:
- Total de posts
- Statistiques globales
- Détails de chaque post
- Top 3 posts par engagement

## Configuration

Dans le fichier `.env`:
```
FB_EMAIL=votre_email@gmail.com
FB_PASSWORD=votre_mot_de_passe
CHECK_INTERVAL=600  # 10 minutes
NUM_SCROLLS=20
```

## Fonctionnement

1. **Détection du dernier post**: Le scraper récupère les 50 posts les plus récents
2. **Nouveaux posts**: Ajoutés automatiquement au JSON
3. **Posts existants**: Métriques mises à jour (likes, comments, shares)
4. **Pas de doublons**: Chaque post_id est unique
5. **Tri**: Posts classés du plus récent au plus ancien

## Améliorations apportées

✅ **Extraction depuis JSON** - Pour les pages comme ESidwaya qui utilisent du JSON embarqué
✅ **Métriques corrigées** - Filtre les années (2025) qui étaient prises pour des likes
✅ **Métriques depuis JSON** - Extraction depuis `reaction_count`, `total_comment_count`
✅ **Keywords configurables** - Support de multiples pages Facebook
✅ **Export JSON** - Format structuré et facile à exploiter
✅ **Timeout augmentés** - 60s au lieu de 30s pour éviter les timeouts

## Arrêter le monitoring

Appuyez sur `Ctrl+C` dans le terminal. Le script sauvegarde automatiquement avant de s'arrêter.
