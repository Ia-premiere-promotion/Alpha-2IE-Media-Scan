#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scheduler pour l'exécution automatique du pipeline
Exécute le scraping toutes les 3 minutes
"""

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging

# Import de l'orchestrateur
from orchestrator import PipelineOrchestrator

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/bakouan/Bureau/APP MEDIA SCAN/backend/pipeline/pipeline.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def run_pipeline_job():
    """Job exécuté par le scheduler"""
    logger.info("="*70)
    logger.info("🔄 DÉMARRAGE DU PIPELINE AUTOMATIQUE")
    logger.info("="*70)
    
    try:
        orchestrator = PipelineOrchestrator()
        stats = orchestrator.run_full_pipeline(max_articles_per_section=15)
        
        logger.info(f"✅ Pipeline terminé avec succès: {stats['total_inserted']} articles insérés")
        
    except Exception as e:
        logger.error(f"❌ Erreur dans le pipeline automatique: {e}")
        import traceback
        logger.error(traceback.format_exc())


def main():
    """Configure et démarre le scheduler"""
    print(f"\n{'='*70}")
    print(f"⏰ SCHEDULER DE SCRAPING AUTOMATIQUE")
    print(f"{'='*70}")
    print(f"Démarré: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n📅 Configuration:")
    print(f"  - Fréquence: Toutes les 3 minutes")
    print(f"  - Articles par section: 15")
    print(f"  - Log: /home/bakouan/Bureau/APP MEDIA SCAN/backend/pipeline/pipeline.log")
    print(f"\n{'='*70}\n")
    
    # Créer le scheduler
    scheduler = BlockingScheduler()
    
    # Ajouter le job : toutes les 3 minutes
    scheduler.add_job(
        run_pipeline_job,
        'interval',
        minutes=3,
        id='pipeline_scraping',
        name='Scraping automatique des médias',
        replace_existing=True
    )
    
    # Optionnel: Exécuter immédiatement au démarrage
    logger.info("🚀 Exécution initiale du pipeline...")
    run_pipeline_job()
    
    logger.info(f"\n⏰ Scheduler actif. Prochaine exécution dans 3 minutes...")
    logger.info(f"Appuyez sur Ctrl+C pour arrêter.\n")
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("\n👋 Arrêt du scheduler...")
        scheduler.shutdown()
        logger.info("✅ Scheduler arrêté proprement")


if __name__ == "__main__":
    main()
