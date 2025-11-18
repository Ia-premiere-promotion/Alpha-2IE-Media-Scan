import os
import time
from supabase import create_client, Client
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')

# Créer le client Supabase avec retry
def create_supabase_client_with_retry(max_retries=3):
    """Crée un client Supabase avec retry en cas d'erreur"""
    for attempt in range(max_retries):
        try:
            client = create_client(SUPABASE_URL, SUPABASE_KEY)
            # Test de connexion
            client.table('medias').select('id').limit(1).execute()
            return client
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠️ Tentative {attempt + 1}/{max_retries} échouée, retry dans 2s...")
                time.sleep(2)
            else:
                print(f"❌ Impossible de se connecter à Supabase après {max_retries} tentatives")
                raise e

supabase: Client = create_supabase_client_with_retry()

def get_supabase_client():
    """Retourne le client Supabase"""
    global supabase
    try:
        # Test si la connexion est toujours active
        supabase.table('medias').select('id').limit(1).execute()
        return supabase
    except:
        # Recréer le client si connexion perdue
        print("🔄 Reconnexion à Supabase...")
        supabase = create_supabase_client_with_retry()
        return supabase

