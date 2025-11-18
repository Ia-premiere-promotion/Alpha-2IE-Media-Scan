#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Export des données scrapées en CSV pour vérification avant insertion
"""

import sys
import csv
from pathlib import Path
from datetime import datetime

# Ajouter le path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers.web.lefaso_scraper import LeFasoScraper
from scrapers.web.sidwaya_scraper import SidwayaScraper
from scrapers.web.fasopresse_scraper import FasoPresseScraper
from scrapers.web.observateur_scraper import ObservateurScraper
from scrapers.web.burkina24_scraper import Burkina24Scraper
from ml.predictor import CategoryPredictor
from utils.cleaner import DataCleaner
from utils.date_manager import DateManager
from supabase_client import get_supabase_client

def validate_for_database(article):
    """
    Valide si un article peut être inséré dans la base de données
    Retourne: (is_valid, errors_list)
    """
    errors = []
    
    # Vérifier les champs requis selon schema.sql
    # articles table: id, media_id, titre, url sont NOT NULL
    
    if not article.get('id'):
        errors.append("ID manquant")
    
    if not article.get('media'):
        errors.append("Média manquant")
    
    if not article.get('titre') or article['titre'] == 'Sans titre':
        errors.append("Titre invalide")
    
    if not article.get('url'):
        errors.append("URL manquante")
    
    # Vérifier les types
    if article.get('date') and not isinstance(article['date'], datetime):
        errors.append("Date invalide (pas un datetime)")
    
    # Vérifier les engagements (doivent être des entiers)
    for field in ['likes', 'commentaires', 'partages']:
        if article.get(field) is not None and not isinstance(article[field], int):
            errors.append(f"{field} doit être un entier")
    
    return len(errors) == 0, errors

def export_to_csv():
    """Exporte les données scrapées en CSV avec validation"""
    
    print(f"\n{'='*70}")
    print(f"📊 EXPORT DES DONNÉES SCRAPÉES EN CSV")
    print(f"{'='*70}\n")
    
    # 1. Initialiser
    date_manager = DateManager()
    supabase = get_supabase_client()
    
    # Charger les médias et catégories pour validation
    medias_result = supabase.table('medias').select('id, name').execute()
    media_mapping = {m['name']: m['id'] for m in medias_result.data}
    print(f"✅ {len(media_mapping)} médias chargés: {list(media_mapping.keys())}")
    
    categories_result = supabase.table('categories').select('id, nom').execute()
    category_mapping = {c['nom'].lower(): c['id'] for c in categories_result.data}
    print(f"✅ {len(category_mapping)} catégories chargées\n")
    
    # 2. Initialiser les scrapers
    scrapers = [
        LeFasoScraper(),
        SidwayaScraper(),
        FasoPresseScraper(),
        ObservateurScraper(),
        Burkina24Scraper()
    ]
    
    # Configurer les dates
    for scraper in scrapers:
        last_date = date_manager.get_last_date(scraper.media_name)
        scraper.set_last_publication_date(last_date)
        print(f"📅 {scraper.media_name}: dernière publication = {last_date.strftime('%Y-%m-%d')}")
    
    print(f"\n{'='*70}")
    print("🔍 SCRAPING EN COURS...")
    print(f"{'='*70}\n")
    
    # 3. Scraper
    all_articles = []
    for scraper in scrapers:
        try:
            articles = scraper.scrape_all_sections(max_articles_per_section=20)
            all_articles.extend(articles)
            print(f"✅ {scraper.media_name}: {len(articles)} articles scrapés")
        except Exception as e:
            print(f"❌ Erreur scraping {scraper.media_name}: {e}")
    
    print(f"\n📊 Total scrapé: {len(all_articles)} articles")
    
    # 4. Prédire catégories
    print(f"\n{'='*70}")
    print("🤖 PRÉDICTION DES CATÉGORIES...")
    print(f"{'='*70}\n")
    
    predictor = CategoryPredictor()
    all_articles = predictor.predict_batch(all_articles)
    
    # 5. Nettoyer
    print(f"\n{'='*70}")
    print("🧹 NETTOYAGE...")
    print(f"{'='*70}\n")
    
    cleaner = DataCleaner()
    all_articles = cleaner.deduplicate(all_articles)
    print(f"✅ {len(all_articles)} articles après dédoublonnage")
    
    # 6. Validation et export CSV
    print(f"\n{'='*70}")
    print("✅ VALIDATION ET EXPORT CSV...")
    print(f"{'='*70}\n")
    
    csv_file = Path(__file__).parent / f"scraped_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    errors_file = Path(__file__).parent / f"validation_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    valid_count = 0
    invalid_count = 0
    validation_errors = []
    
    # Définir les colonnes selon schema.sql
    fieldnames = [
        'id', 'media', 'media_id', 'titre', 'contenu', 'url', 'date', 
        'categorie', 'categorie_id', 
        'likes', 'commentaires', 'partages', 'type_source', 'plateforme',
        'validation_status', 'errors'
    ]
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for article in all_articles:
            # Validation
            is_valid, errors = validate_for_database(article)
            
            # Ajouter media_id et categorie_id
            media_id = media_mapping.get(article.get('media'))
            if not media_id:
                is_valid = False
                errors.append(f"Média '{article.get('media')}' non trouvé dans la BD")
            
            categorie_id = None
            if article.get('categorie'):
                categorie_id = category_mapping.get(article['categorie'].lower())
                if not categorie_id:
                    errors.append(f"Catégorie '{article.get('categorie')}' non trouvée dans la BD")
            
            # Préparer la ligne CSV
            row = {
                'id': article.get('id', ''),
                'media': article.get('media', ''),
                'media_id': media_id or '',
                'titre': article.get('titre', ''),
                'contenu': article.get('contenu', '')[:500] if article.get('contenu') else '',  # Limiter pour lisibilité
                'url': article.get('url', ''),
                'date': article.get('date').strftime('%Y-%m-%d %H:%M:%S') if article.get('date') else '',
                'categorie': article.get('categorie', ''),
                'categorie_id': categorie_id or '',
                'likes': article.get('likes', 0),
                'commentaires': article.get('commentaires', 0),
                'partages': article.get('partages', 0),
                'type_source': article.get('type_source', ''),
                'plateforme': article.get('plateforme', ''),
                'validation_status': 'VALID' if is_valid else 'INVALID',
                'errors': '; '.join(errors) if errors else ''
            }
            
            writer.writerow(row)
            
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
                validation_errors.append({
                    'titre': article.get('titre', 'Sans titre')[:50],
                    'media': article.get('media', 'Unknown'),
                    'errors': errors
                })
    
    # Écrire le fichier d'erreurs
    if validation_errors:
        with open(errors_file, 'w', encoding='utf-8') as f:
            f.write(f"ERREURS DE VALIDATION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*70}\n\n")
            f.write(f"Total articles: {len(all_articles)}\n")
            f.write(f"Valides: {valid_count}\n")
            f.write(f"Invalides: {invalid_count}\n\n")
            f.write(f"{'='*70}\n")
            f.write("DÉTAILS DES ERREURS:\n")
            f.write(f"{'='*70}\n\n")
            
            for i, error_info in enumerate(validation_errors, 1):
                f.write(f"{i}. {error_info['media']} - {error_info['titre']}\n")
                for error in error_info['errors']:
                    f.write(f"   ❌ {error}\n")
                f.write("\n")
    
    # Résumé
    print(f"\n{'='*70}")
    print("📊 RÉSUMÉ DE L'EXPORT")
    print(f"{'='*70}\n")
    print(f"✅ Articles valides: {valid_count}")
    print(f"❌ Articles invalides: {invalid_count}")
    print(f"📁 Fichier CSV: {csv_file}")
    if validation_errors:
        print(f"⚠️  Fichier erreurs: {errors_file}")
    
    print(f"\n{'='*70}")
    print("✅ EXPORT TERMINÉ")
    print(f"{'='*70}\n")
    print("📋 Vérifiez le CSV avant d'insérer dans la base de données:")
    print(f"   cat {csv_file} | head -20")
    print("\n💡 Si tout est OK, vous pouvez utiliser db_writer.py pour l'insertion")

if __name__ == '__main__':
    export_to_csv()
