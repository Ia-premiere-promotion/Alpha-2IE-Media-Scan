#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper pour burkina24.com
"""

from .base_scraper import BaseWebScraper
import html
from datetime import datetime, timedelta

class Burkina24Scraper(BaseWebScraper):
    
    def __init__(self):
        super().__init__('Burkina24', 'https://burkina24.com')
        self.sections = {
            'Monde': 'https://burkina24.com/category/actualite/monde/',
            'Politique': 'https://burkina24.com/category/actualite/politique/',
            'Economie': 'https://burkina24.com/category/actualite/economie/',
            'Sport': 'https://burkina24.com/category/actualite/sports/',
            'Culture': 'https://burkina24.com/category/actualite/culture/',
            'Tech': 'https://burkina24.com/category/tech/',
            'Santé': 'https://burkina24.com/category/actualite/societe/sante/',
            'Education': 'https://burkina24.com/category/actualite/education/',
            'Société': 'https://burkina24.com/category/actualite/societe/societe-societe/',
        }
    
    def parse_relative_date(self, date_text):
        """Convertit les dates relatives en datetime"""
        try:
            maintenant = datetime.now()
            date_text = date_text.lower().strip()
            
            if "il y a" in date_text:
                if "minute" in date_text:
                    return maintenant
                elif "heure" in date_text:
                    hours = int(''.join(filter(str.isdigit, date_text.split("heure")[0]))) if any(c.isdigit() for c in date_text) else 1
                    return maintenant - timedelta(hours=hours)
                elif "jour" in date_text:
                    days = int(''.join(filter(str.isdigit, date_text.split("jour")[0])))
                    return maintenant - timedelta(days=days)
                elif "semaine" in date_text:
                    weeks = int(''.join(filter(str.isdigit, date_text.split("semaine")[0]))) if any(c.isdigit() for c in date_text) else 1
                    return maintenant - timedelta(weeks=weeks)
                elif "mois" in date_text:
                    months = int(''.join(filter(str.isdigit, date_text.split("mois")[0]))) if any(c.isdigit() for c in date_text) else 1
                    return maintenant - timedelta(days=months*30)
            
            return maintenant
        except:
            return datetime.now()
    
    def get_article_urls(self, section_url, max_articles=20):
        """Récupère les URLs des articles"""
        soup = self.make_request(section_url)
        if not soup:
            return []
        
        urls = []
        for article in soup.select('li.post-item h2.post-title a'):
            href = article.get('href')
            if href and href not in urls:
                urls.append(href)
            if len(urls) >= max_articles:
                break
        
        return urls[:max_articles]
    
    def scrape_article(self, url):
        """Scrape un article de Burkina24"""
        soup = self.make_request(url)
        if not soup:
            return None
        
        # TITRE
        titre = ''
        titre_tag = soup.find('h1', class_='post-title')
        if titre_tag:
            titre = html.unescape(titre_tag.get_text(strip=True))
        
        # DATE
        date = None
        date_tag = soup.find('span', class_='date')
        if date_tag:
            date_str = date_tag.get_text(strip=True)
            date = self.parse_relative_date(date_str)
        
        # Vérifier si on doit scraper cet article basé sur sa date
        if not self.should_scrape_article(date):
            return None
        
        # COMMENTAIRES
        commentaires = 0
        try:
            comments_tag = soup.find('span', class_='meta-comment')
            if comments_tag:
                comment_text = comments_tag.get_text(strip=True)
                commentaires = int(''.join(filter(str.isdigit, comment_text))) if comment_text else 0
        except:
            pass
        
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
