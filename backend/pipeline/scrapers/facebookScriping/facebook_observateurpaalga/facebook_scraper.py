"""
Script pour extraire les publications d'une page Facebook via l'API Graph
Page cible: Observateur Paalga (lobspaalgaBF)
"""

import requests
import json
from datetime import datetime
from typing import List, Dict, Optional


class FacebookGraphScraper:
    """Scraper utilisant l'API Graph de Facebook"""
    
    def __init__(self, access_token: str):
        """
        Initialise le scraper avec un token d'accès
        
        Args:
            access_token: Token d'accès à l'API Graph Facebook
        """
        self.access_token = access_token
        self.base_url = "https://graph.facebook.com/v18.0"
        
    def get_page_posts(self, page_id: str, limit: int = 25) -> List[Dict]:
        """
        Récupère les publications d'une page Facebook
        
        Args:
            page_id: ID ou nom de la page (ex: 'lobspaalgaBF')
            limit: Nombre maximum de posts à récupérer
            
        Returns:
            Liste des publications formatées
        """
        # Champs à récupérer pour chaque post
        fields = [
            'id',
            'message',
            'created_time',
            'permalink_url',
            'type',
            'likes.summary(true)',
            'comments.summary(true)',
            'shares'
        ]
        
        url = f"{self.base_url}/{page_id}/posts"
        params = {
            'access_token': self.access_token,
            'fields': ','.join(fields),
            'limit': limit
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            posts = []
            for post in data.get('data', []):
                formatted_post = self._format_post(post, page_id)
                posts.append(formatted_post)
                
            return posts
            
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la récupération des posts: {e}")
            return []
    
    def get_post_comments(self, post_id: str, limit: int = 100) -> List[Dict]:
        """
        Récupère les commentaires d'un post
        
        Args:
            post_id: ID du post
            limit: Nombre maximum de commentaires
            
        Returns:
            Liste des commentaires formatés
        """
        url = f"{self.base_url}/{post_id}/comments"
        params = {
            'access_token': self.access_token,
            'fields': 'message,created_time,from',
            'limit': limit
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            comments = []
            for idx, comment in enumerate(data.get('data', []), 1):
                comments.append({
                    'numero': idx,
                    'texte': comment.get('message', ''),
                    'auteur': comment.get('from', {}).get('name', ''),
                    'date': comment.get('created_time', '')
                })
                
            return comments
            
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la récupération des commentaires: {e}")
            return []
    
    def _format_post(self, post: Dict, page_id: str) -> Dict:
        """
        Formate un post selon le schéma de sortie défini
        
        Args:
            post: Données brutes du post depuis l'API
            page_id: ID de la page source
            
        Returns:
            Post formaté
        """
        post_id = post.get('id', '')
        likes_count = post.get('likes', {}).get('summary', {}).get('total_count', 0)
        comments_count = post.get('comments', {}).get('summary', {}).get('total_count', 0)
        shares_count = post.get('shares', {}).get('count', 0)
        
        # Récupérer les commentaires
        commentaires = self.get_post_comments(post_id)
        
        return {
            'post_id': post_id,
            'url': post.get('permalink_url', ''),
            'source': f'Facebook - {page_id}',
            'date_post': post.get('created_time', ''),
            'contenu': post.get('message', ''),
            'type_post': post.get('type', 'status'),
            'likes': likes_count,
            'comments': comments_count,
            'shares': shares_count,
            'engagement_total': likes_count + comments_count + shares_count,
            'commentaires': commentaires[:10]  # Limiter à 10 commentaires par post
        }
    
    def scrape_and_save(self, page_id: str, output_file: str = 'facebook_data.json', limit: int = 25):
        """
        Scrape les données et les sauvegarde en JSON
        
        Args:
            page_id: ID ou nom de la page
            output_file: Fichier de sortie JSON
            limit: Nombre de posts à récupérer
        """
        print(f"Récupération des posts de la page {page_id}...")
        posts = self.get_page_posts(page_id, limit)
        
        output_data = {
            'posts': posts,
            'metadata': {
                'page_id': page_id,
                'total_posts': len(posts),
                'scraped_at': datetime.now().isoformat(),
                'total_engagement': sum(p['engagement_total'] for p in posts)
            }
        }
        
        # Sauvegarder en JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ {len(posts)} posts sauvegardés dans {output_file}")
        print(f"✓ Engagement total: {output_data['metadata']['total_engagement']}")


def main():
    """Fonction principale"""
    
    # IMPORTANT: Remplacer par votre token d'accès
    # Pour obtenir un token:
    # 1. Aller sur https://developers.facebook.com/tools/explorer/
    # 2. Sélectionner votre application ou créer une nouvelle app
    # 3. Générer un token avec les permissions: pages_read_engagement, pages_show_list
    ACCESS_TOKEN = "VOTRE_TOKEN_ICI"
    
    # ID de la page Observateur Paalga
    PAGE_ID = "lobspaalgaBF"
    
    # Créer le scraper
    scraper = FacebookGraphScraper(ACCESS_TOKEN)
    
    # Scraper et sauvegarder
    scraper.scrape_and_save(
        page_id=PAGE_ID,
        output_file='observateur_paalga_posts.json',
        limit=50  # Récupérer les 50 derniers posts
    )


if __name__ == "__main__":
    main()
