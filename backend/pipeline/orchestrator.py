#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Orchestrateur principal du pipeline de scraping
Coordonne: Scraping (Web + Facebook) → ML Prediction → Cleaning → Database Insertion → CSV Export
"""

import sys
import os
import csv
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Charger variables d'environnement
load_dotenv()

# Ajouter le path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Importations des modules du pipeline
from scrapers.web.lefaso_scraper import LeFasoScraper
from scrapers.web.sidwaya_scraper import SidwayaScraper
from scrapers.web.fasopresse_scraper import FasoPresseScraper
from scrapers.web.observateur_scraper import ObservateurScraper
from scrapers.web.burkina24_scraper import Burkina24Scraper
# Facebook scraper retiré - on utilise les JSON déjà scrapés
from ml.predictor import CategoryPredictor
from utils.cleaner import DataCleaner
from utils.db_writer import DatabaseWriter
from utils.date_manager import DateManager
from supabase_client import get_supabase_client


class PipelineOrchestrator:
    """Orchestre l'exécution complète du pipeline de scraping"""
    
    def __init__(self, include_facebook=False):
        print(f"\n{'='*70}")
        print(f"🚀 PIPELINE DE SCRAPING AUTOMATIQUE - MONITORING MÉDIATIQUE")
        print(f"{'='*70}")
        print(f"Démarré: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Initialiser le client Supabase
        self.supabase = get_supabase_client()
        
        # Initialiser le gestionnaire de dates
        self.date_manager = DateManager()
        
        # Initialiser les scrapers WEB
        self.scrapers = [
            LeFasoScraper(),
            SidwayaScraper(),
            FasoPresseScraper(),
            ObservateurScraper(),
            Burkina24Scraper()
        ]
        
        # Facebook scraping désactivé - on utilise les JSON déjà générés
        self.include_facebook = False
        self.facebook_scraper = None
        
        # Configurer la date de dernière publication pour chaque scraper web
        for scraper in self.scrapers:
            last_date = self.date_manager.get_last_date(scraper.media_name)
            scraper.set_last_publication_date(last_date)
            print(f"📅 {scraper.media_name}: Dernière publication = {last_date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Initialiser les modules
        self.predictor = CategoryPredictor()
        self.cleaner = DataCleaner()
        self.db_writer = DatabaseWriter()
        
        # Statistiques
        self.stats = {
            'total_scraped': 0,
            'total_cleaned': 0,
            'total_inserted': 0,
            'total_skipped': 0,
            'total_errors': 0
        }
        
        # Détails par média (pour scraping_media_details)
        self.media_stats = {}
        
        # ID du log en cours (pour enregistrement en BD)
        self.scraping_log_id = None
        
        # Liste des fichiers CSV temporaires créés (pour suppression auto)
        self.temp_csv_files = []
    
    def run_scraping(self, max_articles_per_section=20, facebook_max_posts=50):
        """
        Étape 1: Scrape tous les médias (Web + Facebook)
        
        Args:
            max_articles_per_section: Nombre max d'articles par section (web)
            facebook_max_posts: Nombre max de posts Facebook
        
        Returns:
            Liste d'articles bruts
        """
        print(f"\n{'='*70}")
        print(f"📰 ÉTAPE 1: SCRAPING DES MÉDIAS")
        print(f"{'='*70}\n")
        
        all_articles = []
        
        # Scraper les sites web
        for scraper in self.scrapers:
            try:
                articles = scraper.scrape_all_sections(max_articles_per_section)
                all_articles.extend(articles)
                
                # Enregistrer les stats par média
                media_name = scraper.media_name
                if media_name not in self.media_stats:
                    self.media_stats[media_name] = {
                        'scraped': 0,
                        'inserted': 0,
                        'skipped': 0,
                        'last_article_date': None
                    }
                
                self.media_stats[media_name]['scraped'] = len(articles)
                
                # Trouver la date du dernier article
                if articles:
                    dates = [a.get('date') for a in articles if a.get('date')]
                    if dates:
                        self.media_stats[media_name]['last_article_date'] = max(dates)
                
                print(f"✅ {scraper.media_name}: {len(articles)} articles scrapés")
            except Exception as e:
                print(f"❌ Erreur scraping {scraper.media_name}: {e}")
        
        # Facebook scraping désactivé - utilisera les JSON via facebook_orchestrator.py séparé
        
        self.stats['total_scraped'] = len(all_articles)
        print(f"\n✅ Total scrapé: {len(all_articles)} articles de {len(self.scrapers)} sources")
        
        return all_articles
    
    def run_prediction(self, articles):
        """
        Étape 2: Prédire les catégories avec ML
        
        Args:
            articles: Liste d'articles
        
        Returns:
            Liste d'articles avec catégories prédites
        """
        print(f"\n{'='*70}")
        print(f"🤖 ÉTAPE 2: PRÉDICTION DES CATÉGORIES (ML)")
        print(f"{'='*70}")
        
        articles = self.predictor.predict_batch(articles)
        
        return articles
    
    def run_cleaning(self, articles):
        """
        Étape 3: Nettoyer et valider les données
        
        Args:
            articles: Liste d'articles
        
        Returns:
            Liste d'articles nettoyés et validés
        """
        print(f"\n{'='*70}")
        print(f"🧹 ÉTAPE 3: NETTOYAGE ET VALIDATION")
        print(f"{'='*70}")
        
        # Nettoyer
        articles = self.cleaner.clean_batch(articles)
        
        # Supprimer les doublons
        articles = self.cleaner.deduplicate(articles)
        
        self.stats['total_cleaned'] = len(articles)
        
        return articles
    
    def run_insertion(self, articles):
        """
        Étape 4: Insérer dans la base de données
        
        Args:
            articles: Liste d'articles nettoyés
        
        Returns:
            Statistiques d'insertion
        """
        print(f"\n{'='*70}")
        print(f"💾 ÉTAPE 4: INSERTION DANS SUPABASE")
        print(f"{'='*70}")
        
        stats = self.db_writer.insert_batch(articles)
        
        self.stats['total_inserted'] = stats['inserted']
        self.stats['total_skipped'] = stats['skipped']
        self.stats['total_errors'] = stats['errors']
        
        return stats
    
    def export_to_csv(self, articles, filename=None):
        """
        Exporte les articles vers un fichier CSV avec validation stricte
        
        Args:
            articles: Liste d'articles à exporter
            filename: Nom du fichier CSV (optionnel)
        
        Returns:
            str: Chemin du fichier CSV créé
        """
        print(f"\n{'='*70}")
        print(f"📄 EXPORT CSV DES ARTICLES")
        print(f"{'='*70}")
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'articles_export_{timestamp}.csv'
        
        # Chemin complet
        csv_path = Path(__file__).parent / filename
        
        # Champs CSV (selon schéma BD exactement)
        fieldnames = [
            'id', 'media', 'titre', 'contenu', 'url', 'date', 
            'categorie', 'type_source', 'plateforme',
            'likes', 'commentaires', 'partages'
        ]
        
        exported = 0
        skipped = 0
        
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for article in articles:
                    try:
                        # Validation stricte avant export
                        is_valid, error_msg = self.db_writer.validate_article_for_db(article)
                        if not is_valid:
                            print(f"⚠️ Ligne ignorée (invalide): {error_msg}")
                            skipped += 1
                            continue
                        
                        # Préparer la ligne CSV (selon schéma BD)
                        row = {
                            'id': article.get('id', ''),
                            'media': article.get('media', ''),
                            'titre': article.get('titre', '').replace('\n', ' ').replace('\r', ''),
                            'contenu': article.get('contenu', '').replace('\n', ' ').replace('\r', ''),
                            'url': article.get('url', ''),
                            'date': article['date'].isoformat() if hasattr(article['date'], 'isoformat') else str(article['date']),
                            'categorie': article.get('categorie', ''),
                            'type_source': article.get('type_source', 'article'),
                            'plateforme': article.get('plateforme', 'web'),
                            'likes': article.get('likes', 0),
                            'commentaires': article.get('commentaires', 0),
                            'partages': article.get('partages', 0)
                        }
                        
                        writer.writerow(row)
                        exported += 1
                        
                    except Exception as e:
                        print(f"❌ Erreur export ligne: {e} - Article ignoré")
                        skipped += 1
                        continue
            
            print(f"✅ Export CSV terminé:")
            print(f"   - Exportés: {exported}")
            if skipped > 0:
                print(f"   - Ignorés: {skipped}")
            print(f"   - Fichier: {csv_path}")
            
            # Ajouter à la liste des fichiers temporaires pour suppression ultérieure
            self.temp_csv_files.append(str(csv_path))
            
            return str(csv_path)
            
        except Exception as e:
            print(f"❌ Erreur lors de la création du fichier CSV: {e}")
            return None
    
    def run_full_pipeline(self, max_articles_per_section=20, facebook_max_posts=50):
        """
        Exécute le pipeline complet
        
        Args:
            max_articles_per_section: Nombre max d'articles par section (défaut: 20)
            facebook_max_posts: Nombre max de posts Facebook (défaut: 50)
        
        Returns:
            dict: Statistiques complètes
        """
        start_time = datetime.now()
        
        # Créer l'entrée dans scraping_logs
        try:
            log_entry = self.supabase.table('scraping_logs').insert({
                'started_at': start_time.isoformat(),
                'status': 'running',
                'total_scraped': 0,
                'total_inserted': 0,
                'total_skipped': 0,
                'total_errors': 0
            }).execute()
            
            self.scraping_log_id = log_entry.data[0]['id']
            print(f"📝 Log de scraping créé: ID={self.scraping_log_id}")
        except Exception as e:
            print(f"⚠️ Erreur création log scraping: {e}")
            self.scraping_log_id = None
        
        try:
            # 1. Scraping
            articles = self.run_scraping(max_articles_per_section, facebook_max_posts)
            
            if not articles:
                print("\n⚠️ Aucun article scrapé. Arrêt du pipeline.")
                self._update_scraping_log(start_time, 'completed')
                return self.stats
            
            # 2. Prédiction ML
            articles = self.run_prediction(articles)
            
            # 3. Nettoyage
            articles = self.run_cleaning(articles)
            
            if not articles:
                print("\n⚠️ Aucun article valide après nettoyage. Arrêt du pipeline.")
                self._update_scraping_log(start_time, 'completed')
                return self.stats
            
            # 4. Export CSV BRUT (avant validation BD)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            csv_brut_path = self.export_to_csv(articles, f'articles_brut_{timestamp}.csv')
            if csv_brut_path:
                print(f"✅ CSV brut exporté: {csv_brut_path}")
            
            # 5. Validation stricte selon schéma BD
            print(f"\n{'='*70}")
            print(f"🔧 VALIDATION STRICTE SELON SCHÉMA BD")
            print(f"{'='*70}\n")
            
            validated_articles = []
            rejected_articles = []
            
            print("🔍 Validation et nettoyage en cours...")
            for i, article in enumerate(articles, 1):
                # Nettoyer l'article
                cleaned_article = self.db_writer.clean_article_for_db(article)
                
                # Valider strictement
                is_valid, error_msg = self.db_writer.validate_article_for_db(cleaned_article)
                
                if is_valid:
                    validated_articles.append(cleaned_article)
                else:
                    rejected_articles.append({
                        'article': cleaned_article,
                        'reason': error_msg
                    })
                    print(f"   ⊘ [{i}/{len(articles)}] Rejeté: {error_msg}")
            
            print(f"\n✅ Validation terminée:")
            print(f"   - Articles valides: {len(validated_articles)}")
            print(f"   - Articles rejetés: {len(rejected_articles)}")
            
            # 6. Rapport détaillé des rejets
            if rejected_articles:
                print(f"\n{'='*70}")
                print(f"📋 RAPPORT DES ARTICLES REJETÉS")
                print(f"{'='*70}\n")
                
                # Grouper les rejets par raison
                reject_reasons = {}
                for reject in rejected_articles:
                    reason = reject['reason']
                    if reason not in reject_reasons:
                        reject_reasons[reason] = []
                    reject_reasons[reason].append(reject['article'].get('titre', 'Sans titre')[:50])
                
                for reason, titles in sorted(reject_reasons.items(), key=lambda x: len(x[1]), reverse=True):
                    print(f"❌ {reason} ({len(titles)} articles)")
                    for title in titles[:3]:  # Montrer max 3 exemples
                        print(f"   - {title}...")
                    if len(titles) > 3:
                        print(f"   ... et {len(titles)-3} autres")
                    print()
            
            # 7. Export CSV VALIDÉ (seulement les articles 100% propres)
            if validated_articles:
                csv_valide_path = self.export_to_csv(validated_articles, f'articles_valides_{timestamp}.csv')
                if csv_valide_path:
                    print(f"\n✅ CSV validé exporté: {csv_valide_path}")
                    self.stats['csv_exported'] = csv_valide_path
            else:
                print("\n⚠️ Aucun article valide à exporter !")
            
            # 8. Insertion DB (seulement les articles validés)
            if validated_articles:
                insertion_stats = self.run_insertion(validated_articles)
                
                # Mettre à jour les stats par média avec les résultats d'insertion
                if 'by_media' in insertion_stats:
                    for media_name, media_insertion in insertion_stats['by_media'].items():
                        if media_name in self.media_stats:
                            self.media_stats[media_name]['inserted'] = media_insertion['inserted']
                            self.media_stats[media_name]['skipped'] = media_insertion['skipped']
                
                # Enregistrer les détails par média dans la BD
                self._save_media_details()
            else:
                print("\n⚠️ Aucun article valide pour insertion. Arrêt.")
            
        except Exception as e:
            print(f"\n❌ ERREUR CRITIQUE DANS LE PIPELINE: {e}")
            import traceback
            traceback.print_exc()
            
            # Mettre à jour le log avec l'erreur
            self._update_scraping_log(start_time, 'failed', error_message=str(e))
        
        finally:
            # Mettre à jour le log avec les stats finales
            if self.scraping_log_id:
                self._update_scraping_log(start_time, 'completed')
            
            # Supprimer les fichiers CSV temporaires
            self._cleanup_temp_csv_files()
            
            # Afficher le résumé
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print(f"\n{'='*70}")
            print(f"📊 RÉSUMÉ DU PIPELINE")
            print(f"{'='*70}")
            print(f"Durée totale: {duration:.1f} secondes")
            print(f"\nStatistiques:")
            print(f"  📰 Articles scrapés: {self.stats['total_scraped']}")
            print(f"  ✅ Articles nettoyés: {self.stats['total_cleaned']}")
            print(f"  💾 Articles insérés: {self.stats['total_inserted']}")
            print(f"  ⏭️  Articles ignorés (doublons): {self.stats['total_skipped']}")
            if self.stats['total_errors'] > 0:
                print(f"  ❌ Erreurs: {self.stats['total_errors']}")
            if 'csv_exported' in self.stats:
                print(f"  📄 CSV exporté: {self.stats['csv_exported']}")
            
            success_rate = (self.stats['total_inserted'] / self.stats['total_scraped'] * 100) if self.stats['total_scraped'] > 0 else 0
            print(f"\n  🎯 Taux de réussite: {success_rate:.1f}%")
            
            print(f"\n{'='*70}")
            print(f"🎉 PIPELINE TERMINÉ")
            print(f"{'='*70}\n")
        
        return self.stats
    
    def _update_scraping_log(self, start_time, status, error_message=None):
        """
        Met à jour l'entrée dans scraping_logs
        
        Args:
            start_time: Datetime du début du scraping
            status: 'running', 'completed', 'failed'
            error_message: Message d'erreur si échec
        """
        if not self.scraping_log_id:
            return
        
        try:
            end_time = datetime.now()
            duration = int((end_time - start_time).total_seconds())
            
            update_data = {
                'completed_at': end_time.isoformat(),
                'duration_seconds': duration,
                'status': status,
                'total_scraped': self.stats['total_scraped'],
                'total_inserted': self.stats['total_inserted'],
                'total_skipped': self.stats['total_skipped'],
                'total_errors': self.stats['total_errors']
            }
            
            if error_message:
                update_data['error_message'] = error_message
            
            self.supabase.table('scraping_logs')\
                .update(update_data)\
                .eq('id', self.scraping_log_id)\
                .execute()
            
            print(f"✅ Log de scraping mis à jour: ID={self.scraping_log_id}, status={status}")
        except Exception as e:
            print(f"⚠️ Erreur mise à jour log scraping: {e}")
    
    def _save_media_details(self):
        """
        Enregistre les détails par média dans scraping_media_details
        """
        if not self.scraping_log_id:
            return
        
        try:
            # Récupérer les IDs des médias
            medias_result = self.supabase.table('medias').select('id, name').execute()
            media_name_to_id = {m['name']: m['id'] for m in medias_result.data}
            
            # Créer les entrées pour chaque média
            for media_name, stats in self.media_stats.items():
                # Trouver l'ID du média
                media_id = media_name_to_id.get(media_name)
                if not media_id:
                    print(f"⚠️ Média non trouvé en BD: {media_name}")
                    continue
                
                # Préparer les données
                detail_data = {
                    'scraping_log_id': self.scraping_log_id,
                    'media_id': media_id,
                    'articles_scraped': stats.get('scraped', 0),
                    'articles_inserted': stats.get('inserted', 0),
                    'articles_skipped': stats.get('skipped', 0)
                }
                
                # Ajouter la date du dernier article si disponible
                if stats.get('last_article_date'):
                    last_date = stats['last_article_date']
                    if hasattr(last_date, 'isoformat'):
                        detail_data['last_article_date'] = last_date.isoformat()
                    else:
                        detail_data['last_article_date'] = str(last_date)
                
                # Insérer dans la table
                self.supabase.table('scraping_media_details').insert(detail_data).execute()
            
            print(f"✅ Détails par média enregistrés ({len(self.media_stats)} médias)")
        except Exception as e:
            print(f"⚠️ Erreur enregistrement détails par média: {e}")
            import traceback
            traceback.print_exc()
    
    def _cleanup_temp_csv_files(self):
        """
        Supprime automatiquement les fichiers CSV temporaires après utilisation
        """
        if not self.temp_csv_files:
            return
        
        print(f"\n{'='*70}")
        print(f"🧹 NETTOYAGE DES FICHIERS TEMPORAIRES")
        print(f"{'='*70}")
        
        deleted_count = 0
        failed_count = 0
        
        for csv_file in self.temp_csv_files:
            try:
                csv_path = Path(csv_file)
                if csv_path.exists():
                    csv_path.unlink()  # Supprime le fichier
                    print(f"✅ Supprimé: {csv_path.name}")
                    deleted_count += 1
                else:
                    print(f"⚠️ Fichier introuvable: {csv_path.name}")
            except Exception as e:
                print(f"❌ Erreur suppression {csv_path.name}: {e}")
                failed_count += 1
        
        print(f"\n📊 Résumé nettoyage:")
        print(f"   - Fichiers supprimés: {deleted_count}")
        if failed_count > 0:
            print(f"   - Échecs: {failed_count}")
        
        # Vider la liste
        self.temp_csv_files = []


def main():
    """Point d'entrée principal"""
    # Orchestrateur Web uniquement - Facebook a son propre système
    orchestrator = PipelineOrchestrator()
    
    # Exécuter le pipeline Web
    stats = orchestrator.run_full_pipeline(
        max_articles_per_section=20
    )
    
    return stats


if __name__ == "__main__":
    main()