#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestionnaire de dates pour éviter les doublons
Récupère la dernière date de publication par média
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Ajouter le path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from supabase_client import get_supabase_client


class DateManager:
    """Gère les dates de dernière publication par média"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        self.last_dates = {}
        self._load_last_dates()
    
    def _load_last_dates(self):
        """Charge la dernière date de publication pour chaque média"""
        try:
            # Récupérer tous les médias
            medias_result = self.supabase.table('medias').select('id, name').execute()
            
            for media in medias_result.data:
                media_id = media['id']
                media_name = media['name']
                
                # Récupérer le dernier article de ce média
                result = self.supabase.table('articles')\
                    .select('date')\
                    .eq('media_id', media_id)\
                    .order('date', desc=True)\
                    .limit(1)\
                    .execute()
                
                if result.data:
                    last_date_str = result.data[0]['date']
                    last_date = datetime.fromisoformat(last_date_str.replace('Z', '+00:00'))
                    self.last_dates[media_name] = last_date
                    
                    # Normaliser aussi pour les variations du nom
                    normalized = media_name.lower().replace(' ', '').replace('.', '')
                    self.last_dates[normalized] = last_date
                else:
                    # Pas d'articles pour ce média, prendre il y a 7 jours
                    self.last_dates[media_name] = datetime.now() - timedelta(days=7)
            
            print(f"✅ Dates de dernière publication chargées:")
            for media_name, date in self.last_dates.items():
                if '.' in media_name or ' ' in media_name:  # Afficher seulement les noms originaux
                    print(f"   - {media_name}: {date.strftime('%Y-%m-%d %H:%M')}")
            
        except Exception as e:
            print(f"❌ Erreur chargement dates: {e}")
    
    def get_last_date(self, media_name):
        """
        Récupère la dernière date de publication d'un média
        
        Args:
            media_name: Nom du média
        
        Returns:
            datetime: Dernière date ou date par défaut (il y a 7 jours)
        """
        # Essayer plusieurs variations du nom
        variations = [
            media_name,
            media_name.lower().replace(' ', '').replace('.', ''),
            media_name.lower(),
            media_name.capitalize()
        ]
        
        for var in variations:
            if var in self.last_dates:
                return self.last_dates[var]
        
        # Par défaut: il y a 7 jours
        return datetime.now() - timedelta(days=7)
    
    def is_newer_than_last(self, media_name, article_date):
        """
        Vérifie si un article est plus récent que le dernier en base
        
        Args:
            media_name: Nom du média
            article_date: Date de l'article
        
        Returns:
            bool: True si l'article est plus récent
        """
        if not article_date:
            return False
        
        last_date = self.get_last_date(media_name)
        
        # Convertir article_date en datetime si c'est une string
        if isinstance(article_date, str):
            try:
                article_date = datetime.fromisoformat(article_date.replace('Z', '+00:00'))
            except:
                return False
        
        # L'article doit être du même jour ou plus récent
        return article_date >= last_date.replace(hour=0, minute=0, second=0, microsecond=0)


if __name__ == "__main__":
    # Test
    dm = DateManager()
    print(f"\nTest pour lefaso.net: {dm.get_last_date('lefaso.net')}")
    
    # Test si une date est plus récente
    test_date = datetime.now()
    print(f"Article d'aujourd'hui est nouveau? {dm.is_newer_than_last('lefaso.net', test_date)}")
