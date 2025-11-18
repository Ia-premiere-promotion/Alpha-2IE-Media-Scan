"""
Script pour visualiser les données du JSON ESidwaya de manière formatée
"""

import json
import os
from datetime import datetime

def view_json():
    """Affiche le contenu du JSON de manière formatée"""
    json_file = 'esidwaya_realtime.json'
    
    if not os.path.exists(json_file):
        print(f"❌ Fichier {json_file} introuvable")
        return
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    posts = data.get('posts', [])
    metadata = data.get('metadata', {})
    
    print("=" * 100)
    print("📊 MÉTRIQUES ESIDWAYA - VUE D'ENSEMBLE")
    print("=" * 100)
    
    if not posts:
        print("📭 Aucun post dans le JSON")
        return
    
    print(f"\n📁 Total posts: {metadata.get('total_posts', len(posts))}")
    print(f"📊 Engagement total: {metadata.get('total_engagement', 0)}")
    print(f"👍 Total likes: {metadata.get('total_likes', 0)}")
    print(f"💬 Total comments: {metadata.get('total_comments', 0)}")
    print(f"🔄 Total shares: {metadata.get('total_shares', 0)}")
    print(f"🕐 Dernière MAJ: {metadata.get('last_update', 'N/A')[:19]}")
    print("\n" + "=" * 100)
    
    # Afficher chaque post
    for i, post in enumerate(posts, 1):
        print(f"\n{i}. POST ID: {post.get('post_id', 'N/A')}")
        print(f"   📅 Date: {post.get('date_post', 'N/A')[:19]}")
        print(f"   📝 Contenu: {post.get('contenu', '')[:80]}...")
        print(f"   👍 Likes: {post.get('likes', 0)}")
        print(f"   💬 Comments: {post.get('comments', 0)}")
        print(f"   🔄 Shares: {post.get('shares', 0)}")
        print(f"   📊 Engagement: {post.get('engagement_total', 0)}")
        print(f"   🕐 Dernière MAJ: {post.get('last_update', 'N/A')[:19]}")
        print(f"   🔗 URL: {post.get('url', '')[:60]}...")
        print("   " + "-" * 96)
    
    # Top 3 posts
    print("\n" + "=" * 100)
    print("🏆 TOP 3 POSTS PAR ENGAGEMENT:")
    print("=" * 100)
    
    sorted_posts = sorted(posts, key=lambda x: x.get('engagement_total', 0), reverse=True)[:3]
    for i, post in enumerate(sorted_posts, 1):
        print(f"\n{i}. {post.get('contenu', '')[:70]}...")
        print(f"   📊 {post.get('engagement_total', 0)} engagement (👍 {post.get('likes', 0)} | 💬 {post.get('comments', 0)} | 🔄 {post.get('shares', 0)})")
    
    print("\n" + "=" * 100)

if __name__ == "__main__":
    view_json()
