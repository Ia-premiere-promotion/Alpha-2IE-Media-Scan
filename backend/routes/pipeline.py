"""
Routes API pour le pipeline de scraping automatique
Permet de lancer, suivre et récupérer les résultats des scraping
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
import threading
import os
import sys
import json
from pathlib import Path

# Ajouter le path du pipeline
sys.path.insert(0, str(Path(__file__).parent.parent / 'pipeline'))
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.orchestrator import PipelineOrchestrator
from supabase_client import get_supabase_client

pipeline_bp = Blueprint('pipeline', __name__, url_prefix='/api/pipeline')

# Fichier pour persister l'état du pipeline
STATE_FILE = Path(__file__).parent.parent / 'pipeline_state.json'

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
        print(f"❌ Erreur sauvegarde état: {e}")

# Charger l'état initial
pipeline_state = load_pipeline_state()


def run_pipeline_async(max_articles=20):
    """Exécute le pipeline en arrière-plan"""
    global pipeline_state
    
    try:
        pipeline_state['is_running'] = True
        pipeline_state['current_progress'] = {
            'status': 'starting',
            'message': '🚀 Démarrage du scraping...',
            'timestamp': datetime.now().isoformat()
        }
        save_pipeline_state(pipeline_state)
        
        # Ajouter notification de démarrage
        add_notification({
            'type': 'info',
            'title': 'Scraping démarré',
            'message': 'Le scraping automatique a commencé',
            'timestamp': datetime.now().isoformat()
        })
        
        # Créer et exécuter l'orchestrateur
        orchestrator = PipelineOrchestrator(include_facebook=False)
        
        pipeline_state['current_progress'] = {
            'status': 'scraping',
            'message': '📰 Scraping des médias en cours...',
            'timestamp': datetime.now().isoformat()
        }
        save_pipeline_state(pipeline_state)
        
        stats = orchestrator.run_full_pipeline(
            max_articles_per_section=max_articles,
            facebook_max_posts=0
        )
        
        # Pipeline terminé
        pipeline_state['is_running'] = False
        pipeline_state['last_run'] = datetime.now().isoformat()
        pipeline_state['last_result'] = {
            'success': True,
            'stats': stats,
            'timestamp': datetime.now().isoformat(),
            'duration': stats.get('duration', 0)
        }
        pipeline_state['current_progress'] = None
        save_pipeline_state(pipeline_state)
        
        # Ajouter notification de succès
        add_notification({
            'type': 'success',
            'title': 'Scraping terminé',
            'message': f"{stats['total_inserted']} nouveaux articles insérés",
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        })
        
        print(f"✅ Pipeline terminé: {stats}")
        
    except Exception as e:
        pipeline_state['is_running'] = False
        pipeline_state['last_run'] = datetime.now().isoformat()
        pipeline_state['last_result'] = {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
        pipeline_state['current_progress'] = None
        save_pipeline_state(pipeline_state)
        
        # Ajouter notification d'erreur
        add_notification({
            'type': 'error',
            'title': 'Erreur de scraping',
            'message': f'Erreur: {str(e)}',
            'timestamp': datetime.now().isoformat()
        })
        
        print(f"❌ Erreur pipeline: {e}")
        import traceback
        traceback.print_exc()


def add_notification(notification):
    """Ajoute une notification à la liste (max 20)"""
    global pipeline_state
    pipeline_state['notifications'].insert(0, notification)
    # Garder seulement les 20 dernières
    pipeline_state['notifications'] = pipeline_state['notifications'][:20]
    save_pipeline_state(pipeline_state)
    print(f"📢 Notification ajoutée: {notification['title']}")


@pipeline_bp.route('/run', methods=['POST'])
def run_pipeline():
    """Lance le pipeline de scraping en arrière-plan"""
    global pipeline_state
    
    if pipeline_state['is_running']:
        return jsonify({
            'success': False,
            'message': 'Un scraping est déjà en cours'
        }), 400
    
    # Paramètres optionnels - gérer les différents formats de requête
    try:
        max_articles = request.json.get('max_articles', 20) if request.json and isinstance(request.json, dict) else 20
    except:
        max_articles = 20
    
    # Lancer le pipeline dans un thread séparé
    thread = threading.Thread(target=run_pipeline_async, args=(max_articles,))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'message': 'Pipeline démarré en arrière-plan',
        'timestamp': datetime.now().isoformat()
    })


@pipeline_bp.route('/status', methods=['GET'])
def get_status():
    """Retourne l'état actuel du pipeline"""
    # Recharger l'état depuis le fichier pour avoir les dernières données
    global pipeline_state
    pipeline_state = load_pipeline_state()
    
    return jsonify({
        'is_running': pipeline_state['is_running'],
        'last_run': pipeline_state['last_run'],
        'last_result': pipeline_state['last_result'],
        'current_progress': pipeline_state['current_progress']
    })


@pipeline_bp.route('/notifications', methods=['GET'])
def get_notifications():
    """Retourne les notifications de scraping"""
    # Recharger l'état depuis le fichier
    global pipeline_state
    pipeline_state = load_pipeline_state()
    
    # Filtrer par type si spécifié
    notification_type = request.args.get('type')
    
    notifications = pipeline_state['notifications']
    if notification_type:
        notifications = [n for n in notifications if n['type'] == notification_type]
    
    print(f"📋 Retour {len(notifications)} notifications")
    
    return jsonify({
        'notifications': notifications,
        'count': len(notifications),
        'unread_count': len([n for n in pipeline_state['notifications'] if not n.get('read', False)])
    })


@pipeline_bp.route('/notifications/mark-read', methods=['POST'])
def mark_notifications_read():
    """Marque toutes les notifications comme lues"""
    global pipeline_state
    pipeline_state = load_pipeline_state()
    
    for notification in pipeline_state['notifications']:
        notification['read'] = True
    
    save_pipeline_state(pipeline_state)
    
    return jsonify({
        'success': True,
        'message': 'Notifications marquées comme lues'
    })


@pipeline_bp.route('/notifications/clear', methods=['POST'])
def clear_notifications():
    """Efface toutes les notifications"""
    global pipeline_state
    pipeline_state = load_pipeline_state()
    pipeline_state['notifications'] = []
    save_pipeline_state(pipeline_state)
    
    return jsonify({
        'success': True,
        'message': 'Notifications effacées'
    })


@pipeline_bp.route('/history', methods=['GET'])
def get_history():
    """Retourne l'historique des scrappings depuis la base de données"""
    try:
        supabase = get_supabase_client()
        
        # Paramètres de pagination
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Récupérer l'historique des scrappings
        result = supabase.table('scraping_logs')\
            .select('*')\
            .order('started_at', desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()
        
        logs = result.data
        
        # Enrichir avec les détails par média
        for log in logs:
            # Récupérer les détails par média pour ce scraping
            media_details = supabase.table('scraping_media_details')\
                .select('*, medias(name)')\
                .eq('scraping_log_id', log['id'])\
                .execute()
            
            log['media_details'] = media_details.data
        
        return jsonify({
            'success': True,
            'logs': logs,
            'count': len(logs)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@pipeline_bp.route('/history/<int:log_id>', methods=['GET'])
def get_history_detail(log_id):
    """Retourne les détails d'un scraping spécifique"""
    try:
        supabase = get_supabase_client()
        
        # Récupérer le log
        log_result = supabase.table('scraping_logs')\
            .select('*')\
            .eq('id', log_id)\
            .single()\
            .execute()
        
        if not log_result.data:
            return jsonify({
                'success': False,
                'error': 'Log non trouvé'
            }), 404
        
        log = log_result.data
        
        # Récupérer les détails par média
        media_details = supabase.table('scraping_media_details')\
            .select('*, medias(name, logo)')\
            .eq('scraping_log_id', log_id)\
            .execute()
        
        log['media_details'] = media_details.data
        
        return jsonify({
            'success': True,
            'log': log
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

