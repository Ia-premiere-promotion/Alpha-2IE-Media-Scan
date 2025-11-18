# Analyseur Déontologique d'Articles Journalistiques

Script d'analyse automatique du respect de la déontologie journalistique utilisant Google Gemini.

## Installation

```bash
# Installer les dépendances
pip install -r requirements.txt
```

## Configuration

1. Copiez le fichier de configuration exemple :
```bash
cp config.json.example config.json
```

2. Éditez `config.json` avec vos paramètres :
```json
{
  "database": {
    "host": "localhost",
    "port": 5432,
    "dbname": "votre_database",
    "user": "votre_utilisateur",
    "password": "votre_mot_de_passe"
  },
  "gemini_api_key": "VOTRE_CLE_API_GEMINI"
}
```

## Utilisation

### Analyser tous les articles
```bash
python analyze_deontology.py
```

### Analyser les 5 derniers articles
```bash
python analyze_deontology.py --limit 5
```

### Analyser un article spécifique
```bash
python analyze_deontology.py --article-id "ID_DE_L_ARTICLE"
```

### Sauvegarder les résultats dans un fichier
```bash
python analyze_deontology.py --limit 10 --output resultats.json
```

## Format de sortie

Le script retourne un JSON avec :

```json
{
  "interpretation": "Description en 2 lignes de l'analyse",
  "score": 8
}
```

### Échelle de notation (sur 10)

- **10/10** : Contenu exemplaire, respect total de la déontologie
- **8-9/10** : Contenu correct avec de légères réserves
- **6-7/10** : Contenu acceptable mais avec des problèmes mineurs
- **4-5/10** : Contenu problématique avec infractions modérées
- **2-3/10** : Contenu grave (diffamation, incitation à la haine)
- **0-1/10** : Contenu inacceptable, violations majeures multiples

## Critères d'évaluation

1. **Diffamation** : Accusations non fondées
2. **Insultes** : Langage offensant ou injurieux
3. **Fausses allégations** : Informations non vérifiées
4. **Incitation à la haine** : Propos discriminatoires
5. **Partialité excessive** : Manque d'objectivité
6. **Respect de la vie privée** : Atteintes injustifiées
7. **Présomption d'innocence** : Non-respect du principe
8. **Vérification des sources** : Absence de fact-checking

## Intégration dans un backend

Le script peut être importé comme module :

```python
from analyze_deontology import DeontologyAnalyzer

analyzer = DeontologyAnalyzer(
    db_config={
        "host": "localhost",
        "port": 5432,
        "dbname": "mydb",
        "user": "user",
        "password": "pass"
    },
    gemini_api_key="YOUR_API_KEY"
)

analyzer.connect_db()
analysis = analyzer.analyze_content(
    titre="Titre de l'article",
    contenu="Contenu de l'article..."
)
analyzer.close_db()

print(analysis)
# {'interpretation': '...', 'score': 8}
```
