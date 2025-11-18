import os
import threading
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import config

# Import des blueprints
from routes.auth import auth_bp
from routes.api import api_bp
from routes.users import users_bp
from routes.dashboard import dashboard_bp
from routes.pipeline import pipeline_bp
from routes.export import export_bp

jwt = JWTManager()


def start_scheduler():
    """
    🔄 LANCE LES 2 PIPELINES (WEB + FACEBOOK) AUTOMATIQUEMENT
    Toutes les 10 minutes en arrière-plan
    """
    import sys
    from pathlib import Path
    
    # Ajouter le path du backend et du pipeline
    sys.path.insert(0, str(Path(__file__).parent))
    sys.path.insert(0, str(Path(__file__).parent / 'pipeline'))
    
    from apscheduler.schedulers.background import BackgroundScheduler
    from pipeline.unified_scheduler import run_unified_pipeline
    import logging
    
    # Configuration des logs du scheduler
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - [SCHEDULER] - %(message)s'
    )
    logger = logging.getLogger('unified_scheduler')
    
    # 🔓 RESET du flag is_running au démarrage (au cas où il serait bloqué)
    try:
        import json
        from pathlib import Path
        state_file = Path(__file__).parent / 'pipeline_state.json'
        if state_file.exists():
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            if state.get('is_running', False):
                logger.warning("⚠️ Flag 'is_running' était bloqué - Réinitialisation")
                state['is_running'] = False
                with open(state_file, 'w', encoding='utf-8') as f:
                    json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Erreur lors du reset du flag: {e}")
    
    # Créer le scheduler en arrière-plan
    scheduler = BackgroundScheduler()
    
    # 🚀 EXÉCUTER IMMÉDIATEMENT au démarrage
    logger.info("🚀 LANCEMENT IMMÉDIAT des pipelines WEB + FACEBOOK...")
    logger.info("📰 Pipeline WEB: 5 médias burkinabè")
    logger.info("👥 Pipeline Facebook: 5 pages Facebook")
    
    try:
        run_unified_pipeline()
        logger.info("✅ Première exécution terminée avec succès")
    except Exception as e:
        logger.error(f"❌ Erreur lors de la première exécution: {e}")
    
    # Ajouter le job unifié : toutes les 10 MINUTES
    scheduler.add_job(
        run_unified_pipeline,
        'interval',
        minutes=10,
        id='unified_pipeline_scraping',
        name='Scraping automatique WEB + Facebook',
        replace_existing=True,
        max_instances=1  # Un seul job à la fois
    )
    
    # Démarrer le scheduler
    scheduler.start()
    logger.info("⏰ SCHEDULER UNIFIÉ ACTIVÉ - Prochaine exécution dans 10 minutes")



def create_app(config_name='development'):
    """Factory pour créer l'application Flask"""
    app = Flask(__name__)
    
    # Configuration
    app.config.from_object(config[config_name])
    
    # Initialiser JWT
    jwt.init_app(app)
    
    # CORS - Configuration complète pour production (Vercel)
    CORS(app, 
         resources={r"/api/*": {
             "origins": [
                 "http://localhost:5173", 
                 "http://127.0.0.1:5173",
                 "http://localhost:5174",
                 "https://alpha-2-ie-media-scan.vercel.app",
                 "https://*.vercel.app"
             ],
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization"],
             "expose_headers": ["Content-Type", "Authorization"],
             "supports_credentials": True,
             "send_wildcard": False,
             "max_age": 3600
         }})
    
    # Enregistrer les blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(pipeline_bp)
    app.register_blueprint(export_bp)
    
    # Route de base
    @app.route('/')
    def index():
        return jsonify({
            'name': 'MÉDIA-SCAN API',
            'version': '1.0.0',
            'description': 'Système Intelligent d\'Observation et d\'Analyse des Médias au Burkina Faso',
            'endpoints': {
                'auth': '/api/auth',
                'api': '/api'
            }
        })
    
    # Route de santé
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'healthy',
            'database': 'supabase'
        })
    
    # Gestion des erreurs JWT
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'error': 'Token expiré',
            'message': 'Le token a expiré. Veuillez vous reconnecter.'
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'error': 'Token invalide',
            'message': 'La vérification du token a échoué.'
        }), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            'error': 'Token manquant',
            'message': 'Token d\'autorisation requis.'
        }), 401
    
    return app


if __name__ == '__main__':
    # Récupérer l'environnement
    env = os.getenv('FLASK_ENV', 'development')
    app = create_app(env)
    
    # Lancer le scheduler dans un thread séparé
    print("\n" + "="*70)
    print("🚀 DÉMARRAGE MÉDIA-SCAN")
    print("="*70)
    print("📡 API Flask: http://127.0.0.1:5000")
    print("⏰ SCHEDULER UNIFIÉ: WEB + Facebook toutes les 10 MINUTES")
    print("📢 Notifications: Cloche + Popup bleues activées")
    print("="*70 + "\n")
    
    scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
    scheduler_thread.start()
    
    # Lancer l'application Flask
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=app.config['DEBUG'],
        use_reloader=False  # Désactive le watchdog pour éviter double exécution du scheduler
    )
