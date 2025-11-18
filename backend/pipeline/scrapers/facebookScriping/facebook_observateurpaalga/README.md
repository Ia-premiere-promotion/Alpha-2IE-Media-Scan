# Facebook Graph API Scraper - Observateur Paalga

Script Python pour extraire les publications de la page Facebook **Observateur Paalga** via l'API Graph de Facebook.

## 🎯 Fonctionnalités

- ✅ Extraction des publications via l'API officielle Graph
- ✅ Récupération des métriques d'engagement (likes, comments, shares)
- ✅ Extraction des commentaires de chaque post
- ✅ Sauvegarde au format JSON standardisé
- ✅ Gestion des erreurs et pagination

## 📋 Prérequis

1. **Compte développeur Facebook**
   - Créer un compte sur [Facebook Developers](https://developers.facebook.com/)
   
2. **Application Facebook**
   - Créer une application sur le portail développeur
   - Obtenir un token d'accès avec les permissions nécessaires

3. **Python 3.7+**

## 🚀 Installation

```powershell
# Installer les dépendances
pip install -r requirements.txt
```

## 🔑 Obtenir un Token d'Accès

### Méthode 1 : Graph API Explorer (pour tester)

1. Aller sur [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Sélectionner votre application
3. Cliquer sur "Generate Access Token"
4. Sélectionner les permissions :
   - `pages_read_engagement`
   - `pages_show_list`
5. Copier le token généré

⚠️ **Note** : Les tokens du Graph Explorer expirent rapidement (1-2h). Pour une utilisation long terme, voir la méthode 2.

### Méthode 2 : Token Long Terme (recommandé)

```python
# Convertir un token court en token long terme
import requests

APP_ID = "votre_app_id"
APP_SECRET = "votre_app_secret"
SHORT_TOKEN = "votre_token_court"

url = f"https://graph.facebook.com/v18.0/oauth/access_token"
params = {
    'grant_type': 'fb_exchange_token',
    'client_id': APP_ID,
    'client_secret': APP_SECRET,
    'fb_exchange_token': SHORT_TOKEN
}

response = requests.get(url, params=params)
long_token = response.json()['access_token']
print(long_token)
```

## 📝 Configuration

Éditer `facebook_scraper.py` et remplacer :

```python
ACCESS_TOKEN = "VOTRE_TOKEN_ICI"  # Votre token d'accès
PAGE_ID = "lobspaalgaBF"           # ID de la page à scraper
```

## ▶️ Utilisation

```powershell
# Exécuter le script
python facebook_scraper.py
```

Le script va :
1. Se connecter à l'API Graph
2. Récupérer les 50 derniers posts de la page
3. Extraire les commentaires de chaque post
4. Sauvegarder les données dans `observateur_paalga_posts.json`

## 📊 Format de Sortie

```json
{
  "posts": [
    {
      "post_id": "123456789_987654321",
      "url": "https://www.facebook.com/...",
      "source": "Facebook - lobspaalgaBF",
      "date_post": "2025-11-17T10:30:00+0000",
      "contenu": "Texte du post...",
      "type_post": "status",
      "likes": 150,
      "comments": 25,
      "shares": 10,
      "engagement_total": 185,
      "commentaires": [
        {"numero": 1, "texte": "Commentaire 1...", "auteur": "User1", "date": "..."},
        {"numero": 2, "texte": "Commentaire 2...", "auteur": "User2", "date": "..."}
      ]
    }
  ],
  "metadata": {
    "page_id": "lobspaalgaBF",
    "total_posts": 50,
    "scraped_at": "2025-11-17T12:00:00",
    "total_engagement": 5420
  }
}
```

## 🛠️ Personnalisation

### Modifier le nombre de posts

```python
scraper.scrape_and_save(
    page_id=PAGE_ID,
    output_file='output.json',
    limit=100  # Récupérer 100 posts
)
```

### Changer les champs extraits

Modifier la liste `fields` dans `get_page_posts()` :

```python
fields = [
    'id',
    'message',
    'created_time',
    'full_picture',  # Ajouter l'image
    'reactions.summary(true)',  # Détailler les réactions
    # ... autres champs
]
```

## 📚 Champs Disponibles

L'API Graph offre de nombreux champs :
- `message` : Texte du post
- `story` : Description générée automatiquement
- `full_picture` : URL de l'image
- `video` : Données vidéo
- `reactions` : Détails des réactions (love, haha, wow, etc.)
- `attachments` : Pièces jointes
- `insights` : Statistiques (nécessite permissions supplémentaires)

[Documentation complète](https://developers.facebook.com/docs/graph-api/reference/post/)

## ⚠️ Limitations

- **Rate limiting** : L'API limite le nombre de requêtes (200 appels/heure pour un user token)
- **Permissions** : Certaines données nécessitent des permissions spéciales
- **Pages publiques** : Plus facile d'accès que les profils personnels
- **Données historiques** : Limité aux posts récents selon les permissions

## 🔍 Debugging

Activer les logs détaillés :

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Tester une requête simple :

```python
scraper = FacebookGraphScraper(ACCESS_TOKEN)
url = f"{scraper.base_url}/me?access_token={ACCESS_TOKEN}"
response = requests.get(url)
print(response.json())  # Vérifier que le token fonctionne
```

## 📖 Ressources

- [Graph API Documentation](https://developers.facebook.com/docs/graph-api/)
- [Page Insights](https://developers.facebook.com/docs/graph-api/reference/page/insights/)
- [Permissions de l'API](https://developers.facebook.com/docs/permissions/reference)

## 🤝 Support

Pour toute question sur :
- L'API Graph : [Documentation Facebook](https://developers.facebook.com/support/)
- Ce script : Ouvrir une issue sur le repository
