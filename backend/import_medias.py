import os
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv
import numpy as np
import re

# Charger les variables d'environnement du fichier .env
load_dotenv()

# Configuration de Supabase
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in your .env file.")

supabase: Client = create_client(url, key)

# Chemin vers le fichier CSV
file_path = '/home/bakouan/Bureau/APP MEDIA SCAN/backend/info_medias_page_facebook.csv'

def clean_data(df):
    """Nettoie et prépare le DataFrame pour l'insertion."""
    
    # Renommer les colonnes pour correspondre à la table 'medias'
    column_mapping = {
        'pageName': 'page_name',
        'facebookId': 'facebook_id',
        'followers': 'followers',
        'email': 'email',
        'phone': 'phone',
        'website': 'website',
        'rating': 'rating',
        'ratingCount': 'rating_count',
        'address': 'address',
        'profilePictureUrl': 'profile_photo_url',
        'facebookUrl': 'facebook_url',
        'intro': 'intro',
        'creation_date': 'creation_date'
    }
    df.rename(columns=column_mapping, inplace=True)

    # Utiliser 'page_name' pour la colonne 'name' unique
    if 'page_name' in df.columns:
        df['name'] = df['page_name']
    else:
        raise ValueError("La colonne 'pageName' (renommée en 'page_name') est essentielle et est manquante.")

    # Définir le type de média
    df['type'] = 'social_media'

    # Nettoyage et conversion explicite des types pour les colonnes numériques
    if 'followers' in df.columns:
        df['followers'] = pd.to_numeric(df['followers'], errors='coerce').fillna(0).astype(int)
        
    if 'rating_count' in df.columns:
        df['rating_count'] = pd.to_numeric(df['rating_count'], errors='coerce').fillna(0).astype(int)

    if 'creation_date' in df.columns:
        df['creation_date'] = pd.to_datetime(df['creation_date'], errors='coerce').dt.strftime('%Y-%m-%d')

    if 'rating' in df.columns:
        # Extrait le nombre de la chaîne (ex: "96% recommend (25 Reviews)" -> 96)
        df['rating'] = df['rating'].astype(str).str.extract(r'(\d+)').astype(float).fillna(0)

    # Remplacer les NaN de pandas par None (qui devient NULL en SQL)
    df = df.replace({np.nan: None})

    # Ajout des couleurs de manière cyclique
    colors = [
        '#ef4444', '#f97316', '#f59e0b', '#eab308', '#84cc16', '#22c55e',
        '#10b981', '#14b8a6', '#06b6d4', '#0ea5e9', '#3b82f6', '#6366f1',
        '#8b5cf6', '#a855f7', '#d946ef', '#ec4899', '#f43f5e'
    ]
    if not df.empty:
        df['couleur'] = [colors[i % len(colors)] for i in range(len(df))]

    return df

def import_medias():
    """Lit le CSV et insère/met à jour les données dans la table medias."""
    try:
        df = pd.read_csv(file_path)
        print("Fichier CSV lu avec succès.")
    except FileNotFoundError:
        print(f"Erreur : Le fichier {file_path} n'a pas été trouvé.")
        return
    except Exception as e:
        print(f"Une erreur est survenue lors de la lecture du CSV : {e}")
        return

    df_cleaned = clean_data(df)
    
    # Colonnes à insérer
    columns_to_insert = [
        'name', 'page_name', 'facebook_id', 'followers', 'email', 'phone', 
        'website', 'rating', 'rating_count', 'address', 'profile_photo_url', 
        'facebook_url', 'intro', 'creation_date', 'type', 'couleur'
    ]
    
    # Filtrer le DataFrame pour ne garder que les colonnes existantes
    db_columns = [
        'name', 'type', 'couleur', 'icon', 'is_active',
        'facebook_id', 'followers', 'email', 'phone', 'website', 'rating',
        'rating_count', 'address', 'profile_photo_url', 'facebook_url',
        'intro', 'page_name', 'creation_date'
    ]

    # Garder uniquement les colonnes du DataFrame qui existent dans la table de la BDD
    columns_to_keep = [col for col in df_cleaned.columns if col in db_columns]
    df_final = df_cleaned[columns_to_keep]

    # Convertir le DataFrame final en une liste de dictionnaires
    records = df_final.to_dict(orient='records')
    
    print(f"Début de l'importation de {len(records)} médias...")

    # Utiliser 'upsert' pour insérer ou mettre à jour les enregistrements
    # 'on_conflict' se base sur la colonne 'name' qui a une contrainte UNIQUE
    response = supabase.table('medias').upsert(records, on_conflict='name').execute()

    if response.data:
        print(f"{len(response.data)} enregistrements ont été traités avec succès.")
    else:
        print("Aucun enregistrement n'a été traité. Vérifiez les erreurs possibles.")
        # En cas d'erreur, Supabase peut ne pas renvoyer de données mais une erreur.
        # La bibliothèque python-supabase lèvera une exception pour les erreurs HTTP.

    print("Importation terminée.")

if __name__ == "__main__":
    import_medias()
