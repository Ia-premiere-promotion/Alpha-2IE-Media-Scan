"""
Script de visualisation des données Fasopresse
Affiche les statistiques et les posts récents
"""

import json
import os
from datetime import datetime


def format_number(num):
    """Formate un nombre avec des séparateurs"""
    return f"{num:,}".replace(',', ' ')


def truncate_text(text, max_length=100):
    """Tronque un texte avec des points de suspension"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def view_fasopresse_data(filename='fasopresse_realtime.json'):
    """
    Affiche les données de monitoring de Fasopresse
    
    Args:
        filename: Nom du fichier JSON à lire
    """
    if not os.path.exists(filename):
        print(f"❌ Fichier non trouvé: {filename}")
        return
    
    # Charger les données
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    posts = data.get('posts', [])
    metadata = data.get('metadata', {})
    
    # Afficher l'en-tête
    print("\n" + "="*80)
    print(f"📊 DONNÉES FASOPRESSE - {metadata.get('page', 'Fasopresse')}")
    print("="*80)
    
    # Afficher les métadonnées
    print(f"\n📅 Dernière mise à jour: {metadata.get('last_update', 'N/A')}")
    print(f"🌐 Page: {metadata.get('page_url', 'N/A')}")
    print(f"\n📈 STATISTIQUES GLOBALES:")
    print(f"  📝 Total posts: {format_number(metadata.get('total_posts', 0))}")
    print(f"  💬 Engagement total: {format_number(metadata.get('total_engagement', 0))}")
    print(f"  👍 Likes: {format_number(metadata.get('total_likes', 0))}")
    print(f"  💬 Commentaires: {format_number(metadata.get('total_comments', 0))}")
    print(f"  🔄 Partages: {format_number(metadata.get('total_shares', 0))}")
    
    if not posts:
        print("\n⚠️ Aucun post à afficher")
        return
    
    # Calculer l'engagement moyen
    avg_engagement = metadata.get('total_engagement', 0) / len(posts) if posts else 0
    print(f"  📊 Engagement moyen/post: {format_number(int(avg_engagement))}")
    
    # Afficher les 10 derniers posts
    print(f"\n{'='*80}")
    print(f"📰 LES {min(10, len(posts))} DERNIERS POSTS")
    print(f"{'='*80}\n")
    
    for i, post in enumerate(posts[:10], 1):
        print(f"{'─'*80}")
        print(f"Post #{i} - {post.get('date_post', 'Date inconnue')}")
        print(f"{'─'*80}")
        print(f"🆔 ID: {post.get('post_id', 'N/A')[:50]}...")
        print(f"📝 Contenu: {truncate_text(post.get('text', 'Pas de texte'), 150)}")
        print(f"🔗 URL: {post.get('url', 'N/A')}")
        print(f"\n📊 Métriques:")
        print(f"  👍 Likes: {format_number(post.get('likes', 0))}")
        print(f"  💬 Commentaires: {format_number(post.get('comments', 0))}")
        print(f"  🔄 Partages: {format_number(post.get('shares', 0))}")
        print(f"  💯 Engagement total: {format_number(post.get('engagement_total', 0))}")
        
        # Afficher les médias s'il y en a
        medias = post.get('medias', [])
        if medias:
            print(f"\n🖼️ Médias ({len(medias)}):")
            for j, media in enumerate(medias[:3], 1):
                print(f"  {j}. {media.get('type', 'unknown')}: {truncate_text(media.get('url', 'N/A'), 80)}")
        
        print()
    
    # Afficher le top 5 des posts les plus engageants
    if len(posts) > 1:
        print(f"\n{'='*80}")
        print(f"🔥 TOP 5 DES POSTS LES PLUS ENGAGEANTS")
        print(f"{'='*80}\n")
        
        sorted_posts = sorted(posts, key=lambda x: x.get('engagement_total', 0), reverse=True)
        
        for i, post in enumerate(sorted_posts[:5], 1):
            print(f"{i}. 💯 {format_number(post.get('engagement_total', 0))} - {truncate_text(post.get('text', 'Sans texte'), 80)}")
            print(f"   📅 {post.get('date_post', 'Date inconnue')}")
            print()
    
    print("="*80 + "\n")


def main():
    """Point d'entrée principal"""
    # Essayer d'abord le fichier de monitoring temps réel
    if os.path.exists('fasopresse_realtime.json'):
        view_fasopresse_data('fasopresse_realtime.json')
    # Sinon, essayer le fichier de scraping unique
    elif os.path.exists('fasopresse_posts.json'):
        view_fasopresse_data('fasopresse_posts.json')
    else:
        print("❌ Aucun fichier de données Fasopresse trouvé.")
        print("Fichiers recherchés:")
        print("  - fasopresse_realtime.json")
        print("  - fasopresse_posts.json")


if __name__ == "__main__":
    main()
