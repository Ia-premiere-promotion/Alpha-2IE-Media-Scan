#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper pour lefaso.net
"""

from .base_scraper import BaseWebScraper
import re
import html

class LeFasoScraper(BaseWebScraper):
    
    def __init__(self):
        super().__init__('LeFaso', 'https://lefaso.net')
        self.sections = {
            "Actualités": "https://lefaso.net/spip.php?rubrique1",
            "Politique": "https://lefaso.net/spip.php?rubrique2",
            "Économie": "https://lefaso.net/spip.php?rubrique3",
            "Société": "https://lefaso.net/spip.php?rubrique4",
            "International": "https://lefaso.net/spip.php?rubrique7",
            "Sport": "https://lefaso.net/spip.php?rubrique5",
            "Culture": "https://lefaso.net/spip.php?rubrique18",
        }
    
    def get_article_urls(self, section_url, max_articles=20):
        """Récupère les URLs des articles d'une section"""
        soup = self.make_request(section_url)
        if not soup:
            return []
        
        urls = []
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and 'spip.php?article' in href:
                if href.startswith('http'):
                    url_complete = href
                elif href.startswith('/'):
                    url_complete = self.base_url + href
                else:
                    url_complete = self.base_url + '/' + href
                
                if url_complete not in urls:
                    urls.append(url_complete)
                
                if len(urls) >= max_articles:
                    break
        
        return urls[:max_articles]
    
    def scrape_article(self, url):
        """Scrape un article complet de LeFaso.net"""
        soup = self.make_request(url)
        if not soup:
            return None
        
        # TITRE - chercher tous les h1.entry-title et ignorer "Newsletter"
        titre = ''
        all_titles = soup.find_all('h1', class_='entry-title')
        for titre_tag in all_titles:
            titre_brut = titre_tag.get_text(strip=True)
            titre_brut = html.unescape(titre_brut)
            titre_brut = re.sub(r'\s+', ' ', titre_brut)
            titre_brut = re.sub(r'\s*-\s*le[Ff]aso\.net.*$', '', titre_brut)
            titre_brut = re.sub(r'\s*-\s*LeFaso\.net.*$', '', titre_brut)
            # Ignorer "Newsletter" et prendre le premier titre valide
            if titre_brut and titre_brut != 'Newsletter LeFaso.net' and 'Newsletter' not in titre_brut:
                titre = titre_brut.strip()
                break
        
        if not titre:
            titre = 'Sans titre'
        
        # DATE
        date_brute = None
        for p_tag in soup.find_all('p'):
            texte_p = p_tag.get_text(strip=True)
            if 'Publié' in texte_p or 'publié' in texte_p:
                match = re.search(r'Publié le (.+?)(?:\s+à|\s*$)', texte_p, re.I)
                if match:
                    date_brute = match.group(1).strip()
                    break
        
        date = self.parse_french_date(date_brute) if date_brute else None
        
        # Vérifier si on doit scraper cet article basé sur sa date
        if not self.should_scrape_article(date):
            return None
        
        # AUTEUR
        auteur = None
        auteur_meta = soup.find('meta', {'name': re.compile('author', re.I)})
        if auteur_meta:
            auteur = auteur_meta.get('content', '')
        
        # CONTENU
        contenu = ''
        contenu_div = soup.find('div', class_='entry-content')
        if contenu_div:
            paragraphes = contenu_div.find_all('p')
            contenu = '\n\n'.join([p.get_text(strip=True) for p in paragraphes if p.get_text(strip=True)])
        
        # COMMENTAIRES/RÉACTIONS
        commentaires = 0
        try:
            # Chercher le titre avec le compteur de réactions
            reactions_heading = soup.find('h2', string=re.compile(r'Vos r[ée]actions', re.I))
            if reactions_heading:
                # Extraire le nombre entre parenthèses
                match = re.search(r'\((\d+)\)', reactions_heading.get_text())
                if match:
                    commentaires = int(match.group(1))
            
            # Méthode alternative: compter les éléments <li class="forum-fil">
            if commentaires == 0:
                forum_ul = soup.find('ul', id='navforum', class_='forum')
                if forum_ul:
                    forum_fils = forum_ul.find_all('li', class_='forum-fil', recursive=False)
                    commentaires = len(forum_fils)
        except Exception as e:
            print(f"  ⚠️ Erreur extraction commentaires: {e}")
            pass
        
        return self.create_article_dict(
            url=url,
            titre=titre,
            contenu=contenu,
            date=date,
            auteur=auteur,
            commentaires=commentaires
        )
    
    def scrape_all_sections(self, max_articles_per_section=20):
        """Scrape toutes les sections"""
        print(f"\n{'='*70}")
        print(f"🔍 SCRAPING: {self.media_name.upper()}")
        print(f"{'='*70}")
        
        all_articles = []
        for nom_section, url_section in self.sections.items():
            print(f"\n📂 Section: {nom_section}")
            articles = self.scrape_section(url_section, max_articles_per_section)
            all_articles.extend(articles)
        
        print(f"\n✅ Total: {len(all_articles)} articles scrapés de {self.media_name}")
        return all_articles


if __name__ == "__main__":
    scraper = LeFasoScraper()
    articles = scraper.scrape_all_sections(max_articles_per_section=5)
    print(f"\n📊 Articles récupérés: {len(articles)}")
    if articles:
        print(f"Exemple: {articles[0]['titre'][:100]}...")
