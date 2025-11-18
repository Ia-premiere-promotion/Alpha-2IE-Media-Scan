"""
Script pour scraper une seule fois la page Facebook Lefaso.net
Utilise facebook_playwright_scraper.py
"""

import os
from dotenv import load_dotenv
from facebook_playwright_scraper import FacebookPlaywrightScraper
import json
from datetime import datetime

# Charger les variables d'environnement
load_dotenv()


def main():
    """Fonction principale pour scraper Lefaso.net"""
    
    print("=" * 70)
    print("🔍 SCRAPING UNIQUE - Lefaso.net")
    print("=" * 70)
    
    # Configuration
    email = os.getenv('FB_EMAIL')
    password = os.getenv('FB_PASSWORD')
    # URL de la page Lefaso.net
    page_url = 'https://web.facebook.com/lefaso.net'
    
    if not email or not password:
        print("❌ Erreur: Identifiants manquants dans le fichier .env")
        print("   Créez un fichier .env avec:")
        print("   FB_EMAIL=votre_email@example.com")
        print("   FB_PASSWORD=votre_mot_de_passe")
        return
    
    print(f"📍 Page à scraper: {page_url}")
    print(f"📧 Email: {email[:3]}***{email.split('@')[1] if '@' in email else ''}")
    print(f"🎯 Posts à récupérer: 50 maximum")
    print("=" * 70)
    
    # Créer le scraper avec les keywords pour Lefaso.net
    page_keywords = ['lefaso.net', 'lefaso', 'Le Faso']
    scraper = FacebookPlaywrightScraper(headless=True, page_keywords=page_keywords)
    
    # Scraper la page
    print("\n🚀 Démarrage du scraping...")
    scraper.scrape_page(
        page_url=page_url,
        email=email,
        password=password,
        max_posts=50  # Augmenter pour avoir plus de posts
    )
    
    # Sauvegarder les résultats
    if scraper.posts_data:
        output_file = 'lefaso_posts.json'
        
        output = {
            'posts': scraper.posts_data,
            'metadata': {
                'total_posts': len(scraper.posts_data),
                'scraped_at': datetime.now().isoformat(),
                'total_engagement': sum(p['engagement_total'] for p in scraper.posts_data),
                'page': 'Lefaso.net',
                'page_url': page_url
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"\n{'=' * 70}")
        print("✅ SCRAPING TERMINÉ !")
        print(f"{'=' * 70}")
        print(f"📊 Posts collectés: {len(scraper.posts_data)}")
        print(f"💾 Fichier de sortie: {output_file}")
        print(f"\n📈 STATISTIQUES:")
        print(f"   Total engagement: {sum(p['engagement_total'] for p in scraper.posts_data)}")
        print(f"   Total likes: {sum(p['likes'] for p in scraper.posts_data)}")
        print(f"   Total commentaires: {sum(p['comments'] for p in scraper.posts_data)}")
        print(f"   Total partages: {sum(p['shares'] for p in scraper.posts_data)}")
        
        # Afficher les 3 posts avec le plus d'engagement
        sorted_posts = sorted(scraper.posts_data, key=lambda x: x['engagement_total'], reverse=True)
        print(f"\n🏆 TOP 3 POSTS PAR ENGAGEMENT:")
        for i, post in enumerate(sorted_posts[:3], 1):
            print(f"\n   {i}. {post['contenu'][:80]}...")
            print(f"      👍 {post['likes']} | 💬 {post['comments']} | 🔄 {post['shares']} = 📊 {post['engagement_total']}")
        
        print(f"\n{'=' * 70}")
    else:
        print("\n❌ Aucun post collecté")


if __name__ == "__main__":
    main()
