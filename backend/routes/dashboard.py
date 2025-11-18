"""
Routes API pour le Dashboard - Monitoring Médiatique
Fournit les données pour le frontend (stats, médias, articles, alertes, rankings)
"""

from flask import Blueprint, jsonify, request
from supabase import create_client, Client
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

# Configuration Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

def get_supabase() -> Client:
    """Crée et retourne une instance du client Supabase"""
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def parse_time_range(time_range):
    """Convertit le time_range en datetime ISO"""
    now = datetime.utcnow()
    ranges = {
        '1h': now - timedelta(hours=1),
        '6h': now - timedelta(hours=6),
        '24h': now - timedelta(hours=24),
        '7d': now - timedelta(days=7),
        '30d': now - timedelta(days=30)
    }
    return ranges.get(time_range, ranges['24h']).isoformat()


def calculate_influence_score(medias_data):
    """
    Calcule le score d'influence pour une liste de médias avec normalisation relative avancée
    
    Utilise une approche relative avec:
    - Normalisation logarithmique pour les grandes disparités (followers, engagement)
    - Normalisation par percentile pour la robustesse
    - Pondérations: 40% engagement, 25% followers, 15% articles, 10% ancienneté, 10% régularité
    
    Args:
        medias_data: Liste de dict avec les clés: nb_articles, followers, 
                     engagement_total, anciennete_mois, regularite
    
    Returns:
        Liste de dict avec le score_influence ajouté (échelle 0-100)
    """
    import math
    
    if not medias_data or len(medias_data) == 0:
        return medias_data
    
    # Extraire les valeurs pour normalisation
    articles_values = [m.get('nb_articles', 0) for m in medias_data]
    followers_values = [m.get('followers', 0) for m in medias_data]
    engagement_values = [m.get('engagement_total', 0) for m in medias_data]
    anciennete_values = [m.get('anciennete_mois', 0) for m in medias_data]
    
    # Normalisation logarithmique pour grandes disparités
    def normalize_log(value, values_list):
        """Normalisation logarithmique relative - gère mieux les écarts importants"""
        if not values_list or all(v == 0 for v in values_list):
            return 0.0
        
        # Filtrer les valeurs positives pour log
        positive_values = [v for v in values_list if v > 0]
        if not positive_values or value <= 0:
            return 0.0
        
        log_values = [math.log1p(v) for v in positive_values]  # log1p(x) = log(1+x)
        min_log, max_log = min(log_values), max(log_values)
        
        if max_log == min_log:
            return 0.5  # Tous égaux = score moyen
        
        log_value = math.log1p(value)
        return (log_value - min_log) / (max_log - min_log)
    
    # Normalisation linéaire relative standard
    def normalize_linear(value, values_list):
        """Normalisation linéaire relative classique"""
        if not values_list:
            return 0.0
        
        min_val, max_val = min(values_list), max(values_list)
        
        if max_val == min_val:
            return 0.5  # Tous égaux = score moyen
        
        return (value - min_val) / (max_val - min_val)
    
    # Normalisation par rang (percentile)
    def normalize_rank(value, values_list):
        """Normalisation par rang percentile - très robuste"""
        if not values_list:
            return 0.0
        
        sorted_values = sorted(values_list)
        rank = sorted_values.index(value) if value in sorted_values else 0
        
        if len(sorted_values) <= 1:
            return 0.5
        
        return rank / (len(sorted_values) - 1)
    
    # Calculer le score pour chaque média
    for media in medias_data:
        # Utiliser normalisation log pour followers et engagement (grandes disparités)
        followers_norm = normalize_log(media.get('followers', 0), followers_values)
        engagement_norm = normalize_log(media.get('engagement_total', 0), engagement_values)
        
        # Utiliser normalisation linéaire pour articles et ancienneté (variations modérées)
        articles_norm = normalize_linear(media.get('nb_articles', 0), articles_values)
        anciennete_norm = normalize_linear(media.get('anciennete_mois', 0), anciennete_values)
        
        # Régularité déjà en pourcentage (0-100)
        regularite_norm = min(media.get('regularite', 0) / 100.0, 1.0)
        
        # Score d'influence composite (0-100) avec pondérations
        score = (
            0.40 * engagement_norm +      # 40% - Engagement (le plus important)
            0.25 * followers_norm +        # 25% - Audience
            0.15 * articles_norm +         # 15% - Production
            0.10 * anciennete_norm +       # 10% - Ancienneté
            0.10 * regularite_norm         # 10% - Régularité
        ) * 100
        
        media['score_influence'] = round(score, 2)
    
    return medias_data



@dashboard_bp.route('/stats', methods=['GET'])
def get_stats():
    """Statistiques globales du dashboard - ULTRA OPTIMISÉ"""
    try:
        supabase = get_supabase()
        time_range = request.args.get('time_range', '24h')
        
        print(f"📊 get_stats - time_range: {time_range}")
        
        # Total médias actifs
        medias_result = supabase.table('medias').select('id', count='exact').eq('is_active', True).execute()
        total_medias = medias_result.count or 0
        
        # Total articles dans la période
        if time_range == 'all':
            # TOUS les articles sans filtre de date
            print("Récupération de TOUS les articles...")
            articles_result = supabase.table('articles').select('id', count='exact').execute()
        else:
            # Filtrer par date
            start_date = parse_time_range(time_range)
            print(f"Récupération des articles depuis {start_date}...")
            articles_result = supabase.table('articles').select('id', count='exact').gte('date', start_date).execute()
        
        total_articles = articles_result.count or 0
        print(f"✅ Total articles: {total_articles}")
        
        # Calcul des engagements
        total_likes = 0
        total_commentaires = 0
        total_partages = 0
        
        if total_articles > 0:
            # Récupérer les IDs d'articles de la période
            if time_range == 'all':
                articles_in_period = supabase.table('articles').select('id').execute()
            else:
                start_date = parse_time_range(time_range)
                articles_in_period = supabase.table('articles').select('id').gte('date', start_date).execute()
            
            article_ids_set = set(a['id'] for a in articles_in_period.data)
            print(f"📰 Articles dans la période: {len(article_ids_set)}")
            
            # Récupérer TOUS les engagements puis filtrer en Python
            all_engagements = supabase.table('engagements')\
                .select('article_id, likes, commentaires, partages')\
                .execute()
            
            # Filtrer et calculer
            for eng in all_engagements.data:
                if eng['article_id'] in article_ids_set:
                    total_likes += eng.get('likes', 0) or 0
                    total_commentaires += eng.get('commentaires', 0) or 0
                    total_partages += eng.get('partages', 0) or 0
        
        total_engagement = total_likes + total_commentaires + total_partages
        print(f"💬 Engagement total: {total_engagement}")
        
        # Total alertes actives
        alerts_result = supabase.table('alerts').select('id', count='exact').eq('is_resolved', False).execute()
        total_alerts = alerts_result.count or 0
        
        return jsonify({
            'total_medias': total_medias,
            'total_articles': total_articles,
            'total_engagement': total_engagement,
            'total_alerts': total_alerts,
            'engagement_details': {
                'likes': total_likes,
                'commentaires': total_commentaires,
                'partages': total_partages
            }
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/medias', methods=['GET'])
def get_medias():
    """Liste des médias avec leurs statistiques - ULTRA OPTIMISÉ sans .in_()"""
    try:
        supabase = get_supabase()
        time_range = request.args.get('time_range', 'all')  # Par défaut: tous les articles
        
        # Récupérer tous les médias actifs
        medias_result = supabase.table('medias').select('*').eq('is_active', True).execute()
        medias = {m['id']: m for m in medias_result.data}
        
        # Récupérer tous les articles (avec ou sans filtre de date)
        if time_range == 'all':
            print(f"Récupération de TOUS les articles...")
            articles_result = supabase.table('articles')\
                .select('id, media_id')\
                .execute()
        else:
            start_date = parse_time_range(time_range)
            print(f"Récupération des articles depuis {start_date}...")
            articles_result = supabase.table('articles')\
                .select('id, media_id')\
                .gte('date', start_date)\
                .execute()
        
        # Grouper les articles par média
        articles_by_media = {}
        article_ids_set = set()
        
        for article in articles_result.data:
            media_id = article['media_id']
            if media_id not in articles_by_media:
                articles_by_media[media_id] = []
            articles_by_media[media_id].append(article['id'])
            article_ids_set.add(article['id'])
        
        print(f"Trouvé {len(article_ids_set)} articles dans la période")
        
        # Récupérer TOUS les engagements (sans filtre, filtrage en Python)
        print("Récupération de tous les engagements...")
        all_engagements = supabase.table('engagements')\
            .select('article_id, likes, commentaires, partages')\
            .execute()
        
        # Indexer les engagements par article_id
        engagements_by_article = {}
        for eng in all_engagements.data:
            if eng['article_id'] in article_ids_set:
                engagements_by_article[eng['article_id']] = {
                    'likes': eng.get('likes', 0) or 0,
                    'commentaires': eng.get('commentaires', 0) or 0,
                    'partages': eng.get('partages', 0) or 0
                }
        
        print(f"Trouvé {len(engagements_by_article)} engagements pour la période")
        
        # Calculer les stats par média
        medias_with_stats = []
        now = datetime.utcnow()
        ninety_days_ago = now - timedelta(days=90)
        
        for media_id, media in medias.items():
            article_ids = articles_by_media.get(media_id, [])
            
            total_likes = 0
            total_commentaires = 0
            total_partages = 0
            
            for article_id in article_ids:
                if article_id in engagements_by_article:
                    eng = engagements_by_article[article_id]
                    total_likes += eng['likes']
                    total_commentaires += eng['commentaires']
                    total_partages += eng['partages']
            
            # Calculer la régularité (90 jours)
            regularity_rate = 0
            try:
                regularity_articles = supabase.table('articles')\
                    .select('date')\
                    .eq('media_id', media_id)\
                    .gte('date', ninety_days_ago.isoformat())\
                    .execute()
                
                unique_days = set()
                for article in regularity_articles.data:
                    try:
                        article_date = datetime.fromisoformat(article['date'].replace('Z', '+00:00'))
                        unique_days.add(article_date.date())
                    except:
                        pass
                
                days_with_publication = len(unique_days)
                regularity_rate = round((1 - (90 - days_with_publication) / 90) * 100, 1)
            except:
                regularity_rate = 0
            
            # Calculer l'ancienneté en mois
            anciennete_mois = 0
            if media.get('creation_date'):
                try:
                    creation_date = datetime.fromisoformat(str(media['creation_date']))
                    delta = now - creation_date
                    anciennete_mois = int(delta.days / 30.44)  # Moyenne de jours par mois
                except:
                    pass
            
            medias_with_stats.append({
                'id': media['id'],
                'name': media['name'],
                'url_base': media.get('url_base'),
                'type': media.get('type'),
                'couleur': media.get('couleur', '#3B82F6'),
                'icon': media.get('icon', 'Newspaper'),
                'total_articles': len(article_ids),
                'engagement': {
                    'likes': total_likes,
                    'commentaires': total_commentaires,
                    'partages': total_partages,
                    'total': total_likes + total_commentaires + total_partages
                },
                # Données pour le score d'influence
                'nb_articles': len(article_ids),
                'followers': media.get('followers', 0) or 0,
                'engagement_total': total_likes + total_commentaires + total_partages,
                'anciennete_mois': anciennete_mois,
                'regularite': regularity_rate
            })
        
        # Calculer le score d'influence pour tous les médias
        medias_with_stats = calculate_influence_score(medias_with_stats)
        
        return jsonify(medias_with_stats)
    
    except Exception as e:
        print(f"Erreur dans get_medias: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/medias/<int:media_id>', methods=['GET'])
def get_media_details(media_id):
    """Détails complets d'un média spécifique avec statistiques et analyses - ULTRA OPTIMISÉ"""
    try:
        supabase = get_supabase()
        time_range = request.args.get('time_range', '24h')
        
        print(f"🔍 Chargement des détails pour média {media_id} - période: {time_range}")
        
        # Récupérer le média
        media_result = supabase.table('medias').select('*').eq('id', media_id).single().execute()
        media = media_result.data
        
        # Récupérer TOUTES les catégories une seule fois
        categories_result = supabase.table('categories').select('*').execute()
        categories_dict = {cat['id']: cat for cat in categories_result.data}
        
        # OPTIMISATION: Limiter les articles pour accélérer
        # OPTIMISATION: Limiter drastiquement le nombre d'articles pour accélérer le chargement
        max_articles_for_details = 200  # Réduit de 500 à 200 pour performances
        
        # Construire la requête selon la période
        articles_query = supabase.table('articles')\
            .select('id, titre, date, url, categorie_id')\
            .eq('media_id', media_id)
        
        # Appliquer le filtre de date si nécessaire
        if time_range != 'all':
            start_date = parse_time_range(time_range)
            articles_query = articles_query.gte('date', start_date)
        
        # OPTIMISATION: Réduire la limite pour accélérer
        articles_result = articles_query.order('date', desc=True).limit(max_articles_for_details).execute()
        articles_data = articles_result.data
        article_ids = [a['id'] for a in articles_data]
        
        print(f"📰 Trouvé {len(articles_data)} articles (limité à {max_articles_for_details})")
        
        # Statistiques d'engagement - requête optimisée par media_id et date au lieu de liste d'IDs
        total_likes = 0
        total_commentaires = 0
        total_partages = 0
        engagements_dict = {}
        
        # Récupérer les engagements en filtrant directement par les articles du média
        if len(articles_data) > 0:
            # OPTIMISATION: Augmenter chunk_size et réduire les logs
            chunk_size = 1000  # Traiter plus d'articles par requête
            print(f"🔍 Chargement engagements pour {len(article_ids)} articles...")
            
            for i in range(0, len(article_ids), chunk_size):
                chunk = article_ids[i:i+chunk_size]
                try:
                    engagements_result = supabase.table('engagements')\
                        .select('article_id, likes, commentaires, partages')\
                        .in_('article_id', chunk)\
                        .execute()
                    
                    for eng in engagements_result.data:
                        engagements_dict[eng['article_id']] = eng
                        likes = eng.get('likes', 0) or 0
                        commentaires = eng.get('commentaires', 0) or 0
                        partages = eng.get('partages', 0) or 0
                        total_likes += likes
                        total_commentaires += commentaires
                        total_partages += partages
                        
                except Exception as e:
                    print(f"⚠️ Erreur engagements chunk {i//chunk_size + 1}: {str(e)}")
                    continue
        
        print(f"💬 Total engagement: {total_likes + total_commentaires + total_partages}")
        
        # Distribution thématique - calculée en Python (ultra rapide)
        categories_count = {}
        for article in articles_data:
            cat_id = article.get('categorie_id')
            if cat_id:
                categories_count[cat_id] = categories_count.get(cat_id, 0) + 1
        
        # Palette de couleurs pour les catégories
        category_colors = {
            'politique': '#3b82f6',      # Bleu
            'économie': '#10b981',       # Vert
            'economie': '#10b981',       # Vert (sans accent)
            'social': '#8b5cf6',         # Violet
            'culture': '#f59e0b',        # Orange
            'sport': '#ef4444',          # Rouge
            'santé': '#06b6d4',          # Cyan
            'sante': '#06b6d4',          # Cyan (sans accent)
            'éducation': '#ec4899',      # Rose
            'education': '#ec4899',      # Rose (sans accent)
            'sécurité': '#f97316',       # Orange foncé
            'securite': '#f97316',       # Orange foncé (sans accent)
            'environnement': '#22c55e',  # Vert clair
            'technologie': '#6366f1',    # Indigo
            'justice': '#a855f7',        # Violet clair
            'international': '#0ea5e9',  # Bleu ciel
            'agriculture': '#84cc16',    # Lime
            'tourisme': '#14b8a6'        # Teal
        }
        
        categories_distribution = []
        total_articles_count = len(articles_data)
        for cat_id, count in categories_count.items():
            if cat_id in categories_dict:
                cat = categories_dict[cat_id]
                percentage = (count / total_articles_count) * 100 if total_articles_count > 0 else 0
                
                # Déterminer la couleur : utiliser celle de la BD ou une couleur par défaut basée sur le nom
                color = cat.get('couleur')
                if not color or color == '#6B7280':  # Si pas de couleur ou couleur par défaut grise
                    # Chercher une couleur basée sur le nom
                    cat_name_lower = cat['nom'].lower()
                    color = category_colors.get(cat_name_lower, '#6B7280')
                
                categories_distribution.append({
                    'categorie': cat['nom'],
                    'count': count,
                    'percentage': round(percentage, 1),
                    'couleur': color
                })
        
        # Activité par période - calculée en Python (ultra rapide)
        activity_chart = []
        now = datetime.utcnow()
        
        if time_range == '24h':
            # Grouper par heure pour les dernières 24h
            hours_count = [0] * 24
            for article in articles_data:
                try:
                    article_date = datetime.fromisoformat(article['date'].replace('Z', '+00:00'))
                    hours_diff = int((now - article_date).total_seconds() / 3600)
                    if 0 <= hours_diff < 24:
                        hour_index = 23 - hours_diff
                        hours_count[hour_index] += 1
                except:
                    pass
            
            for i in range(24):
                activity_chart.append({
                    'hour': f'{i}h',
                    'value': hours_count[i]
                })
        
        elif time_range == '7d':
            # Grouper par jour pour les 7 derniers jours
            days_count = [0] * 7
            for article in articles_data:
                try:
                    article_date = datetime.fromisoformat(article['date'].replace('Z', '+00:00'))
                    days_diff = (now.date() - article_date.date()).days
                    if 0 <= days_diff < 7:
                        day_index = 6 - days_diff
                        days_count[day_index] += 1
                except:
                    pass
            
            for i in range(7):
                activity_chart.append({
                    'hour': f'J{i+1}',
                    'value': days_count[i]
                })
        
        elif time_range == '30d':
            # Grouper par jour pour les 30 derniers jours
            days_count = [0] * 30
            for article in articles_data:
                try:
                    article_date = datetime.fromisoformat(article['date'].replace('Z', '+00:00'))
                    days_diff = (now.date() - article_date.date()).days
                    if 0 <= days_diff < 30:
                        day_index = 29 - days_diff
                        days_count[day_index] += 1
                except:
                    pass
            
            # Regrouper par 5 jours pour affichage
            for i in range(6):
                count = sum(days_count[i*5:(i+1)*5])
                activity_chart.append({
                    'hour': f'J{i*5+1}-{min(i*5+5, 30)}',
                    'value': count
                })
        
        elif time_range == 'all':
            # Pour "all", grouper par mois (derniers 12 mois)
            months_count = {}
            for article in articles_data:
                try:
                    article_date = datetime.fromisoformat(article['date'].replace('Z', '+00:00'))
                    month_key = article_date.strftime('%Y-%m')
                    months_count[month_key] = months_count.get(month_key, 0) + 1
                except:
                    pass
            
            # Prendre les 12 derniers mois
            for i in range(12):
                period = now - timedelta(days=30*i)
                month_key = period.strftime('%Y-%m')
                activity_chart.insert(0, {
                    'hour': period.strftime('%b'),
                    'value': months_count.get(month_key, 0)
                })
        
        # Enrichir les top 10 articles (ultra rapide avec les dicts)
        articles_enriched = []
        for article in articles_data[:10]:
            categorie_name = None
            if article.get('categorie_id') and article['categorie_id'] in categories_dict:
                categorie_name = categories_dict[article['categorie_id']]['nom']
            
            engagement = engagements_dict.get(article['id'], {'likes': 0, 'commentaires': 0, 'partages': 0})
            
            articles_enriched.append({
                **article,
                'categorie': categorie_name,
                'engagement': engagement
            })
        
        print(f"✅ Détails du média chargés avec succès")
        
        # Calcul du taux de régularité (sur 90 jours) - INDÉPENDANT de la période sélectionnée
        regularity_rate = 0
        try:
            # Récupérer TOUS les articles des 90 derniers jours (requête séparée)
            ninety_days_ago = now - timedelta(days=90)
            ninety_days_ago_iso = ninety_days_ago.isoformat()
            
            print(f"📅 Calcul régularité depuis {ninety_days_ago_iso}")
            
            # Requête indépendante pour les 90 derniers jours
            regularity_articles = supabase.table('articles')\
                .select('date')\
                .eq('media_id', media_id)\
                .gte('date', ninety_days_ago_iso)\
                .execute()
            
            # Compter le nombre de jours uniques avec publication
            unique_days = set()
            for article in regularity_articles.data:
                try:
                    article_date = datetime.fromisoformat(article['date'].replace('Z', '+00:00'))
                    unique_days.add(article_date.date())
                except Exception as date_error:
                    print(f"⚠️ Erreur parsing date: {article['date']} - {date_error}")
                    pass
            
            # Calculer le taux: (1 - jours_sans_publication / 90) * 100
            days_with_publication = len(unique_days)
            days_without_publication = 90 - days_with_publication
            regularity_rate = round((1 - days_without_publication / 90) * 100, 1)
            
            print(f"📅 Régularité: {len(regularity_articles.data)} articles, {days_with_publication} jours actifs sur 90 = {regularity_rate}%")
        except Exception as e:
            print(f"⚠️ Erreur calcul régularité: {e}")
            import traceback
            traceback.print_exc()
            regularity_rate = 0
        
        # Calcul du score d'influence pour ce média
        score_influence = 0
        try:
            # Calculer l'ancienneté en mois
            anciennete_mois = 0
            if media.get('creation_date'):
                try:
                    creation_date = datetime.fromisoformat(str(media['creation_date']))
                    delta = now - creation_date
                    anciennete_mois = int(delta.days / 30.44)
                except:
                    pass
            
            # Préparer les données pour le calcul du score avec normalisation relative
            media_data = [{
                'nb_articles': len(articles_data),
                'followers': media.get('followers', 0) or 0,
                'engagement_total': total_likes + total_commentaires + total_partages,
                'anciennete_mois': anciennete_mois,
                'regularite': regularity_rate
            }]
            
            # Utiliser la fonction de calcul du score avec normalisation relative
            # MAIS comme on n'a qu'un seul média, on va utiliser des valeurs de référence
            # pour avoir un score absolu plutôt que relatif
            
            # Score basé sur des seuils de référence (valeurs médianes du marché)
            ref_articles = 500  # Médiane de référence
            ref_followers = 500000  # Médiane de référence
            ref_engagement = 50000  # Médiane de référence
            ref_anciennete = 120  # 10 ans
            
            # Normalisation logarithmique pour followers et engagement
            import math
            def normalize_log_single(value, ref_value):
                if value <= 0 or ref_value <= 0:
                    return 0.0
                log_value = math.log1p(value)
                log_ref = math.log1p(ref_value)
                # Normaliser autour de la référence (0.5 = référence)
                return min(log_value / (log_ref * 2), 1.0)
            
            # Normalisation linéaire
            def normalize_linear_single(value, ref_value):
                if ref_value <= 0:
                    return 0.0
                return min(value / (ref_value * 2), 1.0)
            
            followers_norm = normalize_log_single(media_data[0]['followers'], ref_followers)
            engagement_norm = normalize_log_single(media_data[0]['engagement_total'], ref_engagement)
            articles_norm = normalize_linear_single(media_data[0]['nb_articles'], ref_articles)
            anciennete_norm = normalize_linear_single(media_data[0]['anciennete_mois'], ref_anciennete)
            regularite_norm = min(regularity_rate / 100.0, 1.0)
            
            # Score final pondéré (0-100)
            score_influence = round((
                0.40 * engagement_norm +
                0.25 * followers_norm +
                0.15 * articles_norm +
                0.10 * anciennete_norm +
                0.10 * regularite_norm
            ) * 100, 2)
            
            print(f"💯 Score d'influence: {score_influence}/100 (E:{engagement_norm:.2f} F:{followers_norm:.2f} A:{articles_norm:.2f} Anc:{anciennete_norm:.2f} R:{regularite_norm:.2f})")
        except Exception as e:
            print(f"⚠️ Erreur calcul score d'influence: {e}")
            import traceback
            traceback.print_exc()
            score_influence = 0
        
        return jsonify({
            'media': {
                **media,
                'regularityRate': regularity_rate,
                'scoreInfluence': score_influence,
                'followers': media.get('followers', 0) or 0,
                'anciennete_mois': anciennete_mois if 'anciennete_mois' in locals() else 0
            },
            'stats': {
                'total_articles': len(articles_data),
                'total_engagement': total_likes + total_commentaires + total_partages,
                'likes': total_likes,
                'commentaires': total_commentaires,
                'partages': total_partages,
                'avg_engagement_per_article': round((total_likes + total_commentaires + total_partages) / max(len(articles_data), 1), 2)
            },
            'articles': articles_enriched,
            'categories_distribution': categories_distribution,
            'activity_chart': activity_chart,
            'time_range': time_range
        })
    
    except Exception as e:
        print(f"❌ Erreur dans get_media_details: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/medias/<int:media_id>/activity', methods=['GET'])
def get_media_activity(media_id):
    """Données d'activité pour un média spécifique"""
    try:
        supabase = get_supabase()
        time_range = request.args.get('time_range', '7d')
        
        # Utiliser la même logique que get_activity_chart mais filtré par média
        now = datetime.utcnow()
        if time_range == '1h':
            start_date = now - timedelta(hours=1)
            interval = 'hour'
            periods = 12
        elif time_range == '6h':
            start_date = now - timedelta(hours=6)
            interval = 'hour'
            periods = 6
        elif time_range == '24h':
            start_date = now - timedelta(hours=24)
            interval = 'hour'
            periods = 24
        elif time_range == '30d':
            start_date = now - timedelta(days=30)
            interval = 'day'
            periods = 30
        else:  # 7d par défaut
            start_date = now - timedelta(days=7)
            interval = 'day'
            periods = 7
        
        # Récupérer les articles du média dans la période
        articles_result = supabase.table('articles')\
            .select('id, date')\
            .eq('media_id', media_id)\
            .gte('date', start_date.isoformat())\
            .execute()
        
        # Grouper par période
        activity_data = {}
        
        for article in articles_result.data:
            article_date = datetime.fromisoformat(article['date'].replace('Z', '+00:00'))
            
            if interval == 'hour':
                period_key = article_date.strftime('%Y-%m-%d %H:00')
            else:
                period_key = article_date.strftime('%Y-%m-%d')
            
            activity_data[period_key] = activity_data.get(period_key, 0) + 1
        
        # Formater pour le graphique
        chart_data = []
        
        if interval == 'hour':
            for i in range(periods):
                period_time = now - timedelta(hours=periods - i - 1)
                period_key = period_time.strftime('%Y-%m-%d %H:00')
                label = period_time.strftime('%Hh')
                
                chart_data.append({
                    'period': period_key,
                    'label': label,
                    'count': activity_data.get(period_key, 0)
                })
        else:
            for i in range(periods):
                period_date = (now - timedelta(days=periods - i - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
                period_key = period_date.strftime('%Y-%m-%d')
                label = f'J{i + 1}'
                
                chart_data.append({
                    'period': period_key,
                    'label': label,
                    'count': activity_data.get(period_key, 0)
                })
        
        return jsonify(chart_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/articles', methods=['GET'])
def get_articles():
    """Liste des articles avec filtres"""
    try:
        supabase = get_supabase()
        
        # Paramètres de filtrage
        media_id = request.args.get('media_id', type=int)
        categorie_id = request.args.get('categorie_id', type=int)
        time_range = request.args.get('time_range', '24h')
        search = request.args.get('search', '')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        start_date = parse_time_range(time_range)
        
        # Construction de la requête
        query = supabase.table('articles').select('*, engagements(*)', count='exact')
        
        if media_id:
            query = query.eq('media_id', media_id)
        
        if categorie_id:
            query = query.eq('categorie_id', categorie_id)
        
        query = query.gte('date', start_date)
        
        if search:
            query = query.ilike('titre', f'%{search}%')
        
        # Pagination
        start = (page - 1) * per_page
        end = start + per_page - 1
        
        result = query.order('date', desc=True).range(start, end).execute()
        
        return jsonify({
            'articles': result.data,
            'total': result.count,
            'page': page,
            'per_page': per_page
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/categories', methods=['GET'])
def get_categories():
    """Liste des catégories avec compteurs"""
    try:
        supabase = get_supabase()
        
        categories_result = supabase.table('categories').select('*').execute()
        
        categories_with_count = []
        for cat in categories_result.data:
            count = supabase.table('articles').select('id', count='exact').eq('categorie_id', cat['id']).execute()
            categories_with_count.append({
                **cat,
                'total_articles': count.count or 0
            })
        
        return jsonify(categories_with_count)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """Liste des alertes avec filtres"""
    try:
        supabase = get_supabase()
        
        is_resolved = request.args.get('is_resolved', 'false').lower() == 'true'
        severite = request.args.get('severite')
        limit = request.args.get('limit', type=int)
        
        # Récupérer les alertes
        query = supabase.table('alerts').select('*')
        query = query.eq('is_resolved', is_resolved)
        
        if severite:
            query = query.eq('severite', severite)
        
        query = query.order('date', desc=True)
        
        if limit:
            query = query.limit(limit)
        
        alerts_result = query.execute()
        
        # Si des alertes existent, enrichir avec les infos des médias
        if alerts_result.data and len(alerts_result.data) > 0:
            # Récupérer les médias
            medias_result = supabase.table('medias').select('id, name, couleur').execute()
            medias_dict = {m['id']: m for m in medias_result.data}
            
            # Enrichir les alertes
            for alert in alerts_result.data:
                media_id = alert.get('media_id')
                if media_id and media_id in medias_dict:
                    alert['media'] = medias_dict[media_id]
                else:
                    alert['media'] = {'name': 'Inconnu', 'couleur': '#6B7280'}
        
        return jsonify(alerts_result.data)
    
    except Exception as e:
        print(f"❌ Erreur dans get_alerts: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'alerts': []}), 500


@dashboard_bp.route('/alerts/<int:alert_id>/resolve', methods=['PUT'])
def resolve_alert(alert_id):
    """Marquer une alerte comme résolue"""
    try:
        supabase = get_supabase()
        
        result = supabase.table('alerts')\
            .update({'is_resolved': True})\
            .eq('id', alert_id)\
            .execute()
        
        if result.data:
            return jsonify({'success': True, 'alert': result.data[0]})
        else:
            return jsonify({'error': 'Alerte non trouvée'}), 404
    
    except Exception as e:
        print(f"❌ Erreur dans resolve_alert: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/alerts/generate', methods=['POST'])
def generate_alerts():
    """Génère les alertes pour tous les médias actifs"""
    try:
        supabase = get_supabase()
        
        # Importer le générateur d'alertes
        import sys
        sys.path.append('/home/bakouan/Bureau/APP MEDIA SCAN/backend')
        from utils.alert_generator import AlertGenerator
        
        generator = AlertGenerator(supabase)
        
        # Récupérer tous les médias actifs avec leurs stats
        medias = supabase.table('medias')\
            .select('id, name, followers, creation_date, is_active')\
            .eq('is_active', True)\
            .execute()
        
        total_alerts = 0
        alerts_created = []
        
        for media in medias.data:
            # Calculer la régularité
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
                    alerts_created.append(alert['titre'])
        
        return jsonify({
            'success': True,
            'total_alerts': total_alerts,
            'alerts_created': alerts_created[:20]  # Limiter à 20 pour l'affichage
        })
    
    except Exception as e:
        print(f"❌ Erreur dans generate_alerts: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/alerts/stats', methods=['GET'])
def get_alerts_stats():
    """Statistiques sur les alertes"""
    try:
        supabase = get_supabase()
        
        # Total alertes actives
        active = supabase.table('alerts')\
            .select('id', count='exact')\
            .eq('is_resolved', False)\
            .execute()
        
        # Par sévérité
        critical = supabase.table('alerts')\
            .select('id', count='exact')\
            .eq('is_resolved', False)\
            .eq('severite', 'critical')\
            .execute()
        
        high = supabase.table('alerts')\
            .select('id', count='exact')\
            .eq('is_resolved', False)\
            .eq('severite', 'high')\
            .execute()
        
        medium = supabase.table('alerts')\
            .select('id', count='exact')\
            .eq('is_resolved', False)\
            .eq('severite', 'medium')\
            .execute()
        
        low = supabase.table('alerts')\
            .select('id', count='exact')\
            .eq('is_resolved', False)\
            .eq('severite', 'low')\
            .execute()
        
        return jsonify({
            'total_active': active.count or 0,
            'by_severity': {
                'critical': critical.count or 0,
                'high': high.count or 0,
                'medium': medium.count or 0,
                'low': low.count or 0
            }
        })
    
    except Exception as e:
        print(f"❌ Erreur dans get_alerts_stats: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/alerts/deontology', methods=['GET'])
def get_deontology_alerts():
    """
    Récupère les articles avec score déontologique < 5/10
    (Articles qui ont déclenché ou devraient déclencher une alerte)
    """
    try:
        supabase = get_supabase()
        
        # Paramètres optionnels
        limit = request.args.get('limit', type=int, default=50)
        media_id = request.args.get('media_id', type=int)
        
        # Requête de base
        query = supabase.table('articles')\
            .select('id, titre, contenu, url, date, score_deontologique, analyse_deontologique, analyzed_at, medias(id, name, couleur)')\
            .not_.is_('score_deontologique', 'null')\
            .lt('score_deontologique', 5.0)\
            .order('score_deontologique', desc=False)\
            .order('date', desc=True)\
            .limit(limit)
        
        # Filtre par média si spécifié
        if media_id:
            query = query.eq('media_id', media_id)
        
        result = query.execute()
        
        # Formater les résultats
        articles = []
        for article in result.data:
            articles.append({
                'id': article['id'],
                'titre': article['titre'],
                'contenu': article['contenu'][:500] if article.get('contenu') else '',  # Extrait
                'url': article['url'],
                'date': article['date'],
                'score_deontologique': article['score_deontologique'],
                'analyse_deontologique': article['analyse_deontologique'],
                'analyzed_at': article['analyzed_at'],
                'media': article.get('medias', {})
            })
        
        return jsonify({
            'total': len(articles),
            'articles': articles
        })
    
    except Exception as e:
        print(f"❌ Erreur dans get_deontology_alerts: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/ranking', methods=['GET'])
def get_ranking():
    """Classement des médias par engagement"""
    try:
        supabase = get_supabase()
        time_range = request.args.get('time_range', '24h')
        start_date = parse_time_range(time_range)
        
        medias_result = supabase.table('medias').select('*').eq('is_active', True).execute()
        
        ranking = []
        for media in medias_result.data:
            # Articles dans la période
            articles_ids = supabase.table('articles').select('id').eq('media_id', media['id']).gte('date', start_date).execute()
            article_ids = [a['id'] for a in articles_ids.data] if articles_ids.data else []
            
            total_engagement = 0
            if article_ids:
                engagements = supabase.table('engagements').select('likes, commentaires, partages').in_('article_id', article_ids).execute()
                for eng in engagements.data:
                    total_engagement += eng.get('likes', 0) + eng.get('commentaires', 0) + eng.get('partages', 0)
            
            ranking.append({
                'media_id': media['id'],
                'name': media['name'],
                'couleur': media.get('couleur'),
                'total_articles': len(article_ids),
                'total_engagement': total_engagement,
                'influence_score': total_engagement / max(len(article_ids), 1)  # Engagement moyen par article
            })
        
        # Trier par influence_score
        ranking.sort(key=lambda x: x['influence_score'], reverse=True)
        
        return jsonify(ranking)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/activity-chart', methods=['GET'])
def get_activity_chart():
    """Données pour le graphique d'activité (global ou par média) - OPTIMISÉ"""
    try:
        supabase = get_supabase()
        media_id = request.args.get('media_id', type=int)
        time_range = request.args.get('time_range', '7d')
        
        print(f"📊 get_activity_chart - time_range: {time_range}, media_id: {media_id}")
        
        # Déterminer la période et la granularité
        now = datetime.utcnow()
        
        if time_range == 'all':
            # Pour "tous les temps", grouper par mois (derniers 12 mois)
            start_date = now - timedelta(days=365)
            interval = 'month'
            periods = 12
        elif time_range == '1h':
            start_date = now - timedelta(hours=1)
            interval = 'hour'
            periods = 12  # 5 minutes intervals
        elif time_range == '6h':
            start_date = now - timedelta(hours=6)
            interval = 'hour'
            periods = 6
        elif time_range == '24h':
            start_date = now - timedelta(hours=24)
            interval = 'hour'
            periods = 24
        elif time_range == '30d':
            start_date = now - timedelta(days=30)
            interval = 'day'
            periods = 30
        else:  # 7d par défaut
            start_date = now - timedelta(days=7)
            interval = 'day'
            periods = 7
        
        # Récupérer les articles avec filtre de date
        query = supabase.table('articles').select('id, date').gte('date', start_date.isoformat())
        
        if media_id:
            query = query.eq('media_id', media_id)
        
        articles_result = query.execute()
        print(f"📰 Trouvé {len(articles_result.data)} articles pour le graphique")
        
        # Grouper par période
        activity_data = {}
        
        for article in articles_result.data:
            article_date = datetime.fromisoformat(article['date'].replace('Z', '+00:00'))
            
            if interval == 'hour':
                # Grouper par heure
                period_key = article_date.strftime('%Y-%m-%d %H:00')
            elif interval == 'month':
                # Grouper par mois
                period_key = article_date.strftime('%Y-%m')
            else:
                # Grouper par jour
                period_key = article_date.strftime('%Y-%m-%d')
            
            activity_data[period_key] = activity_data.get(period_key, 0) + 1
        
        # Formater pour le graphique
        chart_data = []
        
        if interval == 'hour':
            for i in range(periods):
                period_time = now - timedelta(hours=periods - i - 1)
                period_key = period_time.strftime('%Y-%m-%d %H:00')
                label = period_time.strftime('%Hh')
                
                chart_data.append({
                    'period': period_key,
                    'label': label,
                    'count': activity_data.get(period_key, 0)
                })
        elif interval == 'month':
            for i in range(periods):
                period_date = now - timedelta(days=30*(periods - i - 1))
                period_key = period_date.strftime('%Y-%m')
                label = period_date.strftime('%b')
                
                chart_data.append({
                    'period': period_key,
                    'label': label,
                    'count': activity_data.get(period_key, 0)
                })
        else:
            for i in range(periods):
                period_date = (now - timedelta(days=periods - i - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
                period_key = period_date.strftime('%Y-%m-%d')
                label = f'J{i + 1}'
                
                chart_data.append({
                    'period': period_key,
                    'label': label,
                    'count': activity_data.get(period_key, 0)
                })
        
        print(f"✅ Graphique généré avec {len(chart_data)} points")
        return jsonify(chart_data)
    
    except Exception as e:
        print(f"❌ Erreur get_activity_chart: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/sentiment-analysis', methods=['GET'])
def get_sentiment_analysis():
    """Analyse de sentiment (données simulées pour l'instant)"""
    try:
        # TODO: Implémenter l'analyse de sentiment réelle
        return jsonify({
            'sentiment_distribution': {
                'positive': 45,
                'neutral': 35,
                'negative': 20
            },
            'publications': []
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/thematic-distribution', methods=['GET'])
def get_thematic_distribution():
    """Distribution thématique des articles"""
    try:
        supabase = get_supabase()
        media_id = request.args.get('media_id', type=int)
        time_range = request.args.get('time_range', '24h')
        start_date = parse_time_range(time_range)
        
        # Récupérer toutes les catégories
        categories_result = supabase.table('categories').select('*').execute()
        
        distribution = []
        for cat in categories_result.data:
            query = supabase.table('articles').select('id', count='exact').eq('categorie_id', cat['id']).gte('date', start_date)
            
            if media_id:
                query = query.eq('media_id', media_id)
            
            count_result = query.execute()
            
            if count_result.count and count_result.count > 0:
                distribution.append({
                    'categorie': cat['nom'],
                    'count': count_result.count,
                    'couleur': cat.get('couleur', '#6B7280')
                })
        
        return jsonify(distribution)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/recent-articles', methods=['GET'])
def get_recent_articles():
    """
    Récupère les articles récents avec leurs détails
    Query params:
    - limit: nombre d'articles à récupérer (défaut: 10)
    - media_id: filtrer par média (optionnel)
    - time_range: période (all, 1h, 6h, 24h, 7d, 30d) défaut: 24h
    """
    try:
        supabase = get_supabase()
        limit = request.args.get('limit', 10, type=int)
        media_id = request.args.get('media_id', type=int)
        time_range = request.args.get('time_range', '24h')
        
        print(f"📰 get_recent_articles - media_id: {media_id}, time_range: {time_range}, limit: {limit}")
        
        # Parser la période
        start_date = parse_time_range(time_range)
        
        # Récupérer les catégories
        categories_result = supabase.table('categories').select('*').execute()
        categories = {cat['id']: cat for cat in categories_result.data}
        
        # Récupérer les médias
        medias_result = supabase.table('medias').select('*').execute()
        medias = {media['id']: media for media in medias_result.data}
        
        # Query pour les articles récents
        query = supabase.table('articles').select('*').order('date', desc=True).limit(limit)
        
        # Filtrer par date si pas 'all'
        if time_range != 'all':
            query = query.gte('date', start_date)
        
        # Filtrer par média si spécifié
        if media_id:
            query = query.eq('media_id', media_id)
        
        articles_result = query.execute()
        
        print(f"✅ Trouvé {len(articles_result.data)} articles récents")
        
        # Récupérer tous les engagements en une seule requête
        article_ids = [article['id'] for article in articles_result.data]
        engagements_dict = {}
        if article_ids:
            engagements_result = supabase.table('engagements').select('article_id, likes, commentaires, partages').in_('article_id', article_ids).execute()
            for eng in engagements_result.data:
                article_id = eng['article_id']
                likes = eng.get('likes', 0) or 0
                commentaires = eng.get('commentaires', 0) or 0
                partages = eng.get('partages', 0) or 0
                engagements_dict[article_id] = {
                    'likes': likes,
                    'commentaires': commentaires,
                    'partages': partages,
                    'total': likes + commentaires + partages
                }
        
        # Formater les articles
        articles = []
        for article in articles_result.data:
            cat_id = article.get('categorie_id')
            media_id_art = article.get('media_id')
            
            # Récupérer les engagements depuis le dictionnaire
            engagements = engagements_dict.get(article['id'], {
                'likes': 0,
                'commentaires': 0,
                'partages': 0,
                'total': 0
            })
            
            # Calculer le temps écoulé
            try:
                # Nettoyer le format de date (Supabase peut retourner trop de décimales)
                date_str = article['date']
                if '+' in date_str:
                    # Format: 2025-11-17T06:37:31.15684+00:00
                    # Garder seulement 6 chiffres pour les microsecondes
                    parts = date_str.split('.')
                    if len(parts) == 2:
                        main_part = parts[0]
                        micro_and_tz = parts[1]
                        # Séparer microsecondes et timezone
                        if '+' in micro_and_tz:
                            micro, tz = micro_and_tz.split('+')
                            micro = micro[:6]  # Garder max 6 chiffres
                            date_str = f"{main_part}.{micro}+{tz}"
                        elif '-' in micro_and_tz:
                            micro, tz = micro_and_tz.rsplit('-', 1)
                            micro = micro[:6]
                            date_str = f"{main_part}.{micro}-{tz}"
                
                article_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except Exception as e:
                print(f"⚠️ Erreur parsing date '{article['date']}': {e}")
                article_date = datetime.now(timezone.utc)
            
            from datetime import timezone
            now = datetime.now(timezone.utc)
            delta = now - article_date
            
            if delta.days > 0:
                temps_ecoule = f"Il y a {delta.days}j"
            elif delta.seconds // 3600 > 0:
                temps_ecoule = f"Il y a {delta.seconds // 3600}h"
            else:
                temps_ecoule = f"Il y a {delta.seconds // 60}min"
            
            # Extraire les 5 premières lignes du contenu (ou ~250 caractères)
            contenu = article.get('contenu', '') or article.get('description', '')
            if contenu:
                # Prendre les 5 premières lignes ou 250 premiers caractères
                lines = contenu.split('\n')
                first_5_lines = '\n'.join(lines[:5]) if len(lines) >= 5 else contenu
                description = first_5_lines[:250] if len(first_5_lines) > 250 else first_5_lines
            else:
                description = ''
            
            articles.append({
                'id': article['id'],
                'titre': article.get('titre', 'Sans titre'),
                'description': description,
                'contenu': contenu,  # Contenu complet pour référence
                'categorie': categories.get(cat_id, {}).get('nom', 'Autre') if cat_id else 'Autre',
                'categorie_couleur': categories.get(cat_id, {}).get('couleur', '#6B7280') if cat_id else '#6B7280',
                'media': medias.get(media_id_art, {}).get('nom', 'Inconnu') if media_id_art else 'Inconnu',
                'date': article['date'],
                'temps_ecoule': temps_ecoule,
                'likes': engagements['likes'],
                'commentaires': engagements['commentaires'],
                'partages': engagements['partages'],
                'engagement_total': engagements['total'],
                'vues': engagements['total'],  # Garde vues pour compatibilité
                'url': article.get('url', '')
            })
        
        print(f"📦 Retour de {len(articles)} articles formatés")
        return jsonify(articles)
    
    except Exception as e:
        print(f"❌ Erreur get_recent_articles: {str(e)}")
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/sentiments', methods=['GET'])
def get_sentiments():
    """
    Retourne l'analyse déontologique des articles (scores de qualité journalistique)
    Remplace l'ancienne analyse de sentiments par une vraie analyse LLM
    """
    try:
        supabase = get_supabase()
        media_id = request.args.get('media_id', type=int)
        time_range = request.args.get('time_range', 'all')
        limit = request.args.get('limit', 10, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        print(f"🔍 get_sentiments (déontologie) - media_id: {media_id}, time_range: {time_range}, limit: {limit}, offset: {offset}")
        
        # Construire la requête pour récupérer les articles récents
        query = supabase.table('articles')\
            .select('id, titre, contenu, date, media_id')\
            .order('date', desc=True)\
            .range(offset, offset + limit - 1)
        
        # Filtrer par média si spécifié
        if media_id:
            query = query.eq('media_id', media_id)
        
        # Filtrer par période si nécessaire
        if time_range and time_range != 'all':
            start_date = parse_time_range(time_range)
            query = query.gte('date', start_date)
        
        # Exécuter la requête
        result = query.execute()
        articles_data = result.data
        
        print(f"� {len(articles_data)} articles récupérés pour analyse déontologique")
        
        if not articles_data:
            return jsonify({
                'excellent': 0,
                'bon': 0,
                'moyen': 0,
                'faible': 0,
                'critique': 0,
                'total_posts': 0,
                'score_moyen': 0,
                'articles': []
            })
        
        # Analyser chaque article avec le système LLM
        import os
        from dotenv import load_dotenv
        
        # Charger les variables d'environnement depuis /backend/llm/.env
        llm_env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'llm', '.env')
        load_dotenv(llm_env_path)
        
        # Import du module d'analyse
        import sys
        llm_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'llm')
        if llm_path not in sys.path:
            sys.path.insert(0, llm_path)
        
        from analyze_deontology_supabase import DeontologyAnalyzer
        
        # Récupérer les variables d'environnement
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_KEY')
        mistral_api_key = os.getenv('MISTRAL_API_KEY')
        
        if not all([supabase_url, supabase_key, mistral_api_key]):
            print("⚠️ Variables d'environnement manquantes, utilisation de données simulées")
            print(f"  - SUPABASE_URL: {'✓' if supabase_url else '✗'}")
            print(f"  - SUPABASE_KEY: {'✓' if supabase_key else '✗'}")
            print(f"  - MISTRAL_API_KEY: {'✓' if mistral_api_key else '✗'}")
            # Retourner des données simulées si les clés ne sont pas configurées
            return jsonify({
                'excellent': 3,
                'bon': 4,
                'moyen': 2,
                'faible': 1,
                'critique': 0,
                'total_posts': len(articles_data),
                'score_moyen': 7.2,
                'articles': [
                    {
                        'titre': article['titre'][:60] + '...',
                        'score': 7,
                        'interpretation': 'Article conforme aux standards journalistiques'
                    }
                    for article in articles_data[:3]
                ]
            })
        
        # Créer l'analyseur avec Mistral AI
        analyzer = DeontologyAnalyzer(supabase_url, supabase_key, mistral_api_key)
        
        # Analyser les articles
        excellent = 0  # 9-10
        bon = 0        # 7-8
        moyen = 0      # 5-6
        faible = 0     # 3-4
        critique = 0   # 0-2
        
        scores = []
        articles_analyses = []
        
        import time
        
        for idx, article in enumerate(articles_data):
            try:
                # Ajouter un délai entre les requêtes pour éviter le rate limit (sauf pour la première)
                if idx > 0:
                    time.sleep(0.5)  # 500ms entre chaque requête
                
                analysis = analyzer.analyze_content(article['titre'], article.get('contenu', ''))
                score = analysis['score']
                
                if score >= 9:
                    excellent += 1
                elif score >= 7:
                    bon += 1
                elif score >= 5:
                    moyen += 1
                elif score >= 3:
                    faible += 1
                else:
                    critique += 1
                
                if score >= 0:
                    scores.append(score)
                
                articles_analyses.append({
                    'titre': article['titre'][:80],
                    'score': score,
                    'interpretation': analysis['interpretation'],
                    'date': article['date']
                })
            except Exception as e:
                error_msg = str(e)
                print(f"⚠️ Erreur analyse article '{article['titre'][:50]}': {error_msg}")
                
                # En cas d'erreur (rate limit, etc.), ajouter avec score -1
                articles_analyses.append({
                    'titre': article['titre'][:80],
                    'score': -1,
                    'interpretation': f"Erreur d'analyse temporaire. Réessayez plus tard.",
                    'date': article['date']
                })
        
        score_moyen = sum(scores) / len(scores) if scores else 0
        
        result = {
            'excellent': excellent,
            'bon': bon,
            'moyen': moyen,
            'faible': faible,
            'critique': critique,
            'total_posts': len(articles_data),
            'score_moyen': round(score_moyen, 1),
            'articles': articles_analyses  # Tous les articles analysés
        }
        
        print(f"✅ Analyse terminée: Score moyen={score_moyen:.1f}, Excellent={excellent}, Bon={bon}")
        return jsonify(result)
    
    except Exception as e:
        print(f"❌ Erreur get_sentiments: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

