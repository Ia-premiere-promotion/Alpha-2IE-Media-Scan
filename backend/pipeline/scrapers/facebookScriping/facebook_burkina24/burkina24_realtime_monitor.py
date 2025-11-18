"""
Monitoring en temps réel de la page Facebook Burkina24
Détecte les nouveaux posts et met à jour les métriques automatiquement
"""

from playwright.sync_api import sync_playwright
import json
import time
import re
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class Burkina24RealtimeMonitor:
    """Moniteur en temps réel pour Burkina24"""
    
    def __init__(self, headless=False):
        self.headless = headless
        self.posts_cache = {}  # Cache des posts avec leurs métriques
        self.data_file = 'burkina24_realtime.json'
        self.check_interval = 60  # Intervalle de vérification en secondes
        self.load_existing_data()
    
    def load_existing_data(self):
        """Charge les données existantes depuis le fichier JSON"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'posts' in data:
                        for post in data['posts']:
                            self.posts_cache[post['post_id']] = post
                print(f"📂 {len(self.posts_cache)} posts chargés depuis {self.data_file}")
        except Exception as e:
            print(f"⚠️ Erreur chargement données: {e}")
    
    def save_data(self):
        """Sauvegarde les données dans le fichier JSON"""
        try:
            posts_list = list(self.posts_cache.values())
            # Trier par date (plus récents en premier)
            posts_list.sort(key=lambda x: x.get('date_post', ''), reverse=True)
            
            output = {
                'posts': posts_list,
                'metadata': {
                    'total_posts': len(posts_list),
                    'last_update': datetime.now().isoformat(),
                    'total_engagement': sum(p['engagement_total'] for p in posts_list),
                    'page': 'Burkina24',
                    'page_url': 'https://web.facebook.com/Burkina24'
                }
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"❌ Erreur sauvegarde: {e}")
            return False
    
    def extract_number(self, text: str) -> int:
        """Extrait un nombre d'un texte"""
        if not text:
            return 0
        
        text = text.strip().lower()
        text = re.sub(r'[^\d,\.km]', '', text)
        
        multiplier = 1
        if 'k' in text:
            multiplier = 1000
            text = text.replace('k', '')
        elif 'm' in text:
            multiplier = 1000000
            text = text.replace('m', '')
        
        try:
            number = float(text.replace(',', '.'))
            return int(number * multiplier)
        except:
            return 0
    
    def extract_comments(self, article, page, max_comments=20):
        """Extrait les commentaires d'un post"""
        commentaires = []
        total_comments = 0
        
        try:
            full_text = article.inner_text()
            comment_match = re.search(r'(\d+)\s+commentaires?', full_text, re.IGNORECASE)
            if comment_match:
                total_comments = int(comment_match.group(1))
            
            if total_comments == 0:
                return 0, []
            
            # Essayer de cliquer pour afficher les commentaires
            try:
                elements = article.query_selector_all('span, div[role="button"], a')
                for elem in elements:
                    elem_text = elem.inner_text().strip()
                    if f'{total_comments} commentaire' in elem_text.lower():
                        elem.click()
                        time.sleep(2)
                        break
            except:
                pass
            
            # Extraire les commentaires
            comment_selectors = [
                'div[role="article"][aria-label*="ommentaire"]',
                'div[role="article"][aria-label*="Comment"]',
            ]
            
            seen_texts = set()
            
            for selector in comment_selectors:
                comment_elems = article.query_selector_all(selector)
                
                for comment_elem in comment_elems:
                    if len(commentaires) >= max_comments:
                        break
                    
                    try:
                        aria_label = comment_elem.get_attribute('aria-label') or ""
                        
                        auteur = ""
                        if 'commentaire de' in aria_label.lower():
                            auteur = aria_label.split('il y a')[0].replace('Commentaire de ', '').replace('commentaire de ', '').strip()
                        
                        text_divs = comment_elem.query_selector_all('div[dir="auto"]')
                        best_text = ""
                        
                        for text_div in text_divs:
                            texte = text_div.inner_text().strip()
                            if len(texte) > len(best_text) and len(texte) < 2000:
                                best_text = texte
                        
                        if best_text and best_text not in seen_texts and len(best_text) > 5:
                            commentaires.append({
                                'numero': len(commentaires) + 1,
                                'auteur': auteur,
                                'texte': best_text
                            })
                            seen_texts.add(best_text)
                    
                    except:
                        continue
                
                if len(commentaires) > 0:
                    break
            
            if total_comments == 0:
                total_comments = len(commentaires)
                
        except Exception as e:
            pass
        
        return total_comments, commentaires
    
    def extract_post_metrics(self, article, page, post_id=None):
        """Extrait les métriques d'un post"""
        try:
            # Contenu
            contenu = ""
            divs = article.query_selector_all('div[dir="auto"]')
            for div in divs:
                text = div.inner_text().strip()
                if len(text) > len(contenu) and len(text) < 2000:
                    contenu = text
            
            if len(contenu) < 20:
                return None
            
            # Métriques
            full_text = article.inner_text()
            
            likes = 0
            comments = 0
            shares = 0
            
            # Likes
            match = re.search(r'Toutes les réactions\s*:\s*(\d+)', full_text, re.IGNORECASE)
            if match:
                likes = int(match.group(1))
            
            # Commentaires
            match = re.search(r'(\d+)\s+commentaires?', full_text, re.IGNORECASE)
            if match:
                comments = int(match.group(1))
            
            # Partages
            match = re.search(r'(\d+)\s+partages?', full_text, re.IGNORECASE)
            if match:
                shares = int(match.group(1))
            
            # URL
            url = ""
            links = article.query_selector_all('a[href]')
            for link in links:
                href = link.get_attribute('href') or ""
                if '/posts/' in href or '/permalink/' in href or '/photo/' in href or '/videos/' in href:
                    url = href if href.startswith('http') else f"https://web.facebook.com{href}"
                    break
            
            # Générer un post_id basé sur le contenu si pas d'URL
            if not post_id:
                if url:
                    post_id = url.split('/')[-1].split('?')[0]
                else:
                    # Utiliser un hash du contenu comme ID
                    import hashlib
                    post_id = f"burkina24_{hashlib.md5(contenu.encode()).hexdigest()[:10]}"
            
            if not url:
                url = f"https://web.facebook.com/Burkina24#{post_id}"
            
            # Extraire les commentaires si nécessaire
            total_comments_detected, commentaires_list = self.extract_comments(article, page, max_comments=20)
            if total_comments_detected > comments:
                comments = total_comments_detected
            
            return {
                'post_id': post_id,
                'url': url,
                'source': 'Facebook - Burkina24',
                'date_post': datetime.now().isoformat(),
                'contenu': contenu,
                'type_post': 'status',
                'likes': likes,
                'comments': comments,
                'shares': shares,
                'engagement_total': likes + comments + shares,
                'commentaires': commentaires_list,
                'last_update': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"⚠️ Erreur extraction: {e}")
            return None
    
    def check_for_updates(self, page):
        """Vérifie les mises à jour sur la page"""
        try:
            print(f"\n🔄 Vérification des mises à jour... ({datetime.now().strftime('%H:%M:%S')})")
            
            # Rafraîchir la page
            page.reload(wait_until="domcontentloaded")
            time.sleep(3)
            
            # Scroller un peu pour charger le contenu
            for i in range(5):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1)
            
            # Extraire les posts
            articles = page.query_selector_all('[role="article"]')
            print(f"📊 {len(articles)} articles trouvés")
            
            new_posts = 0
            updated_posts = 0
            
            for idx, article in enumerate(articles[:20], 1):  # Limiter à 20 posts
                try:
                    post_data = self.extract_post_metrics(article, page)
                    
                    if post_data:
                        post_id = post_data['post_id']
                        
                        # Nouveau post
                        if post_id not in self.posts_cache:
                            self.posts_cache[post_id] = post_data
                            new_posts += 1
                            print(f"  🆕 Nouveau post: {post_data['contenu'][:60]}...")
                            print(f"     👍 {post_data['likes']} | 💬 {post_data['comments']} | 🔄 {post_data['shares']}")
                        
                        # Post existant - vérifier les mises à jour
                        else:
                            old_post = self.posts_cache[post_id]
                            changes = []
                            
                            if post_data['likes'] != old_post['likes']:
                                changes.append(f"Likes: {old_post['likes']} → {post_data['likes']}")
                            
                            if post_data['comments'] != old_post['comments']:
                                changes.append(f"Commentaires: {old_post['comments']} → {post_data['comments']}")
                            
                            if post_data['shares'] != old_post['shares']:
                                changes.append(f"Partages: {old_post['shares']} → {post_data['shares']}")
                            
                            if changes:
                                self.posts_cache[post_id] = post_data
                                updated_posts += 1
                                print(f"  🔄 Mise à jour: {post_data['contenu'][:60]}...")
                                for change in changes:
                                    print(f"     • {change}")
                
                except Exception as e:
                    continue
            
            # Sauvegarder les données
            if new_posts > 0 or updated_posts > 0:
                self.save_data()
                print(f"  💾 Données sauvegardées: {new_posts} nouveaux, {updated_posts} mis à jour")
            else:
                print(f"  ✓ Aucun changement détecté")
            
            # Afficher le résumé
            print(f"\n📈 RÉSUMÉ:")
            print(f"   Total posts surveillés: {len(self.posts_cache)}")
            print(f"   Total engagement: {sum(p['engagement_total'] for p in self.posts_cache.values())}")
            
        except Exception as e:
            print(f"❌ Erreur lors de la vérification: {e}")
    
    def start_monitoring(self, email, password, interval=None):
        """Démarre le monitoring en temps réel"""
        if interval:
            self.check_interval = interval
        
        with sync_playwright() as p:
            print("🚀 Lancement du navigateur...")
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(viewport={"width": 1920, "height": 1080})
            page = context.new_page()
            
            try:
                # Connexion
                print("🔐 Connexion à Facebook...")
                page.goto("https://www.facebook.com/")
                time.sleep(3)
                
                try:
                    page.click('button[data-cookiebanner="accept_button"]', timeout=3000)
                    time.sleep(1)
                except:
                    pass
                
                page.fill('input[name="email"]', email)
                page.fill('input[name="pass"]', password)
                page.click('button[name="login"]')
                page.wait_for_load_state("networkidle", timeout=15000)
                time.sleep(3)
                print("✅ Connexion réussie !")
                
                # Aller sur Burkina24
                print("📍 Navigation vers Burkina24...")
                page.goto("https://web.facebook.com/Burkina24")
                time.sleep(5)
                
                print(f"\n{'='*70}")
                print(f"🔴 MONITORING EN TEMPS RÉEL DÉMARRÉ")
                print(f"{'='*70}")
                print(f"Page: Burkina24")
                print(f"Intervalle de vérification: {self.check_interval} secondes")
                print(f"Fichier de sortie: {self.data_file}")
                print(f"{'='*70}\n")
                
                # Première vérification
                self.check_for_updates(page)
                
                # Boucle de monitoring
                iteration = 1
                while True:
                    print(f"\n⏳ Prochaine vérification dans {self.check_interval} secondes...")
                    print(f"   (Appuyez sur Ctrl+C pour arrêter)")
                    time.sleep(self.check_interval)
                    
                    iteration += 1
                    print(f"\n{'='*70}")
                    print(f"ITÉRATION #{iteration}")
                    print(f"{'='*70}")
                    
                    self.check_for_updates(page)
            
            except KeyboardInterrupt:
                print(f"\n\n{'='*70}")
                print("🛑 ARRÊT DU MONITORING")
                print(f"{'='*70}")
                print(f"Posts surveillés: {len(self.posts_cache)}")
                print(f"Données sauvegardées dans: {self.data_file}")
                print(f"{'='*70}\n")
            
            except Exception as e:
                print(f"❌ Erreur: {e}")
                import traceback
                traceback.print_exc()
            
            finally:
                browser.close()


def main():
    """Fonction principale"""
    
    print("="*70)
    print("🔴 MONITORING EN TEMPS RÉEL - Burkina24")
    print("="*70)
    
    # Configuration
    email = os.getenv('FB_EMAIL')
    password = os.getenv('FB_PASSWORD')
    headless = os.getenv('HEADLESS', 'False').lower() == 'true'
    check_interval = int(os.getenv('CHECK_INTERVAL', '60'))  # 60 secondes par défaut
    
    if not email or not password:
        print("❌ Erreur: Identifiants manquants dans le fichier .env")
        print("   Créez un fichier .env avec:")
        print("   FB_EMAIL=votre_email@example.com")
        print("   FB_PASSWORD=votre_mot_de_passe")
        print("   CHECK_INTERVAL=60  # Intervalle en secondes (optionnel)")
        return
    
    print(f"\n📧 Email: {email[:3]}***{email.split('@')[1] if '@' in email else ''}")
    print(f"⏱️ Intervalle: {check_interval} secondes")
    print(f"👁️ Mode: {'Headless' if headless else 'Visible'}")
    
    # Créer et démarrer le moniteur
    monitor = Burkina24RealtimeMonitor(headless=headless)
    monitor.start_monitoring(email, password, interval=check_interval)


if __name__ == "__main__":
    main()
