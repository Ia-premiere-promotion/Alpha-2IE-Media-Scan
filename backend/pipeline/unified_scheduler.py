"""
Scheduler unifié pour lancer automatiquement les 2 pipelines:
- Pipeline WEB (médias burkinabè)
- Pipeline Facebook
Toutes les 10 minutes avec système de notifications
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
import json
import threading
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

# Ajouter les paths nécessaires
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.orchestrator import PipelineOrchestrator
from pipeline.scrapers.facebookScriping.facebook_orchestrator import FacebookOrchestrator

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Fichier pour persister l'état
STATE_FILE = Path(__file__).parent.parent / 'pipeline_state.json'

def load_pipeline_state():
    """Charge l'état du pipeline depuis le fichier"""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erreur chargement état: {e}")
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
    
    # Ajouter l'ID et le statut read
    notification['id'] = datetime.now().timestamp()
    notification['read'] = False
    
    state['notifications'].insert(0, notification)
    # Garder seulement les 20 dernières
    state['notifications'] = state['notifications'][:20]
    save_pipeline_state(state)
    logger.info(f"📢 Notification ajoutée: {notification['title']}")


def run_alerts_check():
    """
    🚨 Vérifie et génère les alertes pour tous les médias
    Appelé toutes les heures
    """
    try:
        logger.info("🚨 Vérification des alertes...")
        
        # Importer les dépendances
        from supabase import create_client
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # Créer le client Supabase
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        supabase = create_client(supabase_url, supabase_key)
        
        # Importer le générateur d'alertes
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from utils.alert_generator import AlertGenerator
        
        generator = AlertGenerator(supabase)
        
        # Récupérer tous les médias actifs
        medias = supabase.table('medias')\
            .select('id, name, followers, creation_date, is_active')\
            .eq('is_active', True)\
            .execute()
        
        total_alerts = 0
        
        for media in medias.data:
            # Calculer la régularité (90 jours)
            from datetime import timedelta
            ninety_days_ago = datetime.utcnow() - timedelta(days=90)
            articles_90d = supabase.table('articles')\
                .select('date')\
                .eq('media_id', media['id'])\
                .gte('date', ninety_days_ago.isoformat())\
                .execute()
            
            dates_with_articles = set()
            for article in articles_90d.data:
                article_date = datetime.fromisoformat(article['date'].replace('Z', '+00:00')).date()
                dates_with_articles.add(article_date)
            
            days_with_publications = len(dates_with_articles)
            regularite = (days_with_publications / 90) * 100
            
            media['regularite'] = regularite
            
            # Générer les alertes pour ce média
            alerts = generator.generate_alerts_for_media(media)
            
            # Sauvegarder les alertes
            for alert in alerts:
                if generator.save_alert(alert):
                    total_alerts += 1
                    
                    # Créer une notification pour les alertes critiques et high
                    if alert['severite'] in ['critical', 'high']:
                        severity_emoji = '🔴' if alert['severite'] == 'critical' else '🟠'
                        add_notification({
                            'type': 'alert',
                            'title': f'{severity_emoji} {alert["titre"]}',
                            'message': alert['message'],
                            'severity': alert['severite'],
                            'timestamp': datetime.now().isoformat()
                        })
        
        logger.info(f"✅ Vérification des alertes terminée: {total_alerts} nouvelles alertes")
        
        # Notification récapitulative si des alertes ont été créées
        if total_alerts > 0:
            add_notification({
                'type': 'info',
                'title': f'🚨 {total_alerts} nouvelles alertes détectées',
                'message': f'Vérification automatique des métriques terminée',
                'timestamp': datetime.now().isoformat()
            })
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la vérification des alertes: {e}")
        import traceback
        traceback.print_exc()


def run_unified_pipeline():
    """
    Exécute les 2 pipelines en parallèle:
    1. Pipeline WEB (médias burkinabè)
    2. Pipeline Facebook
    """
    state = load_pipeline_state()
    
    # Vérifier si un scraping est déjà en cours (avec timeout de sécurité de 30 min)
    if state.get('is_running', False):
        last_run = state.get('last_run')
        if last_run:
            from dateutil import parser
            last_run_time = parser.isoparse(last_run)
            elapsed = (datetime.now() - last_run_time).total_seconds()
            # Si le scraping est bloqué depuis plus de 30 minutes, on le débloque
            if elapsed > 1800:  # 30 minutes
                logger.warning(f"⚠️ Scraping bloqué depuis {elapsed/60:.1f} min - Déblocage forcé")
                state['is_running'] = False
                save_pipeline_state(state)
            else:
                logger.warning(f"⚠️ Un scraping est déjà en cours depuis {elapsed/60:.1f} min")
                return
        else:
            logger.warning("⚠️ Un scraping est déjà en cours, passage ignoré")
            return
    
    logger.info("=" * 80)
    logger.info("🚀 LANCEMENT DES PIPELINES AUTOMATIQUES")
    logger.info("=" * 80)
    
    # Recharger l'état pour préserver les notifications précédentes
    state = load_pipeline_state()
    state['is_running'] = True
    state['last_run'] = datetime.now().isoformat()
    state['current_progress'] = {
        'status': 'starting',
        'message': '🚀 Démarrage des pipelines...',
        'timestamp': datetime.now().isoformat()
    }
    save_pipeline_state(state)
    
    # Notification de démarrage
    add_notification({
        'type': 'info',
        'title': 'Scraping automatique démarré',
        'message': 'Lancement des pipelines WEB et Facebook',
        'timestamp': datetime.now().isoformat()
    })
    
    web_stats = {}
    facebook_stats = {}
    
    # Fonction pour exécuter le pipeline WEB dans un thread
    def run_web_pipeline():
        nonlocal web_stats
        try:
            # === PIPELINE 1: WEB ===
            logger.info("\n📰 === PIPELINE WEB - Médias burkinabè ===")
            
            # Recharger l'état pour préserver les notifications
            state = load_pipeline_state()
            state['current_progress'] = {
                'status': 'web_scraping',
                'message': '📰 Scraping des sites web en cours...',
                'timestamp': datetime.now().isoformat()
            }
            save_pipeline_state(state)
            
            web_orchestrator = PipelineOrchestrator(include_facebook=False)
            web_stats = web_orchestrator.run_full_pipeline(
                max_articles_per_section=20,
                facebook_max_posts=0
            )
            logger.info(f"✅ Pipeline WEB terminé: {web_stats.get('total_inserted', 0)} articles insérés")
            
            # Notification succès WEB
            add_notification({
                'type': 'success',
                'title': 'Pipeline WEB terminé',
                'message': f"{web_stats.get('total_inserted', 0)} nouveaux articles insérés",
                'stats': web_stats,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur Pipeline WEB: {e}")
            add_notification({
                'type': 'error',
                'title': 'Erreur Pipeline WEB',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            })
            web_stats = {'error': str(e), 'total_inserted': 0}
    
    # Fonction pour exécuter le pipeline Facebook dans un thread
    def run_facebook_pipeline():
        nonlocal facebook_stats
        try:
            # === PIPELINE 2: FACEBOOK ===
            logger.info("\n👥 === PIPELINE FACEBOOK ===")
            
            # Recharger l'état pour préserver les notifications
            state = load_pipeline_state()
            state['current_progress'] = {
                'status': 'facebook_scraping',
                'message': '👥 Traitement des posts Facebook...',
                'timestamp': datetime.now().isoformat()
            }
            save_pipeline_state(state)
            
            fb_orchestrator = FacebookOrchestrator()
            facebook_stats = fb_orchestrator.run_full_pipeline()
            logger.info(f"✅ Pipeline Facebook terminé: {facebook_stats.get('inserted', 0)} posts insérés")
            
            # Notification succès Facebook
            add_notification({
                'type': 'success',
                'title': 'Pipeline Facebook terminé',
                'message': f"{facebook_stats.get('inserted', 0)} nouveaux posts insérés",
                'stats': {
                    'total_scraped': facebook_stats.get('total_posts', 0),
                    'total_inserted': facebook_stats.get('inserted', 0),
                    'total_skipped': facebook_stats.get('duplicates', 0) + facebook_stats.get('rejected', 0)
                },
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur Pipeline Facebook: {e}")
            add_notification({
                'type': 'error',
                'title': 'Erreur Pipeline Facebook',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            })
            facebook_stats = {'error': str(e), 'inserted': 0}
    
    try:
        # 🚀 LANCER LES 2 PIPELINES EN PARALLÈLE
        logger.info("🚀 Lancement des 2 pipelines EN PARALLÈLE...")
        
        web_thread = threading.Thread(target=run_web_pipeline, name="WebPipeline")
        facebook_thread = threading.Thread(target=run_facebook_pipeline, name="FacebookPipeline")
        
        # Démarrer les 2 threads simultanément
        web_thread.start()
        facebook_thread.start()
        
        # Attendre que les 2 threads se terminent
        web_thread.join()
        facebook_thread.join()
        
        logger.info("✅ Les 2 pipelines sont terminés")
        
        # === RÉSUMÉ FINAL ===
        total_inserted = web_stats.get('total_inserted', 0) + facebook_stats.get('inserted', 0)
        
        logger.info("\n" + "=" * 80)
        logger.info("📊 RÉSUMÉ DES PIPELINES")
        logger.info("=" * 80)
        logger.info(f"📰 WEB: {web_stats.get('total_inserted', 0)} articles")
        logger.info(f"👥 FACEBOOK: {facebook_stats.get('inserted', 0)} posts")
        logger.info(f"✅ TOTAL: {total_inserted} nouveaux contenus")
        logger.info("=" * 80)
        
        # Recharger l'état pour préserver les notifications
        state = load_pipeline_state()
        state['is_running'] = False
        state['last_run'] = datetime.now().isoformat()
        state['last_result'] = {
            'success': True,
            'web_stats': web_stats,
            'facebook_stats': facebook_stats,
            'total_inserted': total_inserted,
            'timestamp': datetime.now().isoformat()
        }
        state['current_progress'] = None
        save_pipeline_state(state)
        
        # Notification finale de résumé
        add_notification({
            'type': 'success',
            'title': 'Pipelines terminés',
            'message': f"Total: {total_inserted} nouveaux contenus insérés (WEB: {web_stats.get('total_inserted', 0)}, Facebook: {facebook_stats.get('inserted', 0)})",
            'stats': {
                'total_scraped': web_stats.get('total_scraped', 0) + facebook_stats.get('total_posts', 0),
                'total_inserted': total_inserted,
                'total_skipped': web_stats.get('total_skipped', 0) + facebook_stats.get('duplicates', 0) + facebook_stats.get('rejected', 0)
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()
        
        # Recharger l'état pour préserver les notifications
        state = load_pipeline_state()
        state['is_running'] = False
        state['last_run'] = datetime.now().isoformat()
        state['last_result'] = {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
        state['current_progress'] = None
        save_pipeline_state(state)
        
        add_notification({
            'type': 'error',
            'title': 'Erreur critique',
            'message': f'Erreur lors de l\'exécution des pipelines: {str(e)}',
            'timestamp': datetime.now().isoformat()
        })


def start_unified_scheduler():
    """
    Démarre le scheduler unifié qui lance:
    - Les 2 pipelines (WEB + Facebook) toutes les 10 minutes
    - La vérification des alertes toutes les heures
    """
    scheduler = BackgroundScheduler()
    
    # Job 1: Pipelines toutes les 10 minutes
    scheduler.add_job(
        func=run_unified_pipeline,
        trigger='interval',
        minutes=10,
        id='unified_pipeline_job',
        name='Pipeline Unifié (WEB + Facebook)',
        replace_existing=True,
        max_instances=1  # Un seul job à la fois
    )
    
    # Job 2: Alertes toutes les heures
    scheduler.add_job(
        func=run_alerts_check,
        trigger='interval',
        hours=1,
        id='alerts_check_job',
        name='Vérification des alertes',
        replace_existing=True,
        max_instances=1
    )
    
    # Exécuter la vérification des alertes au démarrage
    logger.info("🚨 Lancement initial de la vérification des alertes...")
    try:
        run_alerts_check()
    except Exception as e:
        logger.error(f"❌ Erreur lors de la vérification initiale des alertes: {e}")
    
    # Listener pour les événements
    def job_listener(event):
        if event.exception:
            logger.error(f"❌ Job failed: {event.exception}")
        else:
            logger.info(f"✅ Job executed successfully")
    
    scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    
    scheduler.start()
    logger.info("✅ Scheduler unifié démarré")
    logger.info("   📰 Pipeline WEB + 👥 Pipeline Facebook toutes les 10 minutes")
    logger.info("   🚨 Vérification des alertes toutes les heures")
    logger.info("   ⏰ Prochaine exécution des pipelines dans 10 minutes")
    
    return scheduler


if __name__ == '__main__':
    """
    Mode autonome: lance le scheduler et attend indéfiniment
    """
    logger.info("🚀 Démarrage du scheduler unifié en mode autonome")
    
    scheduler = start_unified_scheduler()
    
    try:
        # Garder le script actif
        import time
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Arrêt du scheduler")
        scheduler.shutdown()
