#!/usr/bin/env python3
"""
Script pour exécuter la migration de la base de données
et générer les alertes
"""

import os
import sys
from dotenv import load_dotenv

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase_client import get_supabase_client

def run_migration():
    """Exécute la migration SQL pour ajouter les colonnes déontologiques"""
    print("🔄 Exécution de la migration...")
    
    # Lire le fichier SQL
    sql_file = os.path.join(os.path.dirname(__file__), 'add_deontology_columns.sql')
    with open(sql_file, 'r') as f:
        sql = f.read()
    
    # Connexion à Supabase
    supabase = get_supabase_client()
    
    try:
        # Exécuter le SQL via RPC (nécessite une fonction dans Supabase)
        # Alternative: utiliser psycopg2 directement
        print("✅ Migration SQL à exécuter manuellement dans Supabase Dashboard")
        print("\nSQL à exécuter:")
        print("=" * 80)
        print(sql)
        print("=" * 80)
        print("\nAllez dans Supabase Dashboard > SQL Editor et exécutez ce code")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    return True

def generate_test_alerts():
    """Génère des alertes de test"""
    print("\n🔄 Génération des alertes...")
    
    from utils.alert_generator import AlertGenerator
    from supabase_client import get_supabase_client
    
    supabase = get_supabase_client()
    generator = AlertGenerator(supabase)
    
    try:
        # Récupérer tous les médias actifs
        medias_response = supabase.table('medias')\
            .select('id, name, regularite')\
            .eq('is_active', True)\
            .execute()
        
        if not medias_response.data:
            print("⚠️  Aucun média actif trouvé")
            return
        
        total_alerts = 0
        for media in medias_response.data:
            print(f"\n→ Vérification: {media['name']}")
            alerts = generator.generate_alerts_for_media(media)
            
            for alert in alerts:
                saved = generator.save_alert(alert)
                if saved:
                    total_alerts += 1
        
        print(f"\n✅ {total_alerts} nouvelles alertes générées")
        
    except Exception as e:
        print(f"❌ Erreur génération alertes: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    load_dotenv()
    
    print("=" * 80)
    print("MIGRATION ET GÉNÉRATION D'ALERTES")
    print("=" * 80)
    
    # Migration
    run_migration()
    
    # Générer les alertes
    input("\nAppuyez sur Entrée après avoir exécuté la migration SQL...")
    generate_test_alerts()
