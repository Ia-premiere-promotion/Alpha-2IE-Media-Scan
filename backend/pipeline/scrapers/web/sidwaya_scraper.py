#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper pour sidwaya.info
"""

from .base_scraper import BaseWebScraper

class SidwayaScraper(BaseWebScraper):
    
    def __init__(self):
        super().__init__('Sidwaya', 'https://www.sidwaya.info')
        self.sections = {
            "A la Une": "https://www.sidwaya.info/category/a-la-une/",
            "Nation": "https://www.sidwaya.info/category/nation/",
            "Societe": "https://www.sidwaya.info/category/societe/",
            "Sport": "https://www.sidwaya.info/category/sport/",
            "Culture": "https://www.sidwaya.info/category/culture/",
            "Economie": "https://www.sidwaya.info/category/economie/",
            "International": "https://www.sidwaya.info/category/international/",
        }
    
    def get_article_urls(self, section_url, max_articles=20):
        """Récupère les URLs des articles"""
        soup = self.make_request(section_url)
        if not soup:
            return []
        
        urls = []
        for link in soup.select('h3.entry-title a, h2.post-title a'):
            href = link.get('href')
            if href and href not in urls:
                urls.append(href)
            if len(urls) >= max_articles:
                break
        
        return urls[:max_articles]
    
    def scrape_article(self, url):
        """Scrape un article de Sidwaya"""
        soup = self.make_request(url)
        if not soup:
            return None
        
        # TITRE
        titre = ''
        titre_tag = soup.find('h1', class_='entry-title')
        if titre_tag:
            titre = titre_tag.get_text(strip=True)
        
        # DATE - Dans span.td-post-date > time
        date = None
        date_span = soup.find('span', class_='td-post-date')
        if date_span:
            date_tag = date_span.find('time', class_='entry-date')
            if date_tag:
                date_str = date_tag.get('datetime')
                if date_str:
                    try:
                        from datetime import datetime
                        date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    except:
                        pass
        
        # Vérifier si on doit scraper cet article basé sur sa date
        if not self.should_scrape_article(date):
            return None
        
        # AUTEUR - Dans div.td-post-author-name > a
        auteur = None
        auteur_div = soup.find('div', class_='td-post-author-name')
        if auteur_div:
            auteur_tag = auteur_div.find('a')
            if auteur_tag:
                auteur = auteur_tag.get_text(strip=True)
        
        # CONTENU - Sur Sidwaya, le contenu principal est dans l'article après les métadonnées
        contenu = ''
        # Chercher d'abord dans article > p (structure principale)
        article_tag = soup.find('article')
        if article_tag:
            paragraphes = article_tag.find_all('p', recursive=True)
            # Exclure les paragraphes des sidebars et widgets
            contenu_parts = []
            for p in paragraphes:
                texte = p.get_text(strip=True)
                # Éviter les paragraphes vides et ceux des widgets/navigation
                if texte and len(texte) > 30 and not p.find_parent('aside') and not p.find_parent('nav'):
                    contenu_parts.append(texte)
            contenu = '\n\n'.join(contenu_parts)
        
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


if __name__ == "__main__":
    scraper = SidwayaScraper()
    articles = scraper.scrape_all_sections(max_articles_per_section=5)
    print(f"\n📊 Articles récupérés: {len(articles)}")
    if articles:
        print(f"Exemple: {articles[0]['titre'][:100]}...")
