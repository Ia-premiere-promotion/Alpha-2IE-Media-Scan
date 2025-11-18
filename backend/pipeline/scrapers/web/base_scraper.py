#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Classe de base pour tous les scrapers web
Fournit les méthodes communes: requêtes HTTP, parsing de dates, etc.
"""

import requests
from bs4 import BeautifulSoup
import hashlib
from datetime import datetime
from abc import ABC, abstractmethod
import re

class BaseWebScraper(ABC):
    """Classe abstraite pour les scrapers web"""
    
    def __init__(self, media_name, base_url):
        self.media_name = media_name
        self.base_url = base_url
        self.timeout = 20
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        # Date de la dernière publication (sera initialisée par l'orchestrateur)
        self.last_publication_date = None
    
    def set_last_publication_date(self, last_date):
        """Définir la date de la dernière publication"""
        self.last_publication_date = last_date
    
    def should_scrape_article(self, article_date):
        """Vérifier si l'article doit être scrapé basé sur sa date"""
        if self.last_publication_date is None:
            return True
        
        if article_date is None:
            return True
        
        # Scraper si l'article est du même jour ou plus récent
        return article_date.date() >= self.last_publication_date.date()
    
    def make_request(self, url):
        """Effectue une requête HTTP avec gestion d'erreurs"""
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"❌ Erreur requête {url}: {e}")
            return None
    
    def generate_id(self, url):
        """Génère un ID unique basé sur l'URL"""
        return hashlib.sha256(url.encode()).hexdigest()
    
    def parse_french_date(self, date_str):
        """Parse une date en français vers datetime"""
        if not date_str:
            return datetime.now()
        
        mois_fr = {
            'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4,
            'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8,
            'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12
        }
        
        try:
            # Nettoyer la chaîne
            date_str = date_str.strip().lower()
            
            # Supprimer le jour de la semaine
            for jour in ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']:
                date_str = date_str.replace(jour, '').strip()
            
            # Remplacer "1er" par "1"
            date_str = date_str.replace('1er', '1')
            
            # Extraire: jour mois année
            parts = date_str.split()
            if len(parts) >= 3:
                jour = int(parts[0])
                mois_nom = parts[1]
                annee = int(parts[2])
                
                if mois_nom in mois_fr:
                    mois = mois_fr[mois_nom]
                    return datetime(annee, mois, jour)
        except:
            pass
        
        return datetime.now()
    
    def create_article_dict(self, url, titre, contenu, date=None, auteur=None, commentaires=0):
        """Crée un dictionnaire article standardisé"""
        return {
            'id': self.generate_id(url),
            'media': self.media_name,
            'titre': titre.strip() if titre else 'Sans titre',
            'date': date if date else datetime.now(),
            'url': url,
            'contenu': contenu.strip() if contenu else '',
            'categorie': None,  # Sera prédite par le modèle ML
            'likes': 0,
            'commentaires': commentaires,
            'partages': 0,
            'auteur': auteur,  # Colonne auteur réactivée
            'type_source': 'article',
            'plateforme': 'web'
        }
    
    @abstractmethod
    def get_article_urls(self, section_url, max_articles=20):
        """Méthode abstraite: récupérer les URLs des articles d'une section"""
        pass
    
    @abstractmethod
    def scrape_article(self, url):
        """Méthode abstraite: scraper un article complet"""
        pass
    
    def scrape_section(self, section_url, max_articles=20):
        """Scrape une section complète"""
        print(f"📰 Scraping: {section_url}")
        urls = self.get_article_urls(section_url, max_articles)
        print(f"   → {len(urls)} URLs trouvées")
        
        articles = []
        for url in urls:
            article = self.scrape_article(url)
            if article:
                articles.append(article)
        
        print(f"   ✅ {len(articles)} articles scrapés")
        return articles
