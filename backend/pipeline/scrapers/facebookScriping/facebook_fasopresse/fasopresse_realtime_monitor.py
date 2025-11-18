"""
Script de monitoring temps réel de la page Facebook Fasopresse
Détecte le dernier post et met à jour les métriques dans un JSON (pas de doublons)
"""

import json
import time
import os
from datetime import datetime
from dotenv import load_dotenv
from facebook_playwright_scraper import FacebookPlaywrightScraper

# Charger les variables d'environnement
load_dotenv()


class FasopresseRealtimeMonitor:
    """Moniteur temps réel pour Fasopresse avec export JSON"""
    
    def __init__(self, check_interval: int = 600):
        """
        Initialise le moniteur
        
        Args:
            check_interval: Intervalle de vérification en secondes (600s = 10min)
        """
        self.check_interval = check_interval
        self.json_filename = 'fasopresse_realtime.json'
        self.posts_dict = {}  # Dict pour accès rapide par post_id
        self.page_keywords = ['fasopresse', 'Fasopresse', 'p/Fasopresse']
        self.scraper = None
        self.is_logged_in = False
        
    def load_existing_data(self):
        """Charge les données existantes depuis le JSON"""
        if not os.path.exists(self.json_filename):
            print(f"📄 Nouveau fichier JSON à créer: {self.json_filename}")
            return
        
        try:
            with open(self.json_filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                posts = data.get('posts', [])
                for post in posts:
                    self.posts_dict[post['post_id']] = post
            print(f"📂 {len(self.posts_dict)} posts chargés depuis JSON")
        except Exception as e:
            print(f"⚠️ Erreur chargement JSON: {e}")
    
    def save_to_json(self):
        """Sauvegarde toutes les données dans le JSON"""
        try:
            # Trier par date (plus récent d'abord)
            sorted_posts = sorted(self.posts_dict.values(), 
                                key=lambda x: x['date_post'], 
                                reverse=True)
            
            # Calculer les statistiques
            total_engagement = sum(p['engagement_total'] for p in sorted_posts)
            total_likes = sum(p['likes'] for p in sorted_posts)
            total_comments = sum(p['comments'] for p in sorted_posts)
            total_shares = sum(p['shares'] for p in sorted_posts)
            
            output = {
                'posts': sorted_posts,
                'metadata': {
                    'total_posts': len(sorted_posts),
                    'last_update': datetime.now().isoformat(),
                    'total_engagement': total_engagement,
                    'total_likes': total_likes,
                    'total_comments': total_comments,
                    'total_shares': total_shares,
                    'page': 'Fasopresse',
                    'page_url': 'https://web.facebook.com/p/Fasopresse-Lactualit%C3%A9-du-Burkina-Faso-100067981629793/'
                }
            }
            
            with open(self.json_filename, 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            
            print(f"💾 {len(self.posts_dict)} posts sauvegardés dans {self.json_filename}")
        except Exception as e:
            print(f"❌ Erreur sauvegarde JSON: {e}")
    
    def check_and_update(self, email: str, password: str, page_url: str):
        """
        Vérifie le dernier post et met à jour les métriques de tous les posts
        """
        print(f"\n{'='*70}")
        print(f"🔍 VÉRIFICATION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}")
        
        # Initialiser le scraper si nécessaire
        if not self.scraper:
            self.scraper = FacebookPlaywrightScraper(headless=True, page_keywords=self.page_keywords)
        
        # Scraper la page (récupère 50 posts max)
        if not self.is_logged_in:
            print("🔐 Connexion initiale...")
        else:
            print("♻️ Réutilisation de la session existante...")
        
        posts = self.scraper.scrape_page(
            page_url=page_url,
            email=email,
            password=password,
            max_posts=50
        )
        
        if posts:
            self.is_logged_in = True
        
        if not posts:
            print("⚠️ Aucun post récupéré lors de cette vérification")
            return
        
        # Mise à jour des posts
        new_posts = 0
        updated_posts = 0
        
        for post in posts:
            post_id = post['post_id']
            
            if post_id not in self.posts_dict:
                # Nouveau post
                self.posts_dict[post_id] = post
                new_posts += 1
                print(f"🆕 Nouveau post détecté: {post_id[:30]}...")
            else:
                # Mise à jour des métriques
                old_post = self.posts_dict[post_id]
                if (post['likes'] != old_post['likes'] or 
                    post['comments'] != old_post['comments'] or 
                    post['shares'] != old_post['shares']):
                    self.posts_dict[post_id] = post
                    updated_posts += 1
        
        # Sauvegarder les changements
        if new_posts > 0 or updated_posts > 0:
            self.save_to_json()
            print(f"✅ {new_posts} nouveaux posts, {updated_posts} posts mis à jour")
        else:
            print("ℹ️ Aucun changement détecté")
    
    def run_continuous(self, email: str, password: str, page_url: str):
        """
        Lance le monitoring en continu
        """
        print("\n" + "="*70)
        print("🚀 DÉMARRAGE DU MONITORING FASOPRESSE")
        print("="*70)
        print(f"📊 Fichier de données: {self.json_filename}")
        print(f"⏱️ Intervalle de vérification: {self.check_interval}s ({self.check_interval//60}min)")
        print(f"🌐 Page: {page_url}")
        print(f"🔑 Mots-clés de validation: {', '.join(self.page_keywords)}")
        print("="*70)
        
        # Charger les données existantes
        self.load_existing_data()
        
        try:
            iteration = 0
            while True:
                iteration += 1
                print(f"\n🔄 ITÉRATION #{iteration}")
                
                # Vérifier et mettre à jour
                try:
                    self.check_and_update(email, password, page_url)
                except Exception as e:
                    print(f"❌ Erreur lors de la vérification: {e}")
                    # Réinitialiser le scraper en cas d'erreur
                    if self.scraper:
                        self.scraper.close()
                        self.scraper = None
                        self.is_logged_in = False
                
                # Attendre avant la prochaine vérification
                print(f"\n⏳ Prochaine vérification dans {self.check_interval}s...")
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            print("\n\n⛔ Arrêt du monitoring demandé par l'utilisateur")
            if self.scraper:
                self.scraper.close()
            print("👋 Au revoir !")


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
    
    # URL de la page Fasopresse
    page_url = "https://web.facebook.com/p/Fasopresse-Lactualit%C3%A9-du-Burkina-Faso-100067981629793/"
    
    # Créer et lancer le moniteur
    monitor = FasopresseRealtimeMonitor(check_interval=600)  # 10 minutes
    monitor.run_continuous(email, password, page_url)


if __name__ == "__main__":
    main()
