"""
Script de scraping unique pour la page Facebook Fasopresse
Récupère les posts et les sauvegarde dans un fichier JSON
"""

import json
import os
from datetime import datetime
from dotenv import load_dotenv
from facebook_playwright_scraper import FacebookPlaywrightScraper

# Charger les variables d'environnement
load_dotenv()


def scrape_fasopresse_once(email: str, password: str, max_posts: int = 50):
    """
    Effectue un scraping unique de la page Fasopresse
    
    Args:
        email: Email Facebook
        password: Mot de passe Facebook
        max_posts: Nombre maximum de posts à récupérer
    """
    print("\n" + "="*70)
    print("🚀 SCRAPING FASOPRESSE - EXÉCUTION UNIQUE")
    print("="*70)
    
    # URL de la page Fasopresse
    page_url = "https://web.facebook.com/p/Fasopresse-Lactualit%C3%A9-du-Burkina-Faso-100067981629793/"
    
    # Mots-clés pour valider les URLs
    page_keywords = ['fasopresse', 'Fasopresse', 'p/Fasopresse']
    
    # Créer le scraper
    scraper = FacebookPlaywrightScraper(headless=False, page_keywords=page_keywords)
    
    print(f"🌐 Page cible: {page_url}")
    print(f"📊 Posts max: {max_posts}")
    print(f"🔑 Mots-clés: {', '.join(page_keywords)}")
    print("="*70 + "\n")
    
    # Scraper la page
    posts = scraper.scrape_page(
        page_url=page_url,
        email=email,
        password=password,
        max_posts=max_posts
    )
    
    if not posts:
        print("\n❌ Aucun post récupéré")
        return
    
    # Calculer les statistiques
    total_engagement = sum(p['engagement_total'] for p in posts)
    total_likes = sum(p['likes'] for p in posts)
    total_comments = sum(p['comments'] for p in posts)
    total_shares = sum(p['shares'] for p in posts)
    
    # Préparer les données
    output = {
        'posts': posts,
        'metadata': {
            'total_posts': len(posts),
            'scrape_date': datetime.now().isoformat(),
            'total_engagement': total_engagement,
            'total_likes': total_likes,
            'total_comments': total_comments,
            'total_shares': total_shares,
            'page': 'Fasopresse',
            'page_url': page_url
        }
    }
    
    # Sauvegarder dans un fichier JSON
    filename = 'fasopresse_posts.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*70}")
    print(f"✅ SCRAPING TERMINÉ")
    print(f"{'='*70}")
    print(f"📁 Fichier: {filename}")
    print(f"📊 Posts récupérés: {len(posts)}")
    print(f"💬 Engagement total: {total_engagement:,}")
    print(f"  👍 Likes: {total_likes:,}")
    print(f"  💬 Commentaires: {total_comments:,}")
    print(f"  🔄 Partages: {total_shares:,}")
    print(f"{'='*70}\n")
    
    # Pas besoin de fermer le scraper, il se ferme automatiquement après scrape_page


def main():
    """Point d'entrée principal"""
    # Récupérer les credentials depuis les variables d'environnement
    email = os.getenv('FACEBOOK_EMAIL')
    password = os.getenv('FACEBOOK_PASSWORD')
    
    if not email or not password:
        print("❌ ERREUR: Variables d'environnement manquantes!")
        print("Créez un fichier .env avec:")
        print("FACEBOOK_EMAIL=votre_email")
        print("FACEBOOK_PASSWORD=votre_mot_de_passe")
        return
    
    # Lancer le scraping
    scrape_fasopresse_once(
        email=email,
        password=password,
        max_posts=50
    )


if __name__ == "__main__":
    main()
