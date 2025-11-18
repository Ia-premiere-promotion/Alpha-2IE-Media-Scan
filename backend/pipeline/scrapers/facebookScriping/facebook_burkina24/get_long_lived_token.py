"""
Utilitaire pour convertir un token Facebook court en token longue durée
"""

import requests
import sys


def exchange_token(app_id: str, app_secret: str, short_token: str) -> dict:
    """
    Échange un token court contre un token longue durée (60 jours)
    
    Args:
        app_id: ID de votre application Facebook
        app_secret: Secret de votre application Facebook
        short_token: Token d'accès court obtenu depuis Graph API Explorer
        
    Returns:
        Dict contenant le nouveau token et sa date d'expiration
    """
    url = "https://graph.facebook.com/v18.0/oauth/access_token"
    
    params = {
        'grant_type': 'fb_exchange_token',
        'client_id': app_id,
        'client_secret': app_secret,
        'fb_exchange_token': short_token
    }
    
    try:
        print("🔄 Échange du token en cours...")
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if 'access_token' in data:
            print("✅ Token longue durée obtenu avec succès !")
            print(f"\n📝 Nouveau token (valide ~60 jours):")
            print(f"{data['access_token']}\n")
            
            if 'expires_in' in data:
                days = data['expires_in'] / 86400
                print(f"⏰ Expire dans: {days:.0f} jours")
            
            # Sauvegarder dans un fichier
            with open('long_lived_token.txt', 'w') as f:
                f.write(data['access_token'])
            print(f"\n💾 Token sauvegardé dans: long_lived_token.txt")
            
            return data
        else:
            print(f"❌ Erreur: {data}")
            return {}
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de requête: {e}")
        if hasattr(e.response, 'text'):
            print(f"Détails: {e.response.text}")
        return {}


def get_page_access_token(user_token: str, page_id: str) -> str:
    """
    Obtient un token d'accès permanent pour une page (ne expire jamais)
    
    Args:
        user_token: Token utilisateur longue durée
        page_id: ID de la page Facebook
        
    Returns:
        Token d'accès permanent de la page
    """
    url = f"https://graph.facebook.com/v18.0/{page_id}"
    
    params = {
        'fields': 'access_token',
        'access_token': user_token
    }
    
    try:
        print(f"\n🔄 Récupération du token permanent pour la page {page_id}...")
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if 'access_token' in data:
            page_token = data['access_token']
            print("✅ Token permanent de page obtenu !")
            print(f"\n📝 Token de page (ne expire jamais):")
            print(f"{page_token}\n")
            
            # Sauvegarder
            with open('page_access_token.txt', 'w') as f:
                f.write(page_token)
            print(f"💾 Token de page sauvegardé dans: page_access_token.txt")
            
            return page_token
        else:
            print(f"❌ Erreur: {data}")
            return ""
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur: {e}")
        if hasattr(e.response, 'text'):
            print(f"Détails: {e.response.text}")
        return ""


def verify_token(token: str) -> dict:
    """
    Vérifie les informations d'un token
    
    Args:
        token: Token à vérifier
        
    Returns:
        Informations sur le token
    """
    url = "https://graph.facebook.com/v18.0/debug_token"
    
    params = {
        'input_token': token,
        'access_token': token  # Utilise le même token pour se vérifier
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'data' in data:
            info = data['data']
            print("\n🔍 Informations du token:")
            print(f"  - App ID: {info.get('app_id')}")
            print(f"  - Type: {info.get('type')}")
            print(f"  - Valide: {info.get('is_valid')}")
            
            if 'expires_at' in info and info['expires_at'] != 0:
                from datetime import datetime
                expiry = datetime.fromtimestamp(info['expires_at'])
                print(f"  - Expire le: {expiry.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print(f"  - Expire: Jamais (token permanent)")
            
            if 'scopes' in info:
                print(f"  - Permissions: {', '.join(info['scopes'])}")
        
        return data
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return {}


def main():
    """Fonction principale interactive"""
    
    print("=" * 60)
    print("🔑 GÉNÉRATEUR DE TOKEN FACEBOOK LONGUE DURÉE")
    print("=" * 60)
    
    print("\n📋 ÉTAPE 1: Informations de votre application")
    print("Trouvez ces infos sur: https://developers.facebook.com/apps/\n")
    
    app_id = input("App ID: ").strip()
    app_secret = input("App Secret: ").strip()
    
    print("\n📋 ÉTAPE 2: Token court")
    print("Obtenez-le sur: https://developers.facebook.com/tools/explorer/")
    print("Permissions nécessaires: pages_read_engagement, pages_show_list\n")
    
    short_token = input("Token court: ").strip()
    
    # Échange pour token longue durée
    result = exchange_token(app_id, app_secret, short_token)
    
    if not result or 'access_token' not in result:
        print("\n❌ Impossible d'obtenir le token longue durée")
        sys.exit(1)
    
    long_token = result['access_token']
    
    # Demander si l'utilisateur veut un token de page
    print("\n" + "=" * 60)
    get_page_token = input("\n❓ Voulez-vous aussi obtenir un token de PAGE permanent (ne expire jamais)? (o/n): ").strip().lower()
    
    if get_page_token == 'o':
        page_id = input("\nID de la page (ex: lobspaalgaBF): ").strip()
        page_token = get_page_access_token(long_token, page_id)
        
        if page_token:
            verify_token(page_token)
            print(f"\n🎯 Utilisez ce token de page dans facebook_scraper.py")
            print(f"   Il ne expirera JAMAIS !")
    else:
        verify_token(long_token)
        print(f"\n🎯 Utilisez ce token utilisateur dans facebook_scraper.py")
        print(f"   Valide pendant ~60 jours")
    
    print("\n" + "=" * 60)
    print("✅ TERMINÉ !")
    print("=" * 60)


if __name__ == "__main__":
    main()
