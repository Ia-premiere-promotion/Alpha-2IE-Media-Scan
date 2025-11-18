"""
Générateur d'alertes intelligentes basé sur les métriques
Calcule les alertes sans stocker de données historiques en BD
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import statistics


class AlertGenerator:
    """Génère des alertes basées sur les métriques en temps réel"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
    
    # ========== MÉTHODES UTILITAIRES ==========
    
    def _calculate_engagement_total(self, article_ids: List[str]) -> int:
        """Calcule l'engagement total pour une liste d'articles"""
        if not article_ids:
            return 0
        
        try:
            engagements = self.supabase.table('engagements')\
                .select('likes, commentaires, partages')\
                .in_('article_id', article_ids)\
                .execute()
            
            total = 0
            for eng in engagements.data:
                total += (eng.get('likes', 0) or 0)
                total += (eng.get('commentaires', 0) or 0)
                total += (eng.get('partages', 0) or 0)
            
            return total
        except Exception as e:
            print(f"❌ Erreur calcul engagement: {e}")
            return 0
    
    def _get_articles_in_period(self, media_id: int, start_date: datetime, end_date: datetime = None) -> List[Dict]:
        """Récupère les articles d'un média dans une période"""
        try:
            query = self.supabase.table('articles')\
                .select('id, date, titre')\
                .eq('media_id', media_id)\
                .gte('date', start_date.isoformat())
            
            if end_date:
                query = query.lte('date', end_date.isoformat())
            
            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"❌ Erreur récupération articles: {e}")
            return []
    
    def _get_engagement_stats_7d(self, media_id: int) -> Dict:
        """Calcule les stats d'engagement des 7 derniers jours"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        articles = self._get_articles_in_period(media_id, start_date, end_date)
        article_ids = [a['id'] for a in articles]
        
        total_engagement = self._calculate_engagement_total(article_ids)
        avg_per_article = total_engagement / len(articles) if articles else 0
        
        return {
            'total': total_engagement,
            'avg_per_article': avg_per_article,
            'nb_articles': len(articles)
        }
    
    # ========== ALERTES CRITIQUES ==========
    
    def check_engagement_spike(self, media_id: int, media_name: str) -> Optional[Dict]:
        """
        🔴 CRITICAL: Pic d'engagement anormal
        Engagement sur 1h > 300% de la moyenne des 7 derniers jours
        """
        try:
            # Engagement dernière heure
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            recent_articles = self._get_articles_in_period(media_id, one_hour_ago)
            recent_ids = [a['id'] for a in recent_articles]
            recent_engagement = self._calculate_engagement_total(recent_ids)
            
            # Moyenne 7 jours
            stats_7d = self._get_engagement_stats_7d(media_id)
            avg_engagement = stats_7d['total'] / 7 / 24 if stats_7d['total'] > 0 else 0  # Moyenne par heure
            
            # Détection: engagement 1h > 300% de la moyenne horaire
            if avg_engagement > 0 and recent_engagement > avg_engagement * 3:
                pourcentage = int((recent_engagement / avg_engagement - 1) * 100)
                return {
                    'media_id': media_id,
                    'type': 'pic_engagement',
                    'severite': 'critical',
                    'titre': f'Pic d\'engagement anormal - {media_name}',
                    'message': f'Engagement inhabituel détecté: {recent_engagement} interactions en 1h (+{pourcentage}% vs moyenne de {int(avg_engagement)})',
                    'date': datetime.utcnow()
                }
            
            return None
        except Exception as e:
            print(f"❌ Erreur check_engagement_spike: {e}")
            return None
    
    def check_inactivity(self, media_id: int, media_name: str) -> Optional[Dict]:
        """
        🔴 CRITICAL: Inactivité prolongée
        Aucun article depuis > 48h pour un média habituellement actif
        """
        try:
            # Dernier article
            last_article = self.supabase.table('articles')\
                .select('date')\
                .eq('media_id', media_id)\
                .order('date', desc=True)\
                .limit(1)\
                .execute()
            
            if not last_article.data:
                return None
            
            last_date = datetime.fromisoformat(last_article.data[0]['date'].replace('Z', '+00:00'))
            hours_since = (datetime.utcnow().replace(tzinfo=last_date.tzinfo) - last_date).total_seconds() / 3600
            
            # Vérifier si le média est habituellement actif (> 3 articles/semaine)
            stats_7d = self._get_engagement_stats_7d(media_id)
            is_active_media = stats_7d['nb_articles'] >= 3
            
            # Alerte si inactif depuis 48h et média habituellement actif
            if hours_since > 48 and is_active_media:
                return {
                    'media_id': media_id,
                    'type': 'inactivite',
                    'severite': 'critical',
                    'titre': f'Inactivité prolongée - {media_name}',
                    'message': f'Aucune publication depuis {int(hours_since)}h (inhabituel pour ce média)',
                    'date': datetime.utcnow()
                }
            
            return None
        except Exception as e:
            print(f"❌ Erreur check_inactivity: {e}")
            return None
    
    def check_engagement_drop(self, media_id: int, media_name: str) -> Optional[Dict]:
        """
        🔴 CRITICAL: Chute brutale d'engagement
        Engagement moyen/article < 30% de la moyenne sur 7j
        """
        try:
            # Engagement dernières 24h
            yesterday = datetime.utcnow() - timedelta(hours=24)
            recent_articles = self._get_articles_in_period(media_id, yesterday)
            recent_ids = [a['id'] for a in recent_articles]
            recent_engagement = self._calculate_engagement_total(recent_ids)
            recent_avg = recent_engagement / len(recent_articles) if recent_articles else 0
            
            # Moyenne 7 jours
            stats_7d = self._get_engagement_stats_7d(media_id)
            
            # Détection: engagement moyen < 30% de la moyenne 7j
            if stats_7d['avg_per_article'] > 0 and recent_avg < stats_7d['avg_per_article'] * 0.3:
                pourcentage = int((1 - recent_avg / stats_7d['avg_per_article']) * 100)
                return {
                    'media_id': media_id,
                    'type': 'chute_engagement',
                    'severite': 'critical',
                    'titre': f'Chute d\'engagement - {media_name}',
                    'message': f'Chute de {pourcentage}% détectée (24h: {int(recent_avg)}/article vs 7j: {int(stats_7d["avg_per_article"])}/article)',
                    'date': datetime.utcnow()
                }
            
            return None
        except Exception as e:
            print(f"❌ Erreur check_engagement_drop: {e}")
            return None
    
    # ========== ALERTES IMPORTANTES ==========
    
    def check_publication_burst(self, media_id: int, media_name: str) -> Optional[Dict]:
        """
        🟠 HIGH: Explosion de publications
        Nb articles sur 1h > 200% de la moyenne horaire
        """
        try:
            # Articles dernière heure
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            recent_articles = self._get_articles_in_period(media_id, one_hour_ago)
            nb_recent = len(recent_articles)
            
            # Moyenne horaire sur 7 jours
            stats_7d = self._get_engagement_stats_7d(media_id)
            avg_per_hour = stats_7d['nb_articles'] / (7 * 24) if stats_7d['nb_articles'] > 0 else 0
            
            # Détection: articles 1h > 200% moyenne horaire
            if avg_per_hour > 0 and nb_recent > avg_per_hour * 2 and nb_recent >= 5:
                return {
                    'media_id': media_id,
                    'type': 'explosion_publications',
                    'severite': 'high',
                    'titre': f'Activité inhabituelle - {media_name}',
                    'message': f'{nb_recent} articles publiés en 1h (moyenne: {avg_per_hour:.1f}/h)',
                    'date': datetime.utcnow()
                }
            
            return None
        except Exception as e:
            print(f"❌ Erreur check_publication_burst: {e}")
            return None
    
    def check_influence_drop(self, media_id: int, media_name: str) -> Optional[Dict]:
        """
        🟠 HIGH: Score d'influence en baisse
        Compare le score actuel avec celui du mois dernier
        """
        try:
            # Score actuel (dernier dans media_stats)
            current_score = self.supabase.table('media_stats')\
                .select('influence_score, date')\
                .eq('media_id', media_id)\
                .order('date', desc=True)\
                .limit(1)\
                .execute()
            
            # Score il y a 30 jours
            thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).date()
            old_score = self.supabase.table('media_stats')\
                .select('influence_score, date')\
                .eq('media_id', media_id)\
                .lte('date', thirty_days_ago.isoformat())\
                .order('date', desc=True)\
                .limit(1)\
                .execute()
            
            if current_score.data and old_score.data:
                current = float(current_score.data[0]['influence_score'])
                old = float(old_score.data[0]['influence_score'])
                
                # Détection: score actuel < 70% du score d'il y a 30j
                if old > 0 and current < old * 0.7:
                    return {
                        'media_id': media_id,
                        'type': 'baisse_influence',
                        'severite': 'high',
                        'titre': f'Score d\'influence en baisse - {media_name}',
                        'message': f'Score passé de {old:.1f} à {current:.1f} en 30 jours',
                        'date': datetime.utcnow()
                    }
            
            return None
        except Exception as e:
            print(f"❌ Erreur check_influence_drop: {e}")
            return None
    
    def check_low_regularity(self, media_id: int, media_name: str, regularite: float) -> Optional[Dict]:
        """
        🟠 HIGH: Régularité faible
        Taux de régularité < 50% sur 30 jours
        """
        try:
            if regularite < 50:
                return {
                    'media_id': media_id,
                    'type': 'regularite_faible',
                    'severite': 'high',
                    'titre': f'Régularité de publication faible - {media_name}',
                    'message': f'Régularité de {regularite:.1f}% sur 90 jours (média peu fiable)',
                    'date': datetime.utcnow()
                }
            
            return None
        except Exception as e:
            print(f"❌ Erreur check_low_regularity: {e}")
            return None
    
    # ========== ALERTES MOYENNES ==========
    
    def check_engagement_ratio(self, media_id: int, media_name: str, followers: int) -> Optional[Dict]:
        """
        🟡 MEDIUM: Ratio engagement/followers anormal
        < 0.5% (compte inactif) OU > 20% (bots suspects)
        """
        try:
            if followers == 0:
                return None
            
            # Engagement total 7 jours
            stats_7d = self._get_engagement_stats_7d(media_id)
            ratio = (stats_7d['total'] / followers) * 100 if followers > 0 else 0
            
            if ratio < 0.5 and followers > 1000:
                return {
                    'media_id': media_id,
                    'type': 'ratio_engagement_faible',
                    'severite': 'medium',
                    'titre': f'Ratio engagement suspect - {media_name}',
                    'message': f'Ratio très faible: {ratio:.2f}% (audience possiblement inactive)',
                    'date': datetime.utcnow()
                }
            elif ratio > 20:
                return {
                    'media_id': media_id,
                    'type': 'ratio_engagement_eleve',
                    'severite': 'medium',
                    'titre': f'Ratio engagement anormal - {media_name}',
                    'message': f'Ratio très élevé: {ratio:.1f}% (engagement possiblement artificiel)',
                    'date': datetime.utcnow()
                }
            
            return None
        except Exception as e:
            print(f"❌ Erreur check_engagement_ratio: {e}")
            return None
    
    def check_new_media_activity(self, media_id: int, media_name: str, creation_date: str) -> Optional[Dict]:
        """
        🟡 MEDIUM: Nouveau média très actif
        Média créé depuis < 30j avec > 50 articles
        """
        try:
            if not creation_date:
                return None
            
            created = datetime.fromisoformat(creation_date.replace('Z', '+00:00'))
            days_since = (datetime.utcnow().replace(tzinfo=created.tzinfo) - created).days
            
            if days_since < 30:
                # Compter les articles
                articles = self.supabase.table('articles')\
                    .select('id', count='exact')\
                    .eq('media_id', media_id)\
                    .execute()
                
                nb_articles = articles.count or 0
                
                if nb_articles > 50:
                    return {
                        'media_id': media_id,
                        'type': 'nouveau_media_actif',
                        'severite': 'medium',
                        'titre': f'Nouveau média très actif - {media_name}',
                        'message': f'{nb_articles} articles publiés en {days_since} jours (nouveau média à surveiller)',
                        'date': datetime.utcnow()
                    }
            
            return None
        except Exception as e:
            print(f"❌ Erreur check_new_media_activity: {e}")
            return None
    
    def check_dominant_category(self, media_id: int, media_name: str) -> Optional[Dict]:
        """
        🟡 MEDIUM: Thématique dominante
        Une catégorie représente > 60% des publications sur 24h
        """
        try:
            yesterday = datetime.utcnow() - timedelta(hours=24)
            articles = self._get_articles_in_period(media_id, yesterday)
            
            if len(articles) < 5:  # Pas assez d'articles pour détecter
                return None
            
            # Compter par catégorie
            category_counts = {}
            for article in articles:
                cat_id = article.get('categorie_id')
                if cat_id:
                    category_counts[cat_id] = category_counts.get(cat_id, 0) + 1
            
            if category_counts:
                max_cat_id = max(category_counts, key=category_counts.get)
                max_count = category_counts[max_cat_id]
                percentage = (max_count / len(articles)) * 100
                
                if percentage > 60:
                    # Récupérer le nom de la catégorie
                    cat = self.supabase.table('categories')\
                        .select('nom')\
                        .eq('id', max_cat_id)\
                        .execute()
                    
                    cat_name = cat.data[0]['nom'] if cat.data else 'Inconnue'
                    
                    return {
                        'media_id': media_id,
                        'type': 'thematique_dominante',
                        'severite': 'medium',
                        'titre': f'Thématique dominante - {media_name}',
                        'message': f'Catégorie "{cat_name}" représente {percentage:.1f}% des publications (24h)',
                        'date': datetime.utcnow()
                    }
            
            return None
        except Exception as e:
            print(f"❌ Erreur check_dominant_category: {e}")
            return None
    
    # ========== ALERTES INFORMATIVES ==========
    
    def check_engagement_record(self, media_id: int, media_name: str) -> Optional[Dict]:
        """
        🔵 LOW: Record d'engagement
        Article avec engagement > record précédent du média
        """
        try:
            # Articles des 24 dernières heures
            yesterday = datetime.utcnow() - timedelta(hours=24)
            recent_articles = self._get_articles_in_period(media_id, yesterday)
            
            if not recent_articles:
                return None
            
            # Calculer engagement pour chaque article récent
            for article in recent_articles:
                eng = self.supabase.table('engagements')\
                    .select('likes, commentaires, partages')\
                    .eq('article_id', article['id'])\
                    .execute()
                
                if eng.data:
                    current_eng = sum([
                        eng.data[0].get('likes', 0) or 0,
                        eng.data[0].get('commentaires', 0) or 0,
                        eng.data[0].get('partages', 0) or 0
                    ])
                    
                    # Comparer avec le max historique (hors 24h)
                    old_articles = self.supabase.table('articles')\
                        .select('id')\
                        .eq('media_id', media_id)\
                        .lt('date', yesterday.isoformat())\
                        .execute()
                    
                    if old_articles.data:
                        old_ids = [a['id'] for a in old_articles.data]
                        old_engs = self.supabase.table('engagements')\
                            .select('likes, commentaires, partages')\
                            .in_('article_id', old_ids)\
                            .execute()
                        
                        max_old = 0
                        for old_eng in old_engs.data:
                            total = sum([
                                old_eng.get('likes', 0) or 0,
                                old_eng.get('commentaires', 0) or 0,
                                old_eng.get('partages', 0) or 0
                            ])
                            max_old = max(max_old, total)
                        
                        if current_eng > max_old and max_old > 0:
                            return {
                                'media_id': media_id,
                                'type': 'record_engagement',
                                'severite': 'low',
                                'titre': f'Nouveau record d\'engagement - {media_name}',
                                'message': f'Record battu avec {current_eng} interactions sur "{article["titre"][:50]}..."',
                                'date': datetime.utcnow()
                            }
            
            return None
        except Exception as e:
            print(f"❌ Erreur check_engagement_record: {e}")
            return None
    
    def check_audience_growth(self, media_id: int, media_name: str) -> Optional[Dict]:
        """
        🔵 LOW: Croissance d'audience
        Followers augmentent de > 10% (nécessite historique - skip pour l'instant)
        """
        # TODO: Implémenter quand on aura un historique de followers
        return None
    
    def check_low_deontology_score(self, media_id: int, media_name: str) -> Optional[Dict]:
        """
        🔴 CRITICAL: Score déontologique faible
        Score moyen < 5/10 sur les 7 derniers jours
        """
        try:
            # Articles des 7 derniers jours avec analyse déontologique
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            articles = self.supabase.table('articles')\
                .select('id, score_deontologique')\
                .eq('media_id', media_id)\
                .gte('date', seven_days_ago.isoformat())\
                .not_.is_('score_deontologique', 'null')\
                .execute()
            
            if not articles.data or len(articles.data) < 3:  # Au moins 3 articles analysés
                return None
            
            # Calculer le score moyen
            scores = [a['score_deontologique'] for a in articles.data if a.get('score_deontologique') is not None]
            if not scores:
                return None
            
            avg_score = statistics.mean(scores)
            
            # Alerte si score moyen < 5/10
            if avg_score < 5.0:
                return {
                    'media_id': media_id,
                    'type': 'score_deontologie_faible',
                    'severite': 'critical',
                    'titre': f'Score déontologique critique - {media_name}',
                    'message': f'Score moyen de {avg_score:.1f}/10 sur les 7 derniers jours ({len(scores)} articles analysés). Détection de pratiques journalistiques problématiques.',
                    'date': datetime.utcnow().isoformat(),
                    'is_resolved': False,
                    'metadata': {
                        'score_moyen': round(avg_score, 1),
                        'nb_articles': len(scores),
                        'score_min': round(min(scores), 1),
                        'score_max': round(max(scores), 1)
                    }
                }
        except Exception as e:
            print(f"❌ Erreur check_low_deontology_score: {e}")
        
        return None
    
    def check_high_comments(self, media_id: int, media_name: str) -> Optional[Dict]:
        """
        🔵 LOW: Commentaires inhabituels
        Nb commentaires/article > 200% de la moyenne
        """
        try:
            # Articles dernières 24h
            yesterday = datetime.utcnow() - timedelta(hours=24)
            recent_articles = self._get_articles_in_period(media_id, yesterday)
            recent_ids = [a['id'] for a in recent_articles]
            
            if not recent_ids:
                return None
            
            # Commentaires récents
            recent_engs = self.supabase.table('engagements')\
                .select('commentaires')\
                .in_('article_id', recent_ids)\
                .execute()
            
            recent_comments = sum([e.get('commentaires', 0) or 0 for e in recent_engs.data])
            recent_avg = recent_comments / len(recent_articles) if recent_articles else 0
            
            # Moyenne 7 jours
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            old_articles = self._get_articles_in_period(media_id, seven_days_ago, yesterday)
            old_ids = [a['id'] for a in old_articles]
            
            if old_ids:
                old_engs = self.supabase.table('engagements')\
                    .select('commentaires')\
                    .in_('article_id', old_ids)\
                    .execute()
                
                old_comments = sum([e.get('commentaires', 0) or 0 for e in old_engs.data])
                old_avg = old_comments / len(old_articles) if old_articles else 0
                
                if old_avg > 0 and recent_avg > old_avg * 2:
                    return {
                        'media_id': media_id,
                        'type': 'commentaires_eleves',
                        'severite': 'low',
                        'titre': f'Débat intense - {media_name}',
                        'message': f'{int(recent_avg)} commentaires/article en moyenne (débat ou contenu polémique)',
                        'date': datetime.utcnow()
                    }
            
            return None
        except Exception as e:
            print(f"❌ Erreur check_high_comments: {e}")
            return None
    
    # ========== MÉTHODE PRINCIPALE ==========
    
    def generate_alerts_for_media(self, media: Dict) -> List[Dict]:
        """
        Génère toutes les alertes pour un média donné
        
        Args:
            media: Dict avec id, name, followers, creation_date, regularite
        
        Returns:
            Liste des alertes détectées
        """
        alerts = []
        media_id = media['id']
        media_name = media['name']
        
        # Alertes critiques
        alert = self.check_engagement_spike(media_id, media_name)
        if alert: alerts.append(alert)
        
        alert = self.check_inactivity(media_id, media_name)
        if alert: alerts.append(alert)
        
        alert = self.check_engagement_drop(media_id, media_name)
        if alert: alerts.append(alert)
        
        # Alerte déontologie (CRITIQUE)
        alert = self.check_low_deontology_score(media_id, media_name)
        if alert: alerts.append(alert)
        
        # Alertes importantes
        alert = self.check_publication_burst(media_id, media_name)
        if alert: alerts.append(alert)
        
        alert = self.check_influence_drop(media_id, media_name)
        if alert: alerts.append(alert)
        
        alert = self.check_low_regularity(media_id, media_name, media.get('regularite', 100))
        if alert: alerts.append(alert)
        
        # Alertes moyennes
        alert = self.check_engagement_ratio(media_id, media_name, media.get('followers', 0))
        if alert: alerts.append(alert)
        
        alert = self.check_new_media_activity(media_id, media_name, media.get('creation_date'))
        if alert: alerts.append(alert)
        
        alert = self.check_dominant_category(media_id, media_name)
        if alert: alerts.append(alert)
        
        # Alertes informatives
        alert = self.check_engagement_record(media_id, media_name)
        if alert: alerts.append(alert)
        
        alert = self.check_high_comments(media_id, media_name)
        if alert: alerts.append(alert)
        
        return alerts
    
    def save_alert(self, alert: Dict) -> bool:
        """
        Sauvegarde une alerte dans la base de données
        Vérifie qu'elle n'existe pas déjà (même type + même média + moins de 24h)
        """
        try:
            # Vérifier si une alerte similaire existe déjà
            yesterday = datetime.utcnow() - timedelta(hours=24)
            existing = self.supabase.table('alerts')\
                .select('id')\
                .eq('media_id', alert['media_id'])\
                .eq('type', alert['type'])\
                .eq('is_resolved', False)\
                .gte('date', yesterday.isoformat())\
                .execute()
            
            if existing.data:
                print(f"⚠️ Alerte déjà existante: {alert['type']} pour média {alert['media_id']}")
                return False
            
            # Insérer l'alerte
            self.supabase.table('alerts').insert(alert).execute()
            print(f"✅ Alerte créée: {alert['titre']}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde alerte: {e}")
            return False
