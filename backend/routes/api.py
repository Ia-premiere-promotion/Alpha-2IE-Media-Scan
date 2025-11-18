from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime, timedelta

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/medias', methods=['GET'])
@jwt_required()
def get_medias():
    """Récupérer tous les médias actifs"""
    try:
        # Données statiques pour l'instant (seront remplacées par Supabase)
        medias = [
            {'id': 1, 'name': 'RTB Télévision', 'type': 'tv', 'is_active': True},
            {'id': 2, 'name': 'Sidwaya', 'type': 'presse_ecrite', 'is_active': True},
            {'id': 3, 'name': "L'Observateur Paalga", 'type': 'presse_ecrite', 'is_active': True},
            {'id': 4, 'name': 'Le Pays', 'type': 'presse_ecrite', 'is_active': True},
            {'id': 5, 'name': 'RTB Radio', 'type': 'radio', 'is_active': True},
            {'id': 6, 'name': 'Oméga FM', 'type': 'radio', 'is_active': True},
            {'id': 7, 'name': 'BF1', 'type': 'tv', 'is_active': True},
            {'id': 8, 'name': 'Burkina 24', 'type': 'en_ligne', 'is_active': True},
        ]
        
        return jsonify({
            'medias': medias,
            'total': len(medias)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """Récupérer les statistiques générales"""
    try:
        # Données statiques pour l'instant
        stats = {
            'total_medias': 8,
            'total_articles': 1247,
            'recent_articles': 156,
            'total_alerts': 23,
            'categories': [
                {'category': 'Politique', 'count': 345},
                {'category': 'Économie', 'count': 278},
                {'category': 'Société', 'count': 412},
                {'category': 'Sport', 'count': 212}
            ]
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@jwt_required()
def get_medias():
    """Récupérer la liste des médias"""
    try:
        medias = Media.query.filter_by(is_active=True).all()
        return jsonify({
            'medias': [media.to_dict() for media in medias],
            'total': len(medias)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/articles', methods=['GET'])
@jwt_required()
def get_articles():
    """Récupérer les articles avec pagination et filtres"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        category = request.args.get('category')
        media_id = request.args.get('media_id', type=int)
        
        query = Article.query
        
        if category:
            query = query.filter_by(category=category)
        if media_id:
            query = query.filter_by(media_id=media_id)
        
        # Trier par date de publication décroissante
        query = query.order_by(desc(Article.published_date))
        
        # Pagination
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'articles': [article.to_dict() for article in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'total_pages': pagination.pages
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/stats/overview', methods=['GET'])
@jwt_required()
def get_overview_stats():
    """Récupérer les statistiques générales"""
    try:
        total_medias = Media.query.filter_by(is_active=True).count()
        total_articles = Article.query.count()
        
        # Articles des dernières 24h
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_articles = Article.query.filter(Article.created_at >= yesterday).count()
        
        # Catégories
        categories = db.session.query(
            Article.category,
            func.count(Article.id).label('count')
        ).group_by(Article.category).all()
        
        return jsonify({
            'total_medias': total_medias,
            'total_articles': total_articles,
            'recent_articles_24h': recent_articles,
            'categories': [{'name': cat[0], 'count': cat[1]} for cat in categories if cat[0]]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/stats/media-influence', methods=['GET'])
@jwt_required()
def get_media_influence():
    """Classement des médias par influence"""
    try:
        # Calculer l'engagement total par média
        media_stats = db.session.query(
            Media.id,
            Media.name,
            func.count(Article.id).label('total_articles'),
            func.sum(Article.likes + Article.shares + Article.comments).label('total_engagement')
        ).join(Article).group_by(Media.id, Media.name).all()
        
        # Calculer le score d'influence (simple: engagement / articles)
        results = []
        for stat in media_stats:
            influence_score = (stat.total_engagement / stat.total_articles) if stat.total_articles > 0 else 0
            results.append({
                'media_id': stat.id,
                'media_name': stat.name,
                'total_articles': stat.total_articles,
                'total_engagement': stat.total_engagement or 0,
                'influence_score': round(influence_score, 2)
            })
        
        # Trier par score d'influence
        results.sort(key=lambda x: x['influence_score'], reverse=True)
        
        return jsonify({
            'rankings': results
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/stats/sensitive-content', methods=['GET'])
@jwt_required()
def get_sensitive_content():
    """Récupérer les contenus sensibles détectés"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = Article.query.filter_by(is_sensitive=True).order_by(desc(Article.toxicity_score))
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'sensitive_articles': [article.to_dict() for article in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
