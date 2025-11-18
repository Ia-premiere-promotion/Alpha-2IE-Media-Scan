#!/usr/bin/env python3
"""
Script pour ajouter la colonne created_at à la table users
"""
from supabase_client import get_supabase_client

def fix_users_table():
    """Ajoute la colonne created_at à la table users"""
    try:
        supabase = get_supabase_client()
        
        print("🔧 Ajout de la colonne created_at à la table users...")
        
        # Lire le fichier SQL
        with open('fix_users_created_at.sql', 'r', encoding='utf-8') as f:
            sql_commands = f.read()
        
        print(f"\n📝 Commandes SQL à exécuter:\n{sql_commands}\n")
        
        # Exécuter les commandes SQL
        # Note: Supabase Python client n'a pas de méthode directe pour exécuter du SQL brut
        # Il faut le faire via l'interface Supabase ou psycopg2
        
        print("⚠️  IMPORTANT:")
        print("Connectez-vous à votre dashboard Supabase et exécutez ces commandes SQL:")
        print("1. Allez sur https://supabase.com/dashboard")
        print("2. Sélectionnez votre projet")
        print("3. Allez dans 'SQL Editor'")
        print("4. Collez et exécutez les commandes ci-dessus")
        print("\nOU utilisez psycopg2 pour exécuter directement le SQL.")
        
        # Vérifier la structure actuelle de la table
        print("\n🔍 Vérification de la structure actuelle...")
        response = supabase.table('users').select('*').limit(1).execute()
        
        if response.data and len(response.data) > 0:
            print("\n✅ Colonnes actuelles dans users:")
            for key in response.data[0].keys():
                print(f"   - {key}")
        else:
            print("⚠️  Aucun utilisateur trouvé pour vérifier la structure")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        return False
    
    return True

if __name__ == '__main__':
    print("=" * 60)
    print("FIX: Ajout de created_at à la table users")
    print("=" * 60)
    print()
    
    fix_users_table()
