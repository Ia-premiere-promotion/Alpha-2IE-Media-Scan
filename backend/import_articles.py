import os
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv
import numpy as np
from tqdm import tqdm
from supabase_client import get_supabase_client
from datetime import datetime
import pytz

# Configuration de Supabase
load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in your .env file.")

supabase: Client = create_client(url, key)

# Initialiser le client Supabase
supabase = get_supabase_client()

# Chemin vers le fichier CSV des articles
file_path = '/home/bakouan/Bureau/APP MEDIA SCAN/backend/medias_unified_cleaned.csv'

def normalize_media_name(name):
    """Normalise le nom du média pour trouver une correspondance."""
    name = name.lower().strip()
    
    # Dictionnaire de correspondances
    media_map = {
        "burkina24": "Burkina24",
        "l'observateur paalga": "L'Observateur Paalga",
        "lobservateur": "L'Observateur Paalga",
        "sidwaya": "Sidwaya",
        "faso presse": "FasoPresse",
        "fasopresse": "FasoPresse",
        "lefaso.net": "LeFaso",  # Correspondance avec "LeFaso" dans la BD
        "lefaso": "LeFaso"
    }
    
    # Recherche exacte d'abord
    if name in media_map:
        return media_map[name]
    
    # Recherche par similarité si pas de correspondance exacte
    for key, value in media_map.items():
        if key in name or name in key:
            return value
            
    return None

def import_data():
    """
    Lit le CSV des articles et peuple les tables categories, articles, et engagements.
    """
    try:
        df = pd.read_csv(file_path)
        print(f"Fichier CSV '{file_path}' lu avec succès, {len(df)} lignes trouvées.")
    except FileNotFoundError:
        print(f"Erreur : Le fichier {file_path} n'a pas été trouvé.")
        return
    except Exception as e:
        print(f"Une erreur est survenue lors de la lecture du CSV : {e}")
        return

    # --- 1. Gérer les Catégories ---
    print("\n--- Étape 1: Gestion des catégories ---")
    unique_categories = df['categorie'].dropna().unique()
    print(f"Catégories uniques trouvées dans le CSV : {len(unique_categories)}")
    
    categories_to_upsert = [{'nom': name} for name in unique_categories]
    supabase.table('categories').upsert(categories_to_upsert, on_conflict='nom').execute()
    print("Catégories insérées/mises à jour dans la base de données.")

    # --- 3. Importer les articles ---
    print("\n--- Étape 3: Importation des articles ---")
    
    # Récupérer les médias depuis Supabase
    media_response = supabase.table('medias').select('id, name').execute()
    if not media_response.data:
        print("Aucun média trouvé dans la base de données.")
        return
    
    # Créer un dictionnaire pour un accès rapide
    media_name_to_id = {m['name'].lower(): m['id'] for m in media_response.data}
    
    print(f"Médias dans la BD: {media_name_to_id}")
    
    # Récupérer les catégories pour mapper les noms aux IDs
    categories_response = supabase.table('categories').select('id, nom').execute()
    if not categories_response.data:
        print("Aucune catégorie trouvée dans la base de données.")
        return
    
    # Créer un dictionnaire pour un accès rapide
    category_name_to_id = {c['nom'].lower(): c['id'] for c in categories_response.data}

    articles_to_insert = []
    engagements_to_insert = []
    
    compteur_debug = {}  # Pour compter les articles par média
    
    for index, row in df.iterrows():
        # Normaliser le nom du média et trouver l'ID
        normalized_media_name = normalize_media_name(row['media'])
        
        if not normalized_media_name:
            print(f"Nom de média non reconnu : {row['media']}. Article ignoré.")
            continue

        media_id = media_name_to_id.get(normalized_media_name.lower())
        
        if not media_id:
            print(f"Aucun ID trouvé pour le média normalisé : '{normalized_media_name}' (original: '{row['media']}'). Article ignoré.")
            continue
        
        # Compter pour debug
        if normalized_media_name not in compteur_debug:
            compteur_debug[normalized_media_name] = 0
        compteur_debug[normalized_media_name] += 1
        
        # Gestion de la date
        try:
            publication_date = pd.to_datetime(row['date'], errors='coerce')
            if pd.isnull(publication_date):
                raise ValueError("Date invalide")
            
            # Assigner le fuseau horaire UTC si pas déjà fait
            if publication_date.tzinfo is None:
                publication_date = pytz.utc.localize(publication_date)
            
        except Exception as e:
            print(f"Erreur lors du traitement de la date pour l'article '{row['titre']}': {e}")
            continue

        # Trouver l'ID de la catégorie
        categorie_id = None
        if pd.notna(row['categorie']):
            categorie_id = category_name_to_id.get(row['categorie'].lower())

        # Préparer les données de l'article
        article_data = {
            'id': str(row['id']),  # Garder l'ID comme chaîne de caractères (slug)
            'media_id': media_id,
            'categorie_id': categorie_id,
            'titre': str(row['titre']) if pd.notna(row['titre']) else '',
            'contenu': str(row['contenu']) if pd.notna(row['contenu']) else '',
            'url': str(row['url']) if pd.notna(row['url']) else '',
            'date': publication_date.isoformat(),
            'created_at': datetime.now(pytz.utc).isoformat()
        }
        articles_to_insert.append(article_data)
        
        # Préparer les données d'engagement
        engagement_data = {
            'article_id': str(row['id']),  # Utiliser le même ID (slug)
            'likes': int(row['likes']) if pd.notna(row['likes']) else 0,
            'commentaires': int(row['commentaires']) if pd.notna(row['commentaires']) else 0,
            'partages': int(row['partages']) if pd.notna(row['partages']) else 0,
            'type_source': str(row['type_source']) if pd.notna(row['type_source']) else '',
            'plateforme': str(row['plateforme']) if pd.notna(row['plateforme']) else ''
        }
        engagements_to_insert.append(engagement_data)

    # Afficher le compteur pour debug
    print(f"\nArticles traités par média:")
    for media, count in compteur_debug.items():
        print(f"  {media}: {count} articles")
    
    # Supprimer les doublons basés sur l'ID
    seen_ids = set()
    articles_uniques = []
    engagements_uniques = []
    doublons = 0
    
    for i, article in enumerate(articles_to_insert):
        if article['id'] not in seen_ids:
            seen_ids.add(article['id'])
            articles_uniques.append(article)
            engagements_uniques.append(engagements_to_insert[i])
        else:
            doublons += 1
    
    if doublons > 0:
        print(f"\n⚠️  {doublons} doublons détectés et supprimés")
    
    articles_to_insert = articles_uniques
    engagements_to_insert = engagements_uniques
    
    # --- 4. Insérer les articles par lots ---
    if articles_to_insert:
        batch_size = 500
        total_records = len(articles_to_insert)
        print(f"\nInsertion de {total_records} articles dans la base de données...")
        for i in tqdm(range(0, total_records, batch_size), desc="Insertion des articles"):
            batch = articles_to_insert[i:i + batch_size]
            try:
                supabase.table('articles').upsert(batch, on_conflict='id').execute()
            except Exception as e:
                print(f"Erreur lors de l'insertion du lot {i//batch_size + 1} des articles: {e}")
    
    # --- 5. Insérer les engagements par lots ---
    if engagements_to_insert:
        batch_size = 500
        total_records = len(engagements_to_insert)
        print(f"\nInsertion de {total_records} engagements dans la base de données...")
        for i in tqdm(range(0, total_records, batch_size), desc="Insertion des engagements"):
            batch = engagements_to_insert[i:i + batch_size]
            try:
                supabase.table('engagements').upsert(batch, on_conflict='article_id').execute()
            except Exception as e:
                print(f"Erreur lors de l'insertion du lot {i//batch_size + 1} des engagements: {e}")

    print("\nImportation des articles et des engagements terminée.")

if __name__ == "__main__":
    import_data()
