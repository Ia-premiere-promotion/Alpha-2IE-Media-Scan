#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module d'insertion des articles dans Supabase
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire parent au path pour importer supabase_client
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from supabase_client import get_supabase_client

class DatabaseWriter:
    """Gère l'insertion des articles dans Supabase"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        self.media_ids = self._load_media_ids()
        self.category_ids = self._load_category_ids()
    
    def _load_media_ids(self):
        """Charge la correspondance nom_media → id"""
        try:
            result = self.supabase.table('medias').select('id, name').execute()
            mapping = {}
            for media in result.data:
                # Normaliser les noms pour la correspondance
                name_normalized = media['name'].lower().replace(' ', '').replace('.', '')
                mapping[name_normalized] = media['id']
                # Aussi avec le nom original
                mapping[media['name']] = media['id']
            print(f"✅ {len(result.data)} médias chargés")
            return mapping
        except Exception as e:
            print(f"❌ Erreur chargement médias: {e}")
            return {}
    
    def _load_category_ids(self):
        """Charge la correspondance nom_categorie → id"""
        try:
            result = self.supabase.table('categories').select('id, nom').execute()
            mapping = {}
            for cat in result.data:
                # Normaliser pour correspondance insensible à la casse
                name_normalized = cat['nom'].lower()
                mapping[name_normalized] = cat['id']
                mapping[cat['nom']] = cat['id']
            print(f"✅ {len(result.data)} catégories chargées")
            return mapping
        except Exception as e:
            print(f"❌ Erreur chargement catégories: {e}")
            return {}
    
    def get_media_id(self, media_name):
        """Récupère l'ID d'un média par son nom"""
        if not media_name:
            return None
        
        # Essayer plusieurs variations du nom
        variations = [
            media_name,
            media_name.lower().replace(' ', '').replace('.', ''),
            media_name.lower()
        ]
        
        for var in variations:
            if var in self.media_ids:
                return self.media_ids[var]
        
        print(f"⚠️ Média non trouvé: {media_name}")
        return None
    
    def get_category_id(self, category_name):
        """Récupère l'ID d'une catégorie par son nom"""
        if not category_name:
            return None
        
        # Essayer plusieurs variations
        variations = [
            category_name,
            category_name.lower(),
            category_name.capitalize()
        ]
        
        for var in variations:
            if var in self.category_ids:
                return self.category_ids[var]
        
        # Catégorie par défaut "Autre"
        return self.category_ids.get('autre') or self.category_ids.get('Autre')
    
    def article_exists(self, article_url):
        """Vérifie si un article existe déjà dans la DB"""
        try:
            result = self.supabase.table('articles').select('id').eq('url', article_url).execute()
            return len(result.data) > 0
        except:
            return False
    
    def validate_article_for_db(self, article):
        """
        Valide strictement qu'un article est compatible avec la base de données
        
        Args:
            article: Dictionnaire avec les données de l'article
        
        Returns:
            tuple: (is_valid, error_message)
        """
        # Vérifier les champs obligatoires (selon schéma BD)
        # Seuls id, media_id et titre sont vraiment obligatoires (NOT NULL)
        required_fields = ['id', 'media', 'titre']
        for field in required_fields:
            if field not in article or not article[field]:
                return False, f"Champ obligatoire manquant: {field}"
        
        # Vérifier que contenu OU url est présent (au moins un des deux)
        if (not article.get('contenu') or len(str(article.get('contenu', '')).strip()) == 0) and \
           (not article.get('url') or len(str(article.get('url', '')).strip()) == 0):
            return False, "L'article doit avoir au moins un contenu ou une URL"
        
        # Valider l'ID
        if not isinstance(article['id'], str) or len(article['id']) < 10:
            return False, "ID invalide (doit être une chaîne de >10 caractères)"
        
        # Valider le média
        media_id = self.get_media_id(article['media'])
        if not media_id:
            return False, f"Média non trouvé: {article['media']}"
        
        # Valider le titre (NOT NULL dans la BD)
        if not isinstance(article['titre'], str) or len(article['titre'].strip()) < 5:
            return False, "Titre trop court (<5 caractères)"
        
        # Valider le contenu (si présent)
        if article.get('contenu'):
            if not isinstance(article['contenu'], str) or len(article['contenu'].strip()) < 10:
                return False, "Contenu trop court (<10 caractères)"
        
        # Valider l'URL (si présente)
        if article.get('url'):
            if not isinstance(article['url'], str) or not (article['url'].startswith('http://') or article['url'].startswith('https://')):
                return False, "URL invalide (doit commencer par http:// ou https://)"
        
        # Valider la date (si présente)
        if article.get('date'):
            try:
                if hasattr(article['date'], 'isoformat'):
                    date_str = article['date'].isoformat()
                else:
                    date_str = str(article['date'])
                
                # Vérifier le format de date
                if 'T' not in date_str and '-' not in date_str:
                    return False, "Format de date invalide"
            except:
                return False, "Date non convertible"
        
        # Valider les métriques (doivent être des entiers >= 0)
        for metric in ['likes', 'commentaires', 'partages']:
            value = article.get(metric, 0)
            try:
                int_value = int(value)
                if int_value < 0:
                    return False, f"{metric} ne peut pas être négatif"
            except:
                return False, f"{metric} doit être un nombre entier (reçu: {type(value).__name__})"
        
        # 8. TYPE_SOURCE et PLATEFORME - optionnels
        if article.get('type_source'):
            if article['type_source'] not in ['article', 'post', 'video', 'image']:
                return False, f"type_source invalide: {article['type_source']} (doit être: article, post, video, ou image)"
        
        if article.get('plateforme'):
            if article['plateforme'] not in ['web', 'facebook', 'twitter', 'instagram']:
                return False, f"plateforme invalide: {article['plateforme']} (doit être: web, facebook, twitter, ou instagram)"
        
        # ===== TOUT EST VALIDE =====
        return True, None
    
    def clean_article_for_db(self, article):
        """
        Nettoie et formate un article pour être 100% conforme à la BD
        Supprime les espaces, caractères invalides, etc.
        
        Args:
            article: Dictionnaire avec les données de l'article
        
        Returns:
            dict: Article nettoyé
        """
        cleaned = {}
        
        # ID - nettoyé
        cleaned['id'] = str(article['id']).strip()
        
        # Média - nettoyé
        cleaned['media'] = str(article['media']).strip()
        
        # Titre - nettoyé (supprimer espaces multiples, sauts de ligne, etc.)
        titre = str(article['titre']).strip()
        titre = ' '.join(titre.split())  # Supprimer espaces multiples
        titre = titre.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        cleaned['titre'] = titre[:500]  # Limiter à 500 chars
        
        # Contenu - nettoyé
        if article.get('contenu'):
            contenu = str(article['contenu']).strip()
            contenu = contenu.replace('\r\n', '\n').replace('\r', '\n')
            # Supprimer les lignes vides multiples
            lines = [line.strip() for line in contenu.split('\n') if line.strip()]
            contenu = '\n'.join(lines)
            cleaned['contenu'] = contenu
        else:
            cleaned['contenu'] = None
        
        # URL - nettoyée
        if article.get('url'):
            url = str(article['url']).strip()
            # Supprimer espaces
            url = url.replace(' ', '')
            cleaned['url'] = url[:1000]  # Limiter à 1000 chars
        else:
            cleaned['url'] = None
        
        # Date - formatée
        if article.get('date'):
            if hasattr(article['date'], 'isoformat'):
                cleaned['date'] = article['date']
            else:
                cleaned['date'] = str(article['date']).strip()
        else:
            cleaned['date'] = None
        
        # Catégorie - nettoyée
        if article.get('categorie'):
            cleaned['categorie'] = str(article['categorie']).strip().capitalize()
        else:
            cleaned['categorie'] = None
        
        # Métriques - nettoyées (convertir en int)
        cleaned['likes'] = int(article.get('likes', 0))
        cleaned['commentaires'] = int(article.get('commentaires', 0))
        cleaned['partages'] = int(article.get('partages', 0))
        
        # Type source et plateforme
        cleaned['type_source'] = article.get('type_source', 'article')
        cleaned['plateforme'] = article.get('plateforme', 'web')
        
        return cleaned

    def insert_article(self, article):
        """
        Insère un article dans la base de données
        
        Args:
            article: Dictionnaire avec les données de l'article
        
        Returns:
            str: ID de l'article inséré ou None si erreur
        """
        try:
            # Validation stricte avant insertion
            is_valid, error_msg = self.validate_article_for_db(article)
            if not is_valid:
                print(f"⚠️ Article rejeté: {error_msg} - '{article.get('titre', '')[:40]}...'")
                return None
            
            # Vérifier si l'article existe déjà
            if self.article_exists(article['url']):
                # print(f"⏭️  Article déjà existant: {article['titre'][:50]}...")
                return None
            
            # Récupérer les IDs
            media_id = self.get_media_id(article['media'])
            if not media_id:
                print(f"❌ Média invalide pour: {article['titre'][:50]}...")
                return None
            
            category_id = self.get_category_id(article.get('categorie'))
            
            # Préparer les données pour l'insertion (selon schéma BD exact)
            article_data = {
                'id': article['id'],
                'media_id': media_id,
                'titre': article['titre'],
                'contenu': article.get('contenu') if article.get('contenu') else None,
                'url': article.get('url') if article.get('url') else None,
                'date': article['date'].isoformat() if hasattr(article.get('date'), 'isoformat') else (str(article['date']) if article.get('date') else None),
                'categorie_id': category_id
            }
            
            # Insérer l'article
            result = self.supabase.table('articles').insert(article_data).execute()
            
            if result.data:
                article_id = result.data[0]['id']
                
                # Insérer les engagements si présents
                if article.get('likes', 0) > 0 or article.get('commentaires', 0) > 0 or article.get('partages', 0) > 0:
                    self.insert_engagement(
                        article_id,
                        article.get('likes', 0),
                        article.get('commentaires', 0),
                        article.get('partages', 0),
                        article.get('type_source', 'article'),
                        article.get('plateforme', 'web')
                    )
                
                return article_id
            
            return None
        
        except Exception as e:
            print(f"❌ Erreur insertion article '{article.get('titre', '')[:50]}...': {e}")
            return None
    
    def insert_engagement(self, article_id, likes, commentaires, partages, type_source=None, plateforme=None):
        """Insère ou met à jour les engagements d'un article"""
        try:
            engagement_data = {
                'article_id': article_id,
                'likes': likes,
                'commentaires': commentaires,
                'partages': partages,
                'type_source': type_source,
                'plateforme': plateforme
            }
            
            # Vérifier si engagement existe déjà
            existing = self.supabase.table('engagements').select('*').eq('article_id', article_id).execute()
            
            if existing.data:
                # Update
                self.supabase.table('engagements').update(engagement_data).eq('article_id', article_id).execute()
            else:
                # Insert
                self.supabase.table('engagements').insert(engagement_data).execute()
            
            return True
        except Exception as e:
            print(f"❌ Erreur insertion engagement: {e}")
            return False
    
    def insert_batch(self, articles):
        """
        Insère une liste d'articles dans la base
        
        Args:
            articles: Liste de dictionnaires
        
        Returns:
            dict: Statistiques d'insertion avec détails par média
        """
        print(f"\n💾 Insertion de {len(articles)} articles dans Supabase...")
        
        inserted = 0
        skipped = 0
        errors = 0
        
        # Stats par média
        media_stats = {}
        
        for article in articles:
            media_name = article.get('media', 'Inconnu')
            
            # Initialiser les stats pour ce média si nécessaire
            if media_name not in media_stats:
                media_stats[media_name] = {
                    'inserted': 0,
                    'skipped': 0,
                    'errors': 0
                }
            
            result = self.insert_article(article)
            if result:
                inserted += 1
                media_stats[media_name]['inserted'] += 1
            elif self.article_exists(article['url']):
                skipped += 1
                media_stats[media_name]['skipped'] += 1
            else:
                errors += 1
                media_stats[media_name]['errors'] += 1
        
        stats = {
            'inserted': inserted,
            'skipped': skipped,
            'errors': errors,
            'total': len(articles),
            'by_media': media_stats
        }
        
        print(f"✅ Insertion terminée:")
        print(f"   - Insérés: {inserted}")
        print(f"   - Ignorés (doublons): {skipped}")
        if errors > 0:
            print(f"   - Erreurs: {errors}")
        
        return stats


if __name__ == "__main__":
    # Test
    writer = DatabaseWriter()
    print(f"\nMédias disponibles: {list(writer.media_ids.keys())[:5]}...")
    print(f"Catégories disponibles: {list(writer.category_ids.keys())[:5]}...")
