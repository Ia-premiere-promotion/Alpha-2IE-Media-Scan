"""
Script de monitoring temps réel de la page Facebook ESidwaya
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


class ESidwayaRealtimeMonitor:
    """Moniteur temps réel pour ESidwaya avec export JSON"""
    
    def __init__(self, check_interval: int = 600):
        """
        Initialise le moniteur
        
        Args:
            check_interval: Intervalle de vérification en secondes (600s = 10min)
        """
        self.check_interval = check_interval
        self.json_filename = 'esidwaya_realtime.json'
        self.posts_dict = {}  # Dict pour accès rapide par post_id
        self.page_keywords = ['ESidwaya', 'sidwaya', '100064709527661']
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
                    'page': 'ESidwaya',
                    'page_url': 'https://web.facebook.com/ESidwaya'
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
            print("♻️ Réutilisation de la session...")
        
        self.scraper.scrape_page(page_url, email, password, max_posts=50)
        self.is_logged_in = True
        
        if not self.scraper.posts_data:
            print("⚠️ Aucun post récupéré")
            return
        
        # Détecter le dernier post (le plus récent)
        latest_post = self.scraper.posts_data[0]  # Le premier est le plus récent
        
        # Statistiques
        new_posts = 0
        updated_posts = 0
        
        # Traiter tous les posts scrapés
        for post in self.scraper.posts_data:
            post_id = post['post_id']
            
            if post_id not in self.posts_dict:
                # Nouveau post détecté
                self.posts_dict[post_id] = {
                    'post_id': post_id,
                    'url': post['url'],
                    'date_post': post['date_post'],
                    'contenu': post['contenu'],
                    'likes': post['likes'],
                    'comments': post['comments'],
                    'shares': post['shares'],
                    'engagement_total': post['engagement_total'],
                    'commentaires': post.get('commentaires', []),
                    'last_update': datetime.now().isoformat()
                }
                new_posts += 1
                
                print(f"\n🆕 NOUVEAU POST détecté:")
                print(f"   📝 {post['contenu'][:100]}...")
                print(f"   👍 {post['likes']} likes | 💬 {post['comments']} comments | 🔄 {post['shares']} shares")
            
            else:
                # Post existant - vérifier si les métriques ont changé
                old_post = self.posts_dict[post_id]
                
                if (old_post['likes'] != post['likes'] or 
                    old_post['comments'] != post['comments'] or 
                    old_post['shares'] != post['shares']):
                    
                    # Mise à jour
                    old_engagement = old_post['engagement_total']
                    new_engagement = post['engagement_total']
                    
                    self.posts_dict[post_id].update({
                        'likes': post['likes'],
                        'comments': post['comments'],
                        'shares': post['shares'],
                        'engagement_total': post['engagement_total'],
                        'commentaires': post.get('commentaires', []),
                        'last_update': datetime.now().isoformat()
                    })
                    updated_posts += 1
                    
                    print(f"\n🔄 POST MIS À JOUR:")
                    print(f"   📝 {post['contenu'][:60]}...")
                    print(f"   👍 {old_post['likes']} → {post['likes']} (+{post['likes'] - old_post['likes']})")
                    print(f"   💬 {old_post['comments']} → {post['comments']} (+{post['comments'] - old_post['comments']})")
                    print(f"   🔄 {old_post['shares']} → {post['shares']} (+{post['shares'] - old_post['shares']})")
                    print(f"   📊 Engagement: {old_engagement} → {new_engagement}")
        
        # Sauvegarder dans le JSON
        self.save_to_json()
        
        # Résumé
        print(f"\n{'='*70}")
        print(f"📊 RÉSUMÉ:")
        print(f"   🆕 Nouveaux posts: {new_posts}")
        print(f"   🔄 Posts mis à jour: {updated_posts}")
        print(f"   📁 Total posts suivis: {len(self.posts_dict)}")
        
        # Info sur le dernier post
        if latest_post['post_id'] in self.posts_dict:
            latest = self.posts_dict[latest_post['post_id']]
            print(f"\n🎯 DERNIER POST:")
            print(f"   📝 {latest['contenu'][:100]}...")
            print(f"   👍 {latest['likes']} | 💬 {latest['comments']} | 🔄 {latest['shares']} = 📊 {latest['engagement_total']}")
        
        print(f"{'='*70}\n")
    
    def start_monitoring(self, email: str, password: str, page_url: str):
        """
        Lance le monitoring en temps réel
        """
        print("=" * 70)
        print("🚀 DÉMARRAGE DU MONITORING TEMPS RÉEL - ESIDWAYA")
        print("=" * 70)
        print(f"📍 Page: {page_url}")
        print(f"⏱️ Intervalle: {self.check_interval}s ({self.check_interval//60} min)")
        print(f"💾 Fichier JSON: {self.json_filename}")
        print("=" * 70)
        
        # Charger les données existantes
        self.load_existing_data()
        
        # Première vérification immédiate
        print("\n🔍 Première vérification...")
        self.check_and_update(email, password, page_url)
        
        # Boucle de monitoring
        try:
            iteration = 1
            while True:
                print(f"\n⏳ Prochaine vérification dans {self.check_interval}s...")
                print(f"   (Ctrl+C pour arrêter)")
                time.sleep(self.check_interval)
                
                iteration += 1
                print(f"\n📅 Itération #{iteration}")
                self.check_and_update(email, password, page_url)
                
        except KeyboardInterrupt:
            print("\n\n⏹️ Arrêt du monitoring...")
            print(f"💾 Dernière sauvegarde...")
            self.save_to_json()
            print("✅ Monitoring arrêté proprement")


def main():
    """Fonction principale"""
    # Configuration
    email = os.getenv('FB_EMAIL')
    password = os.getenv('FB_PASSWORD')
    page_url = 'https://web.facebook.com/ESidwaya'
    check_interval = int(os.getenv('CHECK_INTERVAL', '600'))  # 10 minutes par défaut
    
    if not email or not password:
        print("❌ Erreur: Identifiants manquants dans le fichier .env")
        return
    
    # Créer et lancer le moniteur
    monitor = ESidwayaRealtimeMonitor(check_interval=check_interval)
    monitor.start_monitoring(email, password, page_url)


if __name__ == "__main__":
    main()
