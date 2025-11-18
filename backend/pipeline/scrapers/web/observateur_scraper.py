#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper pour L'Observateur Paalga (lobservateur.bf)
"""

from .base_scraper import BaseWebScraper
import html

class ObservateurScraper(BaseWebScraper):
    
    def __init__(self):
        super().__init__("L'Observateur Paalga", 'https://www.lobservateur.bf')
        self.sections = {
            "A la Une": "https://www.lobservateur.bf/ala-une",
            "Politique": "https://www.lobservateur.bf/politique",
            "Société": "https://www.lobservateur.bf/societe",
            "Sport": "https://www.lobservateur.bf/sport",
            "Culture": "https://www.lobservateur.bf/culture",
            "Economie": "https://www.lobservateur.bf/economie",
        }
    
    def get_article_urls(self, section_url, max_articles=20):
        """Récupère les URLs des articles"""
        soup = self.make_request(section_url)
        if not soup:
            return []
        
        urls = []
        for link in soup.select('h3.entry-title a, h2.entry-title a'):
            href = link.get('href')
            if href and href.startswith(self.base_url) and href not in urls:
                urls.append(href)
            if len(urls) >= max_articles:
                break
        
        return urls[:max_articles]
    
    def scrape_article(self, url):
        """Scrape un article de L'Observateur"""
        soup = self.make_request(url)
        if not soup:
            return None
        
        # TITRE
        titre = ''
        titre_tag = soup.find('h1', class_='entry-title')
        if titre_tag:
            titre = html.unescape(titre_tag.get_text(strip=True))
        
        # DATE
        date = None
        date_div = soup.find('div', class_='entry-meta')
        if date_div:
            date_str = date_div.get_text(strip=True).replace('Publication :', '').strip()
            date = self.parse_french_date(date_str)
        
        # Vérifier si on doit scraper cet article basé sur sa date
        if not self.should_scrape_article(date):
            return None
        
        # AUTEUR
        auteur = None
        auteur_tag = soup.find('span', class_='author')
        if auteur_tag:
            auteur = auteur_tag.get_text(strip=True)
        
        # CONTENU
        contenu = ''
        contenu_div = soup.find('div', class_='entry-content')
        if contenu_div:
            paragraphes = contenu_div.find_all('p')
            contenu = '\n\n'.join([html.unescape(p.get_text(strip=True)) for p in paragraphes if p.get_text(strip=True)])
        
        return self.create_article_dict(
            url=url,
            titre=titre,
            contenu=contenu,
            date=date,
            auteur=auteur
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
