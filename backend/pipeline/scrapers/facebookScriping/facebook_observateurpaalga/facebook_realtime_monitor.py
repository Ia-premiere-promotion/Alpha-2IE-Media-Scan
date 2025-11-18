"""
Script de monitoring temps réel de la page Facebook Observateur Paalga
Vérifie les nouveaux posts toutes les 10 minutes
"""

from playwright.sync_api import sync_playwright
import json
import time
import os
from datetime import datetime
from dotenv import load_dotenv
from facebook_playwright_scraper import FacebookPlaywrightScraper

# Charger les variables d'environnement
load_dotenv()


class FacebookRealtimeMonitor:
    """Moniteur temps réel pour détecter les nouveaux posts"""
    
    def __init__(self, check_interval: int = 600):
        """
        Initialise le moniteur
        
        Args:
            check_interval: Intervalle de vérification en secondes (600s = 10min)
        """
        self.check_interval = check_interval
        self.seen_post_ids = set()
        self.all_posts = []
        self.scraper = None
        self.browser = None
        self.context = None
        self.page = None
        self.is_logged_in = False
        
    def load_existing_posts(self, filename: str = 'observateur_paalga_stream.json'):
        """Charge les posts déjà enregistrés"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.all_posts = data.get('posts', [])
                    self.seen_post_ids = {p['post_id'] for p in self.all_posts}
                    print(f"📂 {len(self.all_posts)} posts existants chargés")
        except Exception as e:
            print(f"⚠️ Erreur chargement: {e}")
    
    def save_posts(self, filename: str = 'observateur_paalga_stream.json'):
        """Sauvegarde tous les posts collectés"""
        output = {
            'posts': self.all_posts,
            'metadata': {
                'total_posts': len(self.all_posts),
                'last_update': datetime.now().isoformat(),
                'total_engagement': sum(p['engagement_total'] for p in self.all_posts),
                'monitoring_started': self.all_posts[0]['date_post'] if self.all_posts else None
            }
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"💾 {len(self.all_posts)} posts sauvegardés dans {filename}")
    
    def update_existing_posts(self, email: str, password: str, page_url: str) -> int:
        """
        Met à jour les métriques de tous les posts existants
        
        Returns:
            Nombre de posts mis à jour
        """
        if not self.all_posts:
            return 0
        
        print(f"🔄 Mise à jour des métriques de {len(self.all_posts)} post(s) existant(s)...")
        
        # Utiliser le scraper avec session persistante
        if not self.scraper:
            self.scraper = FacebookPlaywrightScraper(headless=True)
        
        # Vérifier si on est connecté
        if not self.is_logged_in:
            print("🔐 Connexion initiale...")
            self.scraper.scrape_page(page_url, email, password, max_posts=50)
            self.is_logged_in = True
        else:
            # Réutiliser la session existante
            print("♻️ Réutilisation de la session existante...")
            self.scraper.scrape_page(page_url, email, password, max_posts=50)
        
        # Créer un dictionnaire des posts fraîchement scrapés
        fresh_posts = {post['post_id']: post for post in self.scraper.posts_data}
        
        updated_count = 0
        
        # Mettre à jour chaque post existant
        for i, old_post in enumerate(self.all_posts):
            post_id = old_post['post_id']
            
            if post_id in fresh_posts:
                fresh_post = fresh_posts[post_id]
                
                # Vérifier si les métriques ont changé
                old_engagement = old_post['engagement_total']
                new_engagement = fresh_post['engagement_total']
                
                if new_engagement != old_engagement:
                    # Mettre à jour les métriques
                    old_likes = old_post['likes']
                    old_comments = old_post['comments']
                    old_shares = old_post['shares']
                    
                    self.all_posts[i]['likes'] = fresh_post['likes']
                    self.all_posts[i]['comments'] = fresh_post['comments']
                    self.all_posts[i]['shares'] = fresh_post['shares']
                    self.all_posts[i]['engagement_total'] = fresh_post['engagement_total']
                    
                    # Mettre à jour les commentaires
                    if len(fresh_post['commentaires']) > len(old_post['commentaires']):
                        self.all_posts[i]['commentaires'] = fresh_post['commentaires']
                    
                    # Ajouter un champ de dernière mise à jour
                    self.all_posts[i]['last_updated'] = datetime.now().isoformat()
                    
                    updated_count += 1
                    
                    print(f"   ✅ Post {post_id[:20]}... mis à jour:")
                    print(f"      👍 {old_likes} → {fresh_post['likes']} likes")
                    print(f"      💬 {old_comments} → {fresh_post['comments']} commentaires")
                    print(f"      🔄 {old_shares} → {fresh_post['shares']} partages")
        
        if updated_count > 0:
            print(f"✅ {updated_count} post(s) mis à jour !")
        else:
            print(f"✅ Aucune modification détectée")
        
        return updated_count
    
    def check_new_posts(self, email: str, password: str, page_url: str) -> list:
        """
        Vérifie s'il y a de nouveaux posts
        
        Returns:
            Liste des nouveaux posts détectés
        """
        print(f"\n🔍 Vérification de nouveaux posts... ({datetime.now().strftime('%H:%M:%S')})")
        
        # Utiliser le scraper avec session persistante
        if not self.scraper:
            self.scraper = FacebookPlaywrightScraper(headless=True)
        
        # Vérifier si on est connecté
        if not self.is_logged_in:
            print("🔐 Connexion initiale...")
            self.scraper.scrape_page(page_url, email, password, max_posts=10)
            self.is_logged_in = True
        else:
            # Réutiliser la session existante
            print("♻️ Réutilisation de la session...")
            self.scraper.scrape_page(page_url, email, password, max_posts=10)
        
        # Détecter les nouveaux posts
        new_posts = []
        for post in self.scraper.posts_data:
            if post['post_id'] not in self.seen_post_ids:
                new_posts.append(post)
                self.seen_post_ids.add(post['post_id'])
                self.all_posts.insert(0, post)  # Ajouter au début
        
        return new_posts
    
    def start_monitoring(self, email: str, password: str, page_url: str, output_file: str = 'observateur_paalga_stream.json'):
        """
        Démarre le monitoring en temps réel
        
        Args:
            email: Email Facebook
            password: Mot de passe
            page_url: URL de la page à monitorer
            output_file: Fichier de sortie JSON
        """
        print("=" * 70)
        print("🔴 MONITORING TEMPS RÉEL - Observateur Paalga")
        print("=" * 70)
        print(f"📍 Page: {page_url}")
        print(f"⏱️  Intervalle: {self.check_interval // 60} minutes")
        print(f"💾 Fichier: {output_file}")
        print("=" * 70)
        
        # Charger les posts existants
        self.load_existing_posts(output_file)
        
        # Première vérification immédiate
        print("\n🚀 Première vérification immédiate...")
        
        # Mettre à jour les posts existants
        if self.all_posts:
            updated = self.update_existing_posts(email, password, page_url)
        
        # Vérifier les nouveaux posts
        new_posts = self.check_new_posts(email, password, page_url)
        
        if new_posts:
            print(f"\n🆕 {len(new_posts)} nouveau(x) post(s) détecté(s) !")
            for post in new_posts:
                print(f"   📝 {post['contenu'][:60]}...")
                print(f"   👍 {post['likes']} likes | 💬 {post['comments']} commentaires | 🔄 {post['shares']} partages")
        else:
            print("✅ Aucun nouveau post")
        
        # Sauvegarder
        self.save_posts(output_file)
        
        # Boucle de monitoring
        check_count = 1
        try:
            while True:
                # Attendre l'intervalle
                print(f"\n⏳ Prochaine vérification dans {self.check_interval // 60} minutes...")
                print(f"   (Appuyez sur Ctrl+C pour arrêter)")
                
                # Compte à rebours
                for remaining in range(self.check_interval, 0, -60):
                    mins = remaining // 60
                    print(f"   ⏰ {mins} minute(s) restante(s)...", end='\r')
                    time.sleep(60)
                
                check_count += 1
                print(f"\n\n{'=' * 70}")
                print(f"🔄 Vérification #{check_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'=' * 70}")
                
                # Mettre à jour les posts existants
                updated = self.update_existing_posts(email, password, page_url)
                
                # Vérifier les nouveaux posts
                new_posts = self.check_new_posts(email, password, page_url)
                
                if new_posts:
                    print(f"\n🎉 {len(new_posts)} NOUVEAU(X) POST(S) DÉTECTÉ(S) ! 🎉")
                    for idx, post in enumerate(new_posts, 1):
                        print(f"\n📌 Post #{idx}")
                        print(f"   📝 Contenu: {post['contenu'][:100]}...")
                        print(f"   🔗 URL: {post['url']}")
                        print(f"   📅 Date: {post['date_post']}")
                        print(f"   👍 {post['likes']} likes | 💬 {post['comments']} commentaires | 🔄 {post['shares']} partages")
                        print(f"   📊 Engagement total: {post['engagement_total']}")
                        if post['commentaires']:
                            print(f"   💬 {len(post['commentaires'])} commentaire(s) extrait(s)")
                    
                    # Sauvegarder immédiatement
                    self.save_posts(output_file)
                    print(f"\n✅ Nouveaux posts sauvegardés !")
                elif updated > 0:
                    # Sauvegarder si des mises à jour ont eu lieu
                    self.save_posts(output_file)
                    print(f"\n✅ Mises à jour sauvegardées !")
                else:
                    print("✅ Aucun nouveau post ni mise à jour détectés")
                
                # Afficher les statistiques
                print(f"\n📊 STATISTIQUES GLOBALES:")
                print(f"   Total posts collectés: {len(self.all_posts)}")
                print(f"   Engagement total: {sum(p['engagement_total'] for p in self.all_posts)}")
                print(f"   Vérifications effectuées: {check_count}")
                
        except KeyboardInterrupt:
            print(f"\n\n{'=' * 70}")
            print("⏹️  MONITORING ARRÊTÉ PAR L'UTILISATEUR")
            print(f"{'=' * 70}")
            print(f"📊 Résumé final:")
            print(f"   ✅ {len(self.all_posts)} posts collectés au total")
            print(f"   ✅ {check_count} vérifications effectuées")
            print(f"   💾 Données sauvegardées dans: {output_file}")
            print(f"{'=' * 70}")


def main():
    """Fonction principale"""
    
    # Charger les identifiants depuis .env
    email = os.getenv('FB_EMAIL')
    password = os.getenv('FB_PASSWORD')
    page_url = os.getenv('PAGE_URL', 'https://web.facebook.com/lobspaalgaBF')
    
    # Intervalle de vérification (en secondes)
    check_interval = int(os.getenv('CHECK_INTERVAL', '600'))  # 600s = 10min par défaut
    
    if not email or not password:
        print("❌ Erreur: Identifiants manquants dans le fichier .env")
        return
    
    # Créer et démarrer le moniteur
    monitor = FacebookRealtimeMonitor(check_interval=check_interval)
    monitor.start_monitoring(
        email=email,
        password=password,
        page_url=page_url,
        output_file='observateur_paalga_stream.json'
    )


if __name__ == "__main__":
    main()
