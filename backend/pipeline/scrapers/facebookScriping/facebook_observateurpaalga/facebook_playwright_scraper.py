"""
Script de scraping Facebook avec Playwright (sans API)
Page cible: Observateur Paalga
"""

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import json
import time
import re
import os
from datetime import datetime
from typing import List, Dict
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()


class FacebookPlaywrightScraper:
    """Scraper Facebook utilisant Playwright"""
    
    def __init__(self, headless: bool = False):
        """
        Initialise le scraper
        
        Args:
            headless: Mode sans interface graphique
        """
        self.headless = headless
        self.posts_data = []
        
    def login(self, email: str, password: str, page):
        """
        Se connecte à Facebook
        
        Args:
            email: Email Facebook
            password: Mot de passe
            page: Instance de page Playwright
        """
        print("🔐 Connexion à Facebook...")
        
        # Aller sur Facebook
        page.goto("https://www.facebook.com/", wait_until="networkidle")
        time.sleep(2)
        
        # Remplir le formulaire
        try:
            # Accepter les cookies si demandé
            try:
                page.click('button[data-cookiebanner="accept_button"]', timeout=3000)
                time.sleep(1)
            except:
                pass
            
            # Email
            page.fill('input[name="email"]', email)
            time.sleep(0.5)
            
            # Mot de passe
            page.fill('input[name="pass"]', password)
            time.sleep(0.5)
            
            # Cliquer sur Se connecter
            page.click('button[name="login"]')
            
            # Attendre la redirection
            page.wait_for_load_state("networkidle", timeout=15000)
            time.sleep(3)
            
            print("✅ Connexion réussie !")
            return True
            
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return False
    
    def scroll_page(self, page, scrolls: int = 5):
        """
        Scroll la page pour charger plus de contenu
        
        Args:
            page: Instance de page
            scrolls: Nombre de scrolls
        """
        print(f"📜 Scrolling pour charger le contenu ({scrolls} scrolls)...")
        
        for i in range(scrolls):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            print(f"  Scroll {i+1}/{scrolls}")
    
    def extract_number(self, text: str) -> int:
        """Extrait un nombre d'un texte"""
        if not text:
            return 0
        
        # Gérer les formats : 1K, 1M, 1,5K, etc.
        text = text.strip().lower()
        
        # Enlever tout sauf chiffres, virgules, points et k/m
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
    
    def extract_comments(self, post_element, page, max_comments: int = 10) -> tuple:
        """
        Extrait les commentaires d'un post et compte le nombre total
        
        Args:
            post_element: Élément du post
            page: Instance de page
            max_comments: Nombre maximum de commentaires à extraire
            
        Returns:
            tuple: (nombre_total_commentaires, liste_commentaires)
        """
        commentaires = []
        total_comments = 0
        
        try:
            # D'abord, chercher le nombre total de commentaires dans les aria-labels
            try:
                # Chercher tous les éléments avec aria-label
                all_elements = post_element.query_selector_all('[aria-label]')
                for elem in all_elements:
                    aria_label = elem.get_attribute('aria-label') or ""
                    
                    # Chercher "X commentaires" ou "X commentaire"
                    # Pattern: "6 commentaires", "1 commentaire", etc.
                    match = re.search(r'(\d+)\s+commentaires?', aria_label, re.IGNORECASE)
                    if match:
                        total_comments = max(total_comments, int(match.group(1)))
                    
                    # Aussi chercher dans les aria-label qui mentionnent les commentaires
                    if 'commentaire' in aria_label.lower():
                        nums = re.findall(r'(\d+)', aria_label)
                        for num in nums:
                            try:
                                n = int(num)
                                if 1 <= n <= 10000:  # Plage raisonnable
                                    total_comments = max(total_comments, n)
                            except:
                                pass
            except:
                pass
            
            # Essayer de cliquer pour afficher tous les commentaires
            try:
                # Chercher le bouton "Afficher plus de commentaires" ou "Voir X commentaires"
                show_more_buttons = [
                    'div[role="button"]:has-text("Afficher")',
                    'div[role="button"]:has-text("commentaire")',
                    'span:has-text("Afficher plus")',
                    'div[role="button"]:has-text("Voir")'
                ]
                
                for selector in show_more_buttons:
                    try:
                        buttons = post_element.query_selector_all(selector)
                        for btn in buttons:
                            text = btn.inner_text().lower()
                            if 'commentaire' in text or 'afficher' in text or 'voir' in text:
                                try:
                                    btn.click()
                                    time.sleep(1.5)  # Attendre le chargement
                                except:
                                    pass
                    except:
                        pass
            except:
                pass
            
            # Maintenant extraire les commentaires réels
            try:
                # Chercher les éléments de commentaires spécifiques
                comment_article_selectors = [
                    'div[role="article"][aria-label*="Commentaire"]',
                    'div[role="article"][aria-label*="commentaire"]',
                ]
                
                seen_texts = set()
                
                for selector in comment_article_selectors:
                    comment_articles = post_element.query_selector_all(selector)
                    
                    for comment_elem in comment_articles:
                        if len(commentaires) >= max_comments:
                            break
                            
                        try:
                            # Récupérer l'aria-label pour l'auteur
                            aria_label = comment_elem.get_attribute('aria-label') or ""
                            
                            # Chercher le texte du commentaire dans tous les div[dir="auto"]
                            text_divs = comment_elem.query_selector_all('div[dir="auto"]')
                            
                            # Prendre le div qui contient le texte le plus long (le commentaire principal)
                            best_text = ""
                            for text_div in text_divs:
                                texte = text_div.inner_text().strip()
                                if len(texte) > len(best_text) and len(texte) < 1000:
                                    best_text = texte
                            
                            if best_text and best_text not in seen_texts:
                                commentaires.append({
                                    'numero': len(commentaires) + 1,
                                    'texte': best_text,
                                    'auteur': aria_label.split(' il y a ')[0].replace('Commentaire de ', '') if 'Commentaire de' in aria_label else ''
                                })
                                seen_texts.add(best_text)
                                
                        except Exception as e:
                            continue
                    
                    if len(commentaires) >= max_comments:
                        break
                            
            except Exception as e:
                print(f"    ⚠️ Erreur extraction texte commentaires: {e}")
            
            # Si on n'a pas trouvé le nombre total, utiliser le nombre extrait
            if total_comments == 0:
                total_comments = len(commentaires)
                    
        except Exception as e:
            print(f"    ⚠️ Erreur extraction commentaires: {e}")
        
        return total_comments, commentaires[:max_comments]
    
    def expand_post_content(self, post_element):
        """Clique sur 'Voir plus' pour étendre le contenu"""
        try:
            see_more = post_element.query_selector('div[role="button"]:has-text("En voir plus")')
            if not see_more:
                see_more = post_element.query_selector('div[role="button"]:has-text("Voir plus")')
            if see_more:
                see_more.click()
                time.sleep(0.5)
        except:
            pass
    
    def get_exact_metrics(self, post_element, page) -> tuple:
        """
        Récupère les métriques exactes en survolant/cliquant sur les éléments
        
        Returns:
            tuple: (likes, comments, shares)
        """
        likes = 0
        comments = 0
        shares = 0
        
        try:
            # Méthode 1: Chercher dans les span avec aria-label (plus fiable)
            all_spans = post_element.query_selector_all('span[aria-label]')
            for span in all_spans:
                aria_label = span.get_attribute('aria-label') or ""
                
                # Likes/Réactions
                if any(word in aria_label.lower() for word in ['réaction', 'j\'aime', 'like', 'reaction']):
                    numbers = re.findall(r'(\d+(?:\s?\d+)*)', aria_label)
                    if numbers:
                        # Prendre le premier nombre trouvé
                        num_str = numbers[0].replace(' ', '').replace('\xa0', '')
                        try:
                            likes = max(likes, int(num_str))
                        except:
                            pass
                
                # Commentaires
                if 'commentaire' in aria_label.lower():
                    numbers = re.findall(r'(\d+(?:\s?\d+)*)', aria_label)
                    if numbers:
                        num_str = numbers[0].replace(' ', '').replace('\xa0', '')
                        try:
                            comments = max(comments, int(num_str))
                        except:
                            pass
                
                # Partages
                if 'partage' in aria_label.lower() or 'share' in aria_label.lower():
                    numbers = re.findall(r'(\d+(?:\s?\d+)*)', aria_label)
                    if numbers:
                        num_str = numbers[0].replace(' ', '').replace('\xa0', '')
                        try:
                            shares = max(shares, int(num_str))
                        except:
                            pass
            
            # Méthode 2: Chercher les liens et boutons spécifiques
            try:
                # Commentaires - chercher le texte "X commentaires"
                comment_links = post_element.query_selector_all('a, span, div')
                for elem in comment_links:
                    text = elem.inner_text().strip()
                    
                    # Pattern pour commentaires: "6 commentaires", "1 commentaire"
                    comment_match = re.search(r'^(\d+)\s+commentaires?$', text, re.IGNORECASE)
                    if comment_match:
                        try:
                            comments = max(comments, int(comment_match.group(1)))
                        except:
                            pass
                    
                    # Pattern pour partages
                    share_match = re.search(r'^(\d+)\s+partages?$', text, re.IGNORECASE)
                    if share_match:
                        try:
                            shares = max(shares, int(share_match.group(1)))
                        except:
                            pass
            except:
                pass
            
            # Méthode 3: Chercher dans le texte complet avec patterns plus précis
            try:
                full_text = post_element.inner_text()
                lines = full_text.split('\n')
                
                for line in lines:
                    line = line.strip()
                    
                    # Ligne qui commence par un nombre suivi de "commentaire(s)"
                    if re.match(r'^\d+\s+commentaires?', line, re.IGNORECASE):
                        nums = re.findall(r'^(\d+)', line)
                        if nums and comments == 0:
                            comments = int(nums[0])
                    
                    # Ligne qui commence par un nombre suivi de "partage(s)"
                    if re.match(r'^\d+\s+partages?', line, re.IGNORECASE):
                        nums = re.findall(r'^(\d+)', line)
                        if nums and shares == 0:
                            shares = int(nums[0])
            except:
                pass
                
        except Exception as e:
            print(f"    ⚠️ Erreur métriques exactes: {e}")
        
        return likes, comments, shares
    
    def extract_post_data(self, post_element, page) -> Dict:
        """
        Extrait les données d'un post
        
        Args:
            post_element: Élément du post
            page: Instance de page
            
        Returns:
            Dictionnaire des données du post
        """
        try:
            # Vérifier que c'est bien un vrai post et pas un élément parasite
            # Ignorer les éléments de chargement, suggestions, etc.
            element_text = post_element.inner_text()
            
            # Filtres de sécurité pour ignorer les faux posts
            ignore_keywords = [
                'chargement',
                'loading',
                'suggestions pour vous',
                'personnes que vous connaissez',
                'pages que vous pourriez aimer',
                'publicité',
                'sponsorisé',
                'sponsored'
            ]
            
            element_text_lower = element_text.lower()
            for keyword in ignore_keywords:
                if keyword in element_text_lower and len(element_text) < 200:
                    # C'est probablement un élément parasite
                    return None
            
            # Étendre le contenu si tronqué
            self.expand_post_content(post_element)
            
            # Contenu du post - essayer plusieurs sélecteurs
            contenu = ""
            try:
                # Essayer différents sélecteurs pour le contenu
                content_selectors = [
                    '[data-ad-preview="message"]',
                    'div[data-ad-comet-preview="message"]',
                    '[dir="auto"]',
                    'div.x1iorvi4',
                    'div.xdj266r'
                ]
                
                for selector in content_selectors:
                    elements = post_element.query_selector_all(selector)
                    for elem in elements:
                        text = elem.inner_text().strip()
                        if text and len(text) > len(contenu):
                            contenu = text
                    if contenu:
                        break
                        
            except Exception as e:
                print(f"  ⚠️ Erreur contenu: {e}")
            
            # URL du post
            url = ""
            try:
                # Chercher le lien timestamp
                link_selectors = [
                    'a[href*="/posts/"]',
                    'a[href*="/permalink/"]',
                    'a[href*="/photo/"]',
                    'a[role="link"]'
                ]
                
                for selector in link_selectors:
                    link = post_element.query_selector(selector)
                    if link:
                        url = link.get_attribute('href')
                        if url:
                            if not url.startswith('http'):
                                url = f"https://www.facebook.com{url}"
                            # Ignorer les URLs de commentaires (ce ne sont pas des posts)
                            if 'comment_id=' in url or 'reply_comment_id=' in url:
                                return None
                            # Vérifier que l'URL contient bien la page cible
                            if 'lobspaalgaBF' not in url and 'observateur' not in url.lower():
                                # Ce n'est pas un post de la page Observateur Paalga
                                return None
                            break
            except Exception as e:
                print(f"  ⚠️ Erreur URL: {e}")
            
            # Si pas d'URL valide, ce n'est pas un vrai post
            if not url:
                return None
            
            # Extraire la date depuis l'URL ou le texte
            date_post = datetime.now().isoformat()
            
            # Méthode améliorée pour récupérer les vraies métriques
            print(f"    🔍 Récupération des métriques exactes...")
            likes, comments, shares = self.get_exact_metrics(post_element, page)
            
            # Si aucune métrique trouvée avec la méthode exacte, utiliser l'ancienne méthode
            if likes == 0 and comments == 0 and shares == 0:
                try:
                    # Récupérer tout le texte du post
                    full_text = post_element.inner_text()
                    
                    # Patterns améliorés pour capturer les métriques
                    # Likes/Réactions - chercher "X personnes" ou juste le nombre
                    reactions_patterns = [
                        r'(\d+(?:[,\.]\d+)?[KMk]?)\s*(?:personnes?\s+)?(?:ont réagi|réaction|j\'aime)',
                        r'(\d+[KMk]?)\s*$',  # Nombre seul en fin de ligne
                    ]
                    
                    for pattern in reactions_patterns:
                        like_match = re.search(pattern, full_text, re.IGNORECASE | re.MULTILINE)
                        if like_match:
                            likes = self.extract_number(like_match.group(1))
                            if likes > 0:
                                break
                    
                    # Commentaires
                    comment_patterns = [
                        r'(\d+(?:[,\.]\d+)?[KMk]?)\s+commentaires?',
                        r'commentaires?\s*[:\s]*(\d+(?:[,\.]\d+)?[KMk]?)',
                    ]
                    
                    for pattern in comment_patterns:
                        comment_match = re.search(pattern, full_text, re.IGNORECASE)
                        if comment_match:
                            comments = self.extract_number(comment_match.group(1))
                            if comments > 0:
                                break
                    
                    # Partages
                    share_patterns = [
                        r'(\d+(?:[,\.]\d+)?[KMk]?)\s+partages?',
                        r'partages?\s*[:\s]*(\d+(?:[,\.]\d+)?[KMk]?)',
                    ]
                    
                    for pattern in share_patterns:
                        share_match = re.search(pattern, full_text, re.IGNORECASE)
                        if share_match:
                            shares = self.extract_number(share_match.group(1))
                            if shares > 0:
                                break
                        
                except Exception as e:
                    print(f"  ⚠️ Erreur métriques fallback: {e}")
            
            print(f"    📊 Métriques: {likes} likes, {comments} commentaires, {shares} partages")
            
            # Si pas de contenu texte, vérifier si c'est un post média (photo/vidéo)
            if not contenu:
                # Vérifier si c'est un post avec image ou vidéo
                has_media = False
                try:
                    # Chercher les images
                    images = post_element.query_selector_all('img[src*="scontent"]')
                    if len(images) > 0:
                        has_media = True
                        contenu = "[Post avec image]"
                    
                    # Chercher les vidéos
                    videos = post_element.query_selector_all('video')
                    if len(videos) > 0:
                        has_media = True
                        contenu = "[Post avec vidéo]"
                except:
                    pass
                
                # Si toujours pas de contenu, ignorer ce post
                if not has_media and not contenu:
                    return None
            
            # Validation finale : le contenu doit avoir un minimum de sens
            if len(contenu) < 5:  # Trop court pour être un vrai post
                return None
            
            post_id = url.split('/')[-1].split('?')[0] if url else f"post_{len(self.posts_data)}"
            
            # Extraire les commentaires
            commentaires = []
            print(f"    📝 Extraction des commentaires...")
            
            # Si le post a des commentaires, cliquer sur le lien pour charger tous les commentaires
            if comments > 0:
                try:
                    # Chercher et cliquer sur le lien des commentaires pour les charger tous
                    comment_links = post_element.query_selector_all('a, div[role="button"], span')
                    for link in comment_links:
                        try:
                            text = link.inner_text().strip()
                            # Chercher le texte type "6 commentaires"
                            if re.search(r'\d+\s+commentaires?', text, re.IGNORECASE):
                                try:
                                    link.click()
                                    time.sleep(2)  # Attendre le chargement des commentaires
                                    print(f"    🔄 Chargement de tous les commentaires...")
                                    break
                                except:
                                    pass
                        except:
                            continue
                except:
                    pass
            
            detected_comments, commentaires = self.extract_comments(post_element, page, max_comments=20)
            
            # Utiliser le nombre détecté si plus grand que celui trouvé avant
            if detected_comments > comments:
                comments = detected_comments
            
            print(f"    ✓ {comments} commentaires détectés, {len(commentaires)} extraits")
            
            return {
                'post_id': post_id,
                'url': url,
                'source': 'Facebook - Observateur Paalga',
                'date_post': date_post,
                'contenu': contenu,
                'type_post': 'status',
                'likes': likes,
                'comments': comments,
                'shares': shares,
                'engagement_total': likes + comments + shares,
                'commentaires': commentaires
            }
            
        except Exception as e:
            print(f"  ⚠️ Erreur extraction post: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def scrape_page(self, page_url: str, email: str, password: str, max_posts: int = 50):
        """
        Scrape une page Facebook
        
        Args:
            page_url: URL de la page à scraper
            email: Email Facebook
            password: Mot de passe
            max_posts: Nombre maximum de posts à extraire
        """
        with sync_playwright() as p:
            print("🚀 Lancement du navigateur...")
            
            # Lancer le navigateur
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = context.new_page()
            
            try:
                # Connexion
                if not self.login(email, password, page):
                    print("❌ Impossible de se connecter")
                    return
                
                # Aller sur la page
                print(f"📍 Navigation vers {page_url}...")
                page.goto(page_url, wait_until="networkidle")
                time.sleep(3)
                
                # Nombre de scrolls depuis .env
                num_scrolls = int(os.getenv('NUM_SCROLLS', '20'))
                
                # Scroll pour charger plus de posts
                self.scroll_page(page, scrolls=num_scrolls)
                
                # Extraire les posts
                print("📊 Extraction des posts...")
                
                # Sauvegarder la page pour debug
                print("💾 Sauvegarde de la page HTML pour analyse...")
                with open('debug_page.html', 'w', encoding='utf-8') as f:
                    f.write(page.content())
                
                # Sélecteurs possibles pour les posts
                post_selectors = [
                    '[role="article"]',
                    'div[data-ad-preview="message"]',
                    '.userContentWrapper',
                    'div.x1yztbdb',
                    'div[data-pagelet^="FeedUnit"]'
                ]
                
                posts = []
                for selector in post_selectors:
                    posts = page.query_selector_all(selector)
                    if len(posts) > 0:
                        print(f"✅ Trouvé {len(posts)} posts avec le sélecteur: {selector}")
                        break
                
                if len(posts) == 0:
                    print("⚠️ Aucun post trouvé. Vérifiez les sélecteurs.")
                    # Sauvegarder la page HTML pour debug
                    with open('debug_page.html', 'w', encoding='utf-8') as f:
                        f.write(page.content())
                    print("💾 Page HTML sauvegardée dans debug_page.html")
                
                # Extraire les données de chaque post
                for idx, post in enumerate(posts[:max_posts], 1):
                    print(f"  Extraction post {idx}/{min(len(posts), max_posts)}...")
                    try:
                        post_data = self.extract_post_data(post, page)
                        if post_data and post_data['contenu']:  # Ne garder que les posts avec contenu
                            self.posts_data.append(post_data)
                            print(f"    ✓ Post extrait: {len(post_data['contenu'][:50])} caractères, {post_data['engagement_total']} engagement")
                        else:
                            print(f"    ⊘ Post ignoré (pas de contenu)")
                    except Exception as e:
                        print(f"    ✗ Erreur: {e}")
                        continue
                
                print(f"\n✅ {len(self.posts_data)} posts extraits avec succès !")
                
            except Exception as e:
                print(f"❌ Erreur lors du scraping: {e}")
                import traceback
                traceback.print_exc()
            
            finally:
                # Fermer le navigateur
                browser.close()
    
    def save_to_json(self, output_file: str = 'observateur_paalga_posts.json'):
        """
        Sauvegarde les données en JSON
        
        Args:
            output_file: Nom du fichier de sortie
        """
        output = {
            'posts': self.posts_data,
            'metadata': {
                'total_posts': len(self.posts_data),
                'scraped_at': datetime.now().isoformat(),
                'total_engagement': sum(p['engagement_total'] for p in self.posts_data)
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Données sauvegardées dans: {output_file}")
        print(f"📊 Statistiques:")
        print(f"   - Posts extraits: {len(self.posts_data)}")
        print(f"   - Engagement total: {output['metadata']['total_engagement']}")


def main():
    """Fonction principale"""
    
    print("=" * 60)
    print("🔍 SCRAPER FACEBOOK AVEC PLAYWRIGHT")
    print("   Page: Observateur Paalga")
    print("=" * 60)
    
    # Charger les identifiants depuis .env
    email = os.getenv('FB_EMAIL')
    password = os.getenv('FB_PASSWORD')
    page_url = os.getenv('PAGE_URL', 'https://web.facebook.com/lobspaalgaBF')
    max_posts = int(os.getenv('MAX_POSTS', '50'))
    headless = os.getenv('HEADLESS', 'False').lower() == 'true'
    output_file = os.getenv('OUTPUT_FILE', 'observateur_paalga_posts.json')
    
    if not email or not password:
        print("❌ Erreur: Identifiants manquants dans le fichier .env")
        print("Veuillez créer un fichier .env avec FB_EMAIL et FB_PASSWORD")
        return
    
    print(f"\n🔐 Connexion avec: {email}")
    print(f"📍 Page cible: {page_url}")
    print(f"📊 Posts à extraire: {max_posts}")
    
    # Créer le scraper
    scraper = FacebookPlaywrightScraper(headless=headless)
    
    # Scraper
    scraper.scrape_page(
        page_url=page_url,
        email=email,
        password=password,
        max_posts=max_posts
    )
    
    # Sauvegarder
    scraper.save_to_json(output_file)
    
    print("\n✅ TERMINÉ !")


if __name__ == "__main__":
    main()
