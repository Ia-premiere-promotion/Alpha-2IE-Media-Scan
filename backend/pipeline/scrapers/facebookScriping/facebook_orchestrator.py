#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Orchestrateur du Pipeline Facebook
Transforme les JSON Facebook → CSV → Supabase
Similaire au pipeline Web mais adapté pour les posts Facebook
"""

import sys
import json
import csv
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Ajouter les paths pour imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ml.predictor import CategoryPredictor
from utils.cleaner import DataCleaner
from utils.db_writer import DatabaseWriter
from supabase_client import get_supabase_client


class FacebookOrchestrator:
    """Orchestre le traitement des données Facebook"""
    
    def __init__(self, json_source='consolidated'):
        """
        Initialise l'orchestrateur
        
        Args:
            json_source: 'consolidated' pour all_media_consolidated.json
                        ou 'individual' pour les JSON séparés
        """
        print(f"\n{'='*70}")
        print(f"📘 PIPELINE FACEBOOK - TRAITEMENT DES POSTS")
        print(f"{'='*70}")
        print(f"Démarré: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        self.base_path = Path(__file__).parent
        self.json_source = json_source
        
        # Initialiser les modules
        self.supabase = get_supabase_client()
        self.predictor = CategoryPredictor()
        self.cleaner = DataCleaner()
        self.db_writer = DatabaseWriter()
        
        # Mapping des noms Facebook → Supabase (pour gérer les variations)
        self.media_name_mapping = {
            'Burkina24': 'Burkina24',
            'Lefaso.net': 'LeFaso',
            'lefaso.net': 'LeFaso',
            'Lefaso': 'LeFaso',
            'LeFaso.net': 'LeFaso',
            'Fasopresse': 'FasoPresse',
            'ESidwaya': 'Sidwaya',
            'E-Sidwaya': 'Sidwaya',
            'Observateur Paalga': "L'Observateur Paalga",
            "L'Observateur Paalga": "L'Observateur Paalga",
            'Observateur': "L'Observateur Paalga"
        }
        
        # Statistiques
        self.stats = {
            'total_posts': 0,
            'total_transformed': 0,
            'total_cleaned': 0,
            'total_inserted': 0,
            'total_skipped': 0,
            'total_errors': 0
        }
        
        # Détails par média
        self.media_stats = {}
        
        # ID du log
        self.scraping_log_id = None
    
    def read_json_data(self) -> List[Dict]:
        """
        Lit les données JSON (consolidated ou individual)
        
        Returns:
            Liste de posts bruts
        """
        print(f"\n{'='*70}")
        print(f"📂 ÉTAPE 1: LECTURE DES JSON")
        print(f"{'='*70}\n")
        
        all_posts = []
        
        if self.json_source == 'consolidated':
            # Lire all_media_consolidated.json
            json_file = self.base_path / 'all_media_consolidated.json'
            
            if not json_file.exists():
                print(f"❌ Fichier non trouvé: {json_file}")
                return []
            
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                all_posts = data.get('all_posts', [])
                print(f"✅ {len(all_posts)} posts chargés depuis {json_file.name}")
                
                # Stats par média
                media_stats = data.get('media_stats', {})
                for media_name, stats in media_stats.items():
                    print(f"   📊 {media_name}: {stats.get('total_posts', 0)} posts")
                
            except Exception as e:
                print(f"❌ Erreur lecture JSON: {e}")
                return []
        
        else:
            # Lire les JSON individuels
            json_files = {
                'Burkina24': 'facebook_burkina24/burkina24_realtime.json',
                'Lefaso.net': 'facebook_fasonet/lefaso_realtime.json',
                'Fasopresse': 'facebook_fasopresse/fasopresse_realtime.json',
                'ESidwaya': 'faccebook_sidwaya/esidwaya_realtime.json',
                'Observateur Paalga': 'facebook_observateurpaalga/observateur_paalga_stream.json'
            }
            
            for media_name, json_path in json_files.items():
                file_path = self.base_path / json_path
                
                if not file_path.exists():
                    print(f"⚠️  {media_name}: fichier non trouvé ({json_path})")
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    posts = data.get('posts', [])
                    
                    # Ajouter le nom du média
                    for post in posts:
                        post['media_source'] = media_name
                    
                    all_posts.extend(posts)
                    print(f"✅ {media_name}: {len(posts)} posts")
                    
                except Exception as e:
                    print(f"❌ Erreur {media_name}: {e}")
        
        self.stats['total_posts'] = len(all_posts)
        print(f"\n✅ Total: {len(all_posts)} posts chargés")
        
        return all_posts
    
    def transform_posts(self, posts: List[Dict]) -> List[Dict]:
        """
        Transforme les posts Facebook en format compatible BD
        
        Args:
            posts: Posts Facebook bruts
            
        Returns:
            Articles transformés
        """
        print(f"\n{'='*70}")
        print(f"🔄 ÉTAPE 2: TRANSFORMATION DES POSTS")
        print(f"{'='*70}\n")
        
        articles = []
        
        for post in posts:
            try:
                # Extraction du titre (premiers 100 caractères du contenu)
                contenu = post.get('contenu', '')
                titre = contenu[:100] + '...' if len(contenu) > 100 else contenu
                
                # Extraction du média avec mapping
                media_name_raw = post.get('media_source', 'Unknown')
                media_name = self.media_name_mapping.get(media_name_raw, media_name_raw)
                
                # Créer l'article transformé
                article = {
                    'id': post.get('post_id'),
                    'media': media_name,
                    'titre': titre,
                    'contenu': contenu,
                    'url': post.get('url', ''),
                    'date': self._parse_date(post.get('date_post')),
                    'categorie': None,  # Sera défini par ML
                    'type_source': 'post',
                    'plateforme': 'facebook',
                    'likes': post.get('likes', 0),
                    'commentaires': post.get('comments', 0),  # Nombre
                    'partages': post.get('shares', 0),
                    'commentaire_text': post.get('commentaires', [])  # Array JSON
                }
                
                articles.append(article)
                
            except Exception as e:
                print(f"⚠️  Erreur transformation post: {e}")
                self.stats['total_errors'] += 1
                continue
        
        self.stats['total_transformed'] = len(articles)
        print(f"✅ {len(articles)} posts transformés")
        
        return articles
    
    def _parse_date(self, date_str):
        """Parse une date ISO"""
        if not date_str:
            return datetime.now()
        
        try:
            # Format: 2025-11-17T15:23:32.208432
            if isinstance(date_str, str):
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return date_str
        except:
            return datetime.now()
    
    def run_prediction(self, articles: List[Dict]) -> List[Dict]:
        """
        Prédiction ML des catégories
        
        Args:
            articles: Liste d'articles
            
        Returns:
            Articles avec catégories prédites
        """
        print(f"\n{'='*70}")
        print(f"🤖 ÉTAPE 3: PRÉDICTION DES CATÉGORIES (ML)")
        print(f"{'='*70}")
        
        articles = self.predictor.predict_batch(articles)
        
        return articles
    
    def run_cleaning(self, articles: List[Dict]) -> List[Dict]:
        """
        Nettoyage et validation
        
        Args:
            articles: Articles à nettoyer
            
        Returns:
            Articles nettoyés
        """
        print(f"\n{'='*70}")
        print(f"🧹 ÉTAPE 4: NETTOYAGE ET VALIDATION")
        print(f"{'='*70}")
        
        # Nettoyer
        articles = self.cleaner.clean_batch(articles)
        
        # Supprimer les doublons
        articles = self.cleaner.deduplicate(articles)
        
        self.stats['total_cleaned'] = len(articles)
        
        return articles
    
    def cleanup_temp_csv(self, csv_path: str):
        """
        Supprime un fichier CSV temporaire
        
        Args:
            csv_path: Chemin du fichier à supprimer
        """
        try:
            if os.path.exists(csv_path):
                os.remove(csv_path)
                print(f"🗑️  Fichier temporaire supprimé: {os.path.basename(csv_path)}")
        except Exception as e:
            print(f"⚠️  Erreur suppression {csv_path}: {e}")
    
    def export_to_csv(self, articles: List[Dict], filename: str) -> str:
        """
        Exporte en CSV
        
        Args:
            articles: Articles à exporter
            filename: Nom du fichier
            
        Returns:
            Chemin du fichier créé
        """
        csv_path = self.base_path / filename
        
        fieldnames = [
            'id', 'media', 'titre', 'contenu', 'url', 'date', 
            'categorie', 'type_source', 'plateforme',
            'likes', 'commentaires', 'partages'
        ]
        
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for article in articles:
                    row = {
                        'id': article.get('id', ''),
                        'media': article.get('media', ''),
                        'titre': article.get('titre', '').replace('\n', ' ')[:100],
                        'contenu': article.get('contenu', '').replace('\n', ' '),
                        'url': article.get('url', ''),
                        'date': article['date'].isoformat() if hasattr(article.get('date'), 'isoformat') else str(article.get('date')),
                        'categorie': article.get('categorie', ''),
                        'type_source': article.get('type_source', 'post'),
                        'plateforme': article.get('plateforme', 'facebook'),
                        'likes': article.get('likes', 0),
                        'commentaires': article.get('commentaires', 0),
                        'partages': article.get('partages', 0)
                    }
                    writer.writerow(row)
            
            print(f"✅ CSV exporté: {csv_path}")
            return str(csv_path)
            
        except Exception as e:
            print(f"❌ Erreur export CSV: {e}")
            return None
    
    def run_insertion(self, articles: List[Dict]):
        """
        Insertion dans Supabase
        
        Args:
            articles: Articles à insérer
        """
        print(f"\n{'='*70}")
        print(f"💾 ÉTAPE 5: INSERTION DANS SUPABASE")
        print(f"{'='*70}")
        
        stats = self.db_writer.insert_batch(articles)
        
        self.stats['total_inserted'] = stats['inserted']
        self.stats['total_skipped'] = stats['skipped']
        self.stats['total_errors'] += stats['errors']
        
        return stats
    
    def run_full_pipeline(self):
        """Exécute le pipeline complet"""
        start_time = datetime.now()
        
        try:
            # 1. Lecture JSON
            posts = self.read_json_data()
            
            if not posts:
                print("\n⚠️  Aucun post trouvé. Arrêt.")
                return self.stats
            
            # 2. Transformation
            articles = self.transform_posts(posts)
            
            if not articles:
                print("\n⚠️  Aucun article transformé. Arrêt.")
                return self.stats
            
            # 3. Prédiction ML
            articles = self.run_prediction(articles)
            
            # 4. Nettoyage
            articles = self.run_cleaning(articles)
            
            if not articles:
                print("\n⚠️  Aucun article valide après nettoyage. Arrêt.")
                return self.stats
            
            # 5. Export CSV brut
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            csv_brut = self.export_to_csv(articles, f'facebook_posts_brut_{timestamp}.csv')
            
            # 6. Validation stricte
            print(f"\n{'='*70}")
            print(f"🔧 VALIDATION STRICTE SELON SCHÉMA BD")
            print(f"{'='*70}\n")
            
            validated_articles = []
            for article in articles:
                cleaned = self.db_writer.clean_article_for_db(article)
                is_valid, error_msg = self.db_writer.validate_article_for_db(cleaned)
                
                if is_valid:
                    validated_articles.append(cleaned)
            
            print(f"✅ Articles validés: {len(validated_articles)}/{len(articles)}")
            
            # 7. Export CSV validé
            if validated_articles:
                csv_valide = self.export_to_csv(validated_articles, f'facebook_posts_valides_{timestamp}.csv')
            
            # 8. Insertion BD
            if validated_articles:
                self.run_insertion(validated_articles)
            else:
                print("\n⚠️  Aucun article valide pour insertion.")
        
        except Exception as e:
            print(f"\n❌ ERREUR CRITIQUE: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Résumé
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print(f"\n{'='*70}")
            print(f"📊 RÉSUMÉ DU PIPELINE FACEBOOK")
            print(f"{'='*70}")
            print(f"Durée: {duration:.1f}s")
            print(f"\n📊 Statistiques:")
            print(f"  📘 Posts chargés: {self.stats['total_posts']}")
            print(f"  🔄 Posts transformés: {self.stats['total_transformed']}")
            print(f"  ✅ Posts nettoyés: {self.stats['total_cleaned']}")
            print(f"  💾 Posts insérés: {self.stats['total_inserted']}")
            print(f"  ⏭️  Posts ignorés (doublons): {self.stats['total_skipped']}")
            if self.stats['total_errors'] > 0:
                print(f"  ❌ Erreurs: {self.stats['total_errors']}")
            
            success_rate = (self.stats['total_inserted'] / self.stats['total_posts'] * 100) if self.stats['total_posts'] > 0 else 0
            print(f"\n  🎯 Taux de réussite: {success_rate:.1f}%")
            
            print(f"\n{'='*70}")
            print(f"🎉 PIPELINE FACEBOOK TERMINÉ")
            print(f"{'='*70}\n")
            
            # Nettoyage des fichiers CSV temporaires
            print(f"\n🧹 Nettoyage des fichiers temporaires...")
            if 'csv_brut' in locals():
                self.cleanup_temp_csv(csv_brut)
            if 'csv_valide' in locals():
                self.cleanup_temp_csv(csv_valide)
            print(f"✅ Nettoyage terminé\n")
        
        return self.stats


def main():
    """Point d'entrée principal"""
    orchestrator = FacebookOrchestrator(json_source='consolidated')
    stats = orchestrator.run_full_pipeline()
    return stats


if __name__ == "__main__":
    main()
