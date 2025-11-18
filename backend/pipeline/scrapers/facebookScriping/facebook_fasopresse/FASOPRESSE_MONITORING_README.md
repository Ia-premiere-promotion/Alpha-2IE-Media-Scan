# 📊 Monitoring Fasopresse - Guide d'utilisation

## 📝 Description

Système de monitoring et scraping de la page Facebook **Fasopresse** (L'actualité du Burkina Faso).

**Page Facebook:** https://web.facebook.com/p/Fasopresse-Lactualit%C3%A9-du-Burkina-Faso-100067981629793/

## 🚀 Installation

### 1. Prérequis
- Python 3.8+
- Navigateur Chromium (installé automatiquement par Playwright)

### 2. Installation des dépendances

```bash
pip install -r requirements.txt
```

### 3. Installation de Playwright

```bash
playwright install chromium
```

### 4. Configuration des identifiants Facebook

Créez un fichier `.env` à la racine du projet :

```env
FACEBOOK_EMAIL=votre_email@example.com
FACEBOOK_PASSWORD=votre_mot_de_passe
```

**⚠️ Important:** Ne partagez JAMAIS votre fichier `.env` !

## 📁 Fichiers du projet

### Scripts principaux

1. **`fasopresse_realtime_monitor.py`**
   - Monitoring en temps réel (exécution continue)
   - Vérifie les nouveaux posts toutes les 10 minutes
   - Met à jour `fasopresse_realtime.json` automatiquement
   - Pas de doublons, mise à jour des métriques

2. **`fasopresse_scraper_single.py`**
   - Scraping unique (une seule exécution)
   - Récupère jusqu'à 50 posts
   - Sauvegarde dans `fasopresse_posts.json`

3. **`view_fasopresse_data.py`**
   - Visualise les données collectées
   - Affiche les statistiques
   - Montre les posts les plus engageants

### Fichiers de support

- **`start_fasopresse_monitor.bat`** : Lance le monitoring sur Windows
- **`facebook_playwright_scraper.py`** : Module de scraping (partagé)
- **`.env`** : Identifiants Facebook (à créer)

## 🎯 Utilisation

### Option 1: Monitoring en temps réel (recommandé)

**Windows:**
```bash
# Double-cliquez sur le fichier .bat
start_fasopresse_monitor.bat

# OU en ligne de commande
python fasopresse_realtime_monitor.py
```

**Linux/Mac:**
```bash
python fasopresse_realtime_monitor.py
```

**Comportement:**
- ✅ Vérifie la page toutes les 10 minutes
- ✅ Détecte les nouveaux posts automatiquement
- ✅ Met à jour les métriques (likes, commentaires, partages)
- ✅ Pas de doublons dans le JSON
- ✅ Fonctionne 24/7 (arrêt avec Ctrl+C)

### Option 2: Scraping unique

```bash
python fasopresse_scraper_single.py
```

**Comportement:**
- ✅ Exécution unique
- ✅ Récupère jusqu'à 50 posts
- ✅ Sauvegarde dans `fasopresse_posts.json`
- ✅ Utile pour des exports ponctuels

### Option 3: Visualisation des données

```bash
python view_fasopresse_data.py
```

**Affiche:**
- 📊 Statistiques globales (total posts, engagement, etc.)
- 📰 Les 10 derniers posts
- 🔥 Top 5 des posts les plus engageants
- 📈 Engagement moyen par post

## 📊 Format des données

### Structure du JSON (`fasopresse_realtime.json`)

```json
{
  "posts": [
    {
      "post_id": "pfbid0...",
      "url": "https://web.facebook.com/...",
      "text": "Contenu du post...",
      "date_post": "2025-11-17T14:30:00",
      "likes": 150,
      "comments": 25,
      "shares": 10,
      "engagement_total": 185,
      "medias": [
        {
          "type": "image",
          "url": "https://..."
        }
      ]
    }
  ],
  "metadata": {
    "total_posts": 50,
    "last_update": "2025-11-17T15:00:00",
    "total_engagement": 5420,
    "total_likes": 3200,
    "total_comments": 1850,
    "total_shares": 370,
    "page": "Fasopresse",
    "page_url": "https://web.facebook.com/p/Fasopresse-Lactualit%C3%A9-du-Burkina-Faso-100067981629793/"
  }
}
```

## ⚙️ Configuration avancée

### Modifier l'intervalle de vérification

Dans `fasopresse_realtime_monitor.py`, ligne 216 :

```python
# Par défaut: 600 secondes (10 minutes)
monitor = FasopresseRealtimeMonitor(check_interval=600)

# Exemples:
monitor = FasopresseRealtimeMonitor(check_interval=300)   # 5 minutes
monitor = FasopresseRealtimeMonitor(check_interval=1800)  # 30 minutes
```

### Modifier le nombre de posts récupérés

Dans `fasopresse_scraper_single.py`, ligne 109 :

```python
scrape_fasopresse_once(
    email=email,
    password=password,
    max_posts=50,    # Nombre de posts
    scrolls=5        # Nombre de scrolls (plus = plus de posts)
)
```

### Mode headless (sans interface graphique)

Dans `fasopresse_realtime_monitor.py`, ligne 101 :

```python
# headless=True : sans interface (recommandé pour serveur)
# headless=False : avec interface (utile pour déboguer)
self.scraper = FacebookPlaywrightScraper(headless=True, page_keywords=self.page_keywords)
```

## 🔧 Dépannage

### Problème: "Variables d'environnement manquantes"

**Solution:** Créez le fichier `.env` avec vos identifiants Facebook

### Problème: Playwright ne trouve pas le navigateur

**Solution:**
```bash
playwright install chromium
```

### Problème: Erreur de connexion Facebook

**Solutions:**
- Vérifiez vos identifiants dans `.env`
- Désactivez l'authentification à 2 facteurs (temporairement)
- Essayez avec `headless=False` pour voir ce qui se passe

### Problème: Aucun post récupéré

**Solutions:**
- Vérifiez que l'URL de la page est correcte
- Augmentez le nombre de scrolls
- Vérifiez les mots-clés de validation dans le script

## 📈 Métriques collectées

Pour chaque post:
- ✅ **ID unique** du post
- ✅ **URL** complète
- ✅ **Texte** du contenu
- ✅ **Date** de publication
- ✅ **Likes** (nombre de J'aime)
- ✅ **Commentaires** (nombre)
- ✅ **Partages** (nombre)
- ✅ **Engagement total** (likes + commentaires + partages)
- ✅ **Médias** (images, vidéos, liens)

## 🎯 Cas d'usage

### 1. Monitoring continu pour analyse

```bash
# Lancer et laisser tourner
python fasopresse_realtime_monitor.py
```

### 2. Export ponctuel pour rapport

```bash
# Récupérer les données
python fasopresse_scraper_single.py

# Visualiser
python view_fasopresse_data.py
```

### 3. Analyse comparative

```python
# Comparer avec d'autres pages
# - Lefaso: lefaso_realtime.json
# - Fasopresse: fasopresse_realtime.json
# - Observateur Paalga: (à créer)
```

## 📝 Notes importantes

1. **Respect de Facebook:** Ne lancez pas trop de scrapers simultanément
2. **Limites:** Facebook peut bloquer les comptes trop actifs
3. **Données:** Les JSON sont mis à jour automatiquement (pas de doublons)
4. **Performance:** Le mode headless est plus rapide et consomme moins de ressources

## 🆘 Support

En cas de problème:
1. Vérifiez les logs dans le terminal
2. Essayez en mode non-headless pour visualiser
3. Consultez la documentation de Playwright

## 📄 Licence

Ce projet est à usage personnel et éducatif.

---

**Dernière mise à jour:** 17 novembre 2025
