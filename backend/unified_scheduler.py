"""
🔄 SCHEDULER UNIFIÉ - LANCE LES 2 PIPELINES (WEB + FACEBOOK)
Automatiquement toutes les 10 minutes en arrière-plan
Avec système de notifications (cloche + popup bleues)
"""

import logging
from datetime import datetime
import threading
import time
import json
from pathlib import Path
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ajouter les paths
sys.path.insert(0, str(Path(__file__).parent / 'pipeline'))
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.orchestrator import PipelineOrchestrator
from pipeline.scrapers.facebookScriping.facebook_orchestrator import FacebookOrchestrator

# Fichier d'état partagé avec les routes API
STATE_FILE = Path(__file__).parent / 'pipeline_state.json'

def load_pipeline_state():
    """Charge l'état du pipeline depuis le fichier"""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {
        'is_running': False,
        'last_run': None,
        'last_result': None,
        'current_progress': None,
        'notifications': []
    }

def save_pipeline_state(state):
    """Sauvegarde l'état du pipeline dans le fichier"""
    try:
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"❌ Erreur sauvegarde état: {e}")

def add_notification(notification):
    """Ajoute une notification à la liste (max 20)"""
    state = load_pipeline_state()
    notification['read'] = False  # Nouveau: marquer comme non lu
    state['notifications'].insert(0, notification)
    # Garder seulement les 20 dernières
    state['notifications'] = state['notifications'][:20]
    save_pipeline_state(state)
    logger.info(f"📢 Notification: {notification['title']}")


def run_web_pipeline(max_articles=20):
    """
    🌐 PIPELINE WEB - Scrape les médias web burkinabé
    """
    logger.info("🌐 Démarrage du pipeline WEB...")
    
    try:
        add_notification({
            'type': 'info',
            'title': '🌐 Pipeline WEB démarré',
            'message': 'Scraping des sites web en cours...',
            'timestamp': datetime.now().isoformat()
        })
        
        # Créer et exécuter l'orchestrateur WEB
        orchestrator = PipelineOrchestrator(include_facebook=False)
        
        start_time = time.time()
        stats = orchestrator.run_full_pipeline(
            max_articles_per_section=max_articles,
            facebook_max_posts=0
        )
        duration = time.time() - start_time
        
        # Notification de succès
        add_notification({
            'type': 'success',
            'title': '✅ Pipeline WEB terminé',
            'message': f"{stats.get('total_inserted', 0)} nouveaux articles insérés",
            'stats': stats,
            'duration': f"{duration:.1f}s",
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"✅ Pipeline WEB terminé: {stats.get('total_inserted', 0)} articles")
        return {'success': True, 'stats': stats, 'duration': duration}
        
    except Exception as e:
        logger.error(f"❌ Erreur pipeline WEB: {e}")
        
        add_notification({
            'type': 'error',
            'title': '❌ Erreur Pipeline WEB',
            'message': f'Erreur: {str(e)[:100]}',
            'timestamp': datetime.now().isoformat()
        })
        
        return {'success': False, 'error': str(e)}


def run_facebook_pipeline():
    """
    📘 PIPELINE FACEBOOK - Traite les posts Facebook
    """
    logger.info("📘 Démarrage du pipeline FACEBOOK...")
    
    try:
        add_notification({
            'type': 'info',
            'title': '📘 Pipeline Facebook démarré',
            'message': 'Traitement des posts Facebook...',
            'timestamp': datetime.now().isoformat()
        })
        
        # Créer et exécuter l'orchestrateur FACEBOOK
        fb_orchestrator = FacebookOrchestrator()
        
        start_time = time.time()
        result = fb_orchestrator.run_full_pipeline()
        duration = time.time() - start_time
        
        # Extraire les statistiques
        stats = result.get('stats', {})
        inserted = stats.get('inserted', 0)
        
        # Notification de succès
        add_notification({
            'type': 'success',
            'title': '✅ Pipeline Facebook terminé',
            'message': f"{inserted} nouveaux posts Facebook insérés",
            'stats': stats,
            'duration': f"{duration:.1f}s",
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"✅ Pipeline FACEBOOK terminé: {inserted} posts")
        return {'success': True, 'stats': stats, 'duration': duration}
        
    except Exception as e:
        logger.error(f"❌ Erreur pipeline FACEBOOK: {e}")
        
        add_notification({
            'type': 'error',
            'title': '❌ Erreur Pipeline Facebook',
            'message': f'Erreur: {str(e)[:100]}',
            'timestamp': datetime.now().isoformat()
        })
        
        return {'success': False, 'error': str(e)}


def start_unified_scheduler():
    """
    Démarre le scheduler unifié pour les pipelines WEB et FACEBOOK
    Exécution IMMÉDIATE au lancement puis toutes les 10 minutes
    """
    from apscheduler.schedulers.background import BackgroundScheduler
    
    scheduler = BackgroundScheduler()
    
    # � EXÉCUTER IMMÉDIATEMENT au lancement
    logger.info("🚀 Lancement IMMÉDIAT des pipelines WEB + FACEBOOK...")
    run_unified_pipelines()
    
    # Planifier l'exécution toutes les 10 minutes
    scheduler.add_job(
        func=run_unified_pipelines,
        trigger="interval",
        minutes=10,
        id="unified_pipeline_job",
        name="Pipeline WEB + FACEBOOK unifié",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("✅ Scheduler unifié démarré - Prochaine exécution dans 10 minutes")


if __name__ == "__main__":
    # Test en mode standalone
    print("🧪 Test du scheduler unifié...")
    run_unified_pipelines()
