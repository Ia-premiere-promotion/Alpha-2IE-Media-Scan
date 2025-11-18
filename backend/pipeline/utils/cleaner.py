#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de nettoyage et validation des données scrapées
"""

import re
from datetime import datetime

class DataCleaner:
    """Nettoie et valide les données avant insertion dans la DB"""
    
    @staticmethod
    def clean_text(text):
        """Nettoie un texte (titre ou contenu)"""
        if not text or not isinstance(text, str):
            return ''
        
        # Supprimer les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        
        # Supprimer les retours à la ligne multiples
        text = re.sub(r'\n\n+', '\n\n', text)
        
        # Supprimer les caractères spéciaux inutiles
        text = text.replace('\r', '')
        text = text.replace('\t', ' ')
        
        # Trim
        text = text.strip()
        
        return text
    
    @staticmethod
    def validate_url(url):
        """Valide qu'une URL est correcte"""
        if not url or not isinstance(url, str):
            return False
        
        # Doit commencer par http:// ou https://
        if not (url.startswith('http://') or url.startswith('https://')):
            return False
        
        # Doit avoir un domaine
        if len(url) < 10:
            return False
        
        return True
    
    @staticmethod
    def validate_date(date):
        """Valide et formate une date"""
        if isinstance(date, datetime):
            return date
        
        if isinstance(date, str):
            try:
                return datetime.fromisoformat(date.replace('Z', '+00:00'))
            except:
                pass
        
        # Date par défaut
        return datetime.now()
    
    @staticmethod
    def clean_article(article):
        """
        Nettoie un article complet
        
        Args:
            article: Dictionnaire avec les données de l'article
        
        Returns:
            Dictionnaire nettoyé ou None si invalide
        """
        if not article or not isinstance(article, dict):
            return None
        
        # Nettoyer le titre
        titre = DataCleaner.clean_text(article.get('titre', ''))
        if not titre or len(titre) < 10:
            return None  # Titre trop court ou manquant
        
        # Nettoyer le contenu
        contenu = DataCleaner.clean_text(article.get('contenu', ''))
        if not contenu or len(contenu) < 50:
            contenu = titre  # Si pas de contenu, utiliser le titre
        
        # Valider l'URL
        url = article.get('url', '')
        if not DataCleaner.validate_url(url):
            return None
        
        # Valider la date
        date = DataCleaner.validate_date(article.get('date'))
        
        # S'assurer que les nombres sont bien des entiers
        likes = int(article.get('likes', 0) or 0)
        commentaires = int(article.get('commentaires', 0) or 0)
        partages = int(article.get('partages', 0) or 0)
        
        # Article nettoyé
        cleaned = {
            'id': article.get('id', ''),
            'media': article.get('media', ''),
            'titre': titre,
            'date': date,
            'url': url,
            'contenu': contenu,
            'categorie': article.get('categorie'),
            'likes': likes,
            'commentaires': commentaires,
            'partages': partages,
            'auteur': DataCleaner.clean_text(article.get('auteur', '') or ''),
            'type_source': article.get('type_source', 'article'),
            'plateforme': article.get('plateforme', 'web')
        }
        
        return cleaned
    
    @staticmethod
    def clean_batch(articles):
        """
        Nettoie une liste d'articles
        
        Args:
            articles: Liste de dictionnaires
        
        Returns:
            Liste d'articles nettoyés (peut être plus courte si certains sont invalides)
        """
        print(f"\n🧹 Nettoyage de {len(articles)} articles...")
        
        cleaned_articles = []
        invalid_count = 0
        
        for article in articles:
            cleaned = DataCleaner.clean_article(article)
            if cleaned:
                cleaned_articles.append(cleaned)
            else:
                invalid_count += 1
        
        print(f"✅ {len(cleaned_articles)} articles valides")
        if invalid_count > 0:
            print(f"⚠️  {invalid_count} articles rejetés (invalides)")
        
        return cleaned_articles
    
    @staticmethod
    def deduplicate(articles):
        """
        Supprime les doublons basés sur l'URL
        
        Args:
            articles: Liste d'articles
        
        Returns:
            Liste sans doublons
        """
        seen_urls = set()
        unique_articles = []
        duplicates = 0
        
        for article in articles:
            url = article.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)
            else:
                duplicates += 1
        
        if duplicates > 0:
            print(f"🔄 {duplicates} doublons supprimés")
        
        return unique_articles


if __name__ == "__main__":
    # Test
    test_articles = [
        {
            'id': '123',
            'media': 'Test',
            'titre': '   Article   de   test   ',
            'contenu': 'Contenu  avec   espaces   multiples\n\n\n\nEt retours à la ligne',
            'date': '2025-11-17T10:00:00Z',
            'url': 'https://example.com/article',
            'likes': '10',
            'commentaires': None,
            'auteur': '  Auteur Test  '
        },
        {
            'titre': 'Titre trop court',
            'contenu': 'x',
            'url': 'invalid-url'
        }
    ]
    
    cleaned = DataCleaner.clean_batch(test_articles)
    print(f"\nArticles nettoyés: {len(cleaned)}")
    if cleaned:
        print(f"Exemple: {cleaned[0]}")
