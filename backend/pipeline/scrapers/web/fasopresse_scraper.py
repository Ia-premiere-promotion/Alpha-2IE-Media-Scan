#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper pour fasopresse.net
"""

from .base_scraper import BaseWebScraper
import html

class FasoPresseScraper(BaseWebScraper):
    
    def __init__(self):
        super().__init__('FasoPresse', 'https://www.fasopresse.net')
        self.sections = {
            "Accueil": "https://www.fasopresse.net/accueil",
            "Politique": "https://www.fasopresse.net/politique",
            "Économie": "https://www.fasopresse.net/economie",
            "Société": "https://www.fasopresse.net/societe",
            "Santé et Social": "https://www.fasopresse.net/sante-et-social",
            "International": "https://www.fasopresse.net/international",
            "Sports": "https://www.fasopresse.net/sports",
        }
    
    def get_article_urls(self, section_url, max_articles=20):
        """Récupère les URLs des articles"""
        soup = self.make_request(section_url)
        if not soup:
            return []
        
        urls = []
        # FasoPresse utilise <a class="contentpagetitle"> pour les liens d'articles
        for link in soup.select('a.contentpagetitle, a.blogsection'):
            href = link.get('href')
            if href:
                # Supprimer les paramètres de session
                if '?' in href:
                    href = href.split('?')[0]
                # Convertir les liens relatifs en absolus
                if href.startswith('/'):
                    href = self.base_url + href
                if href not in urls and ('/politique/' in href or '/societe/' in href or '/economie/' in href or '/sports/' in href or '/sante-et-social/' in href or '/international/' in href or '/conseils-des-ministres/' in href):
                    urls.append(href)
            if len(urls) >= max_articles:
                break
        
        return urls[:max_articles]
    
    def scrape_article(self, url):
        """Scrape un article de FasoPresse"""
        soup = self.make_request(url)
        if not soup:
            return None
        
        # TITRE - Dans <a class="contentpagetitle"> ou <td class="contentheading">
        titre = ''
        titre_tag = soup.find('a', class_='contentpagetitle')
        if not titre_tag:
            titre_tag = soup.find('td', class_='contentheading')
            if titre_tag:
                titre_link = titre_tag.find('a')
                if titre_link:
                    titre = html.unescape(titre_link.get_text(strip=True))
        else:
            titre = html.unescape(titre_tag.get_text(strip=True))
        
        # DATE - Dans <td class="createdate">
        date = None
        date_tag = soup.find('td', class_='createdate')
        if date_tag:
            date_str = date_tag.get_text(strip=True)
            date = self.parse_french_date(date_str)
        
        # Vérifier si on doit scraper cet article basé sur sa date
        if not self.should_scrape_article(date):
            return None
        
        # AUTEUR - Dans <span class="small">Écrit par ...</span>
        auteur = None
        auteur_span = soup.find('span', class_='small')
        if auteur_span:
            texte_auteur = auteur_span.get_text(strip=True)
            if 'Écrit par' in texte_auteur:
                auteur = texte_auteur.replace('Écrit par', '').strip()
        
        # CONTENU - Dans les paragraphes de la 2ème table contentpaneopen
        contenu = ''
        content_tables = soup.find_all('table', class_='contentpaneopen')
        # Généralement la 2ème table contient le contenu de l'article
        if len(content_tables) >= 2:
            content_table = content_tables[1]
        elif content_tables:
            content_table = content_tables[0]
        else:
            content_table = None
            
        if content_table:
            # Chercher tous les <p> dans la table
            paragraphes = content_table.find_all('p')
            contenu_parts = []
            for p in paragraphes:
                texte = html.unescape(p.get_text(strip=True))
                if texte and len(texte) > 20:
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
