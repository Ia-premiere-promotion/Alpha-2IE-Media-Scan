# MONITORING TEMPS RÉEL LEFASO.NET

## Fichiers créés

### 1. `lefaso_realtime_monitor.py`
Script principal de monitoring en temps réel. 

**Fonctionnalités:**
- Détecte le **dernier post** automatiquement
- Met à jour les métriques de tous les posts
- Sauvegarde dans un fichier **JSON** (pas de doublons)
- Vérifie toutes les 10 minutes (configurable)

**Lancement:**
```bash
python lefaso_realtime_monitor.py
```

Ou utiliser le fichier batch:
```bash
start_lefaso_monitor.bat
```

### 2. `lefaso_scraper_single.py`
Scraping ponctuel (une seule fois)

```bash
python lefaso_scraper_single.py
```

### 3. Fichier de sortie: `lefaso_realtime.json`

Structure du JSON:
```json
{
  "posts": [
    {
      "post_id": "pfbid...",
      "url": "https://web.facebook.com/lefaso.net/posts/...",
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
    "page": "Lefaso.net",
    "page_url": "https://web.facebook.com/lefaso.net"
  }
}
```

### 4. `view_lefaso_data.py`
Visualisation formatée des données JSON

```bash
python view_lefaso_data.py
```

Affiche:
- Total posts et statistiques globales
- Détail de chaque post avec métriques
- Top 3 posts par engagement

---

## Comment ça marche

### Détection automatique du dernier post
Le script ne demande pas quel post monitorer. Il:
1. **Scrape la page** toutes les 10 minutes
2. **Détecte automatiquement le dernier post** (le plus récent)
3. **Met à jour toutes les métriques** de tous les posts déjà présents
4. **Ajoute les nouveaux posts** s'il y en a

### Pas de doublons
- Chaque post a un `post_id` unique
- Si le post existe déjà → mise à jour des métriques
- Si le post est nouveau → ajout dans le JSON

### Mise à jour des métriques
Pour chaque post, le script met à jour:
- Nombre de likes
- Nombre de commentaires
- Nombre de partages
- Engagement total
- Date de dernière mise à jour

---

## Configuration

### Intervalle de vérification
Modifier dans `lefaso_realtime_monitor.py`:

```python
monitor = LefasoRealtimeMonitor(check_interval=600)  # 600s = 10 minutes
```

Exemples:
- 5 minutes → `check_interval=300`
- 15 minutes → `check_interval=900`
- 30 minutes → `check_interval=1800`

### Nombre de posts à récupérer
Modifier dans `lefaso_realtime_monitor.py`:

```python
self.scraper.scrape_page(page_url, email, password, max_posts=50)
```

---

## Workflow typique

### 1. Premier lancement (scraping initial)
```bash
python lefaso_scraper_single.py
```
→ Crée `lefaso_posts.json` avec ~50 posts

### 2. Démarrer le monitoring temps réel
```bash
python lefaso_realtime_monitor.py
```
ou double-clic sur:
```bash
start_lefaso_monitor.bat
```

Le monitoring:
- Charge les posts existants depuis `lefaso_realtime.json` (s'il existe)
- Vérifie toutes les 10 minutes
- Détecte automatiquement les nouveaux posts
- Met à jour les métriques des posts existants
- Sauvegarde dans `lefaso_realtime.json`

### 3. Visualiser les données
```bash
python view_lefaso_data.py
```

---

## Fichiers de sortie

| Fichier | Description |
|---------|-------------|
| `lefaso_posts.json` | Scraping ponctuel (scraper_single.py) |
| `lefaso_realtime.json` | Monitoring temps réel (monitor.py) |

---

## Arrêter le monitoring

Appuyez sur **Ctrl+C** dans le terminal.

Le script:
1. Sauvegarde proprement les données
2. Ferme le navigateur
3. Affiche un message de confirmation

---

## Exemple de sortie

```
======================================================================
🔍 VÉRIFICATION - 2025-11-17 08:30:00
======================================================================
♻️ Réutilisation de la session...
🔍 Scraping de 50 posts maximum...
✅ 50 posts scrapés

🆕 NOUVEAU POST détecté:
   📝 Lefaso.net annonce une nouvelle...
   👍 25 likes | 💬 3 comments | 🔄 2 shares

🔄 MISE À JOUR:
   📝 Article sur la santé publique...
   📊 +15 engagement
      👍 100 → 110 (+10)
      💬 5 → 8 (+3)
      🔄 2 → 4 (+2)

======================================================================
📊 RÉSUMÉ:
   🆕 1 nouveau(x) post(s)
   🔄 3 mise(s) à jour
   💾 51 posts au total dans JSON
======================================================================
💾 51 posts sauvegardés dans lefaso_realtime.json

⏸️ Prochaine vérification dans 10 minutes...
   (Appuyez sur Ctrl+C pour arrêter)
```
