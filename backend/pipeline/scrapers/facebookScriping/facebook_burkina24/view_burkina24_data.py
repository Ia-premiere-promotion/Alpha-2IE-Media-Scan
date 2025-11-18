"""
Visualiseur de données en temps réel pour Burkina24
Affiche les statistiques et les posts en temps réel
"""

import json
import os
from datetime import datetime
from collections import defaultdict


def load_data(filename='burkina24_realtime.json'):
    """Charge les données depuis le fichier JSON"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print(f"❌ Fichier {filename} introuvable")
            return None
    except Exception as e:
        print(f"❌ Erreur de chargement: {e}")
        return None


def display_statistics(data):
    """Affiche les statistiques globales"""
    if not data or 'posts' not in data:
        return
    
    posts = data['posts']
    metadata = data.get('metadata', {})
    
    print("="*70)
    print("📊 STATISTIQUES GLOBALES")
    print("="*70)
    print(f"Total posts: {metadata.get('total_posts', len(posts))}")
    print(f"Total engagement: {metadata.get('total_engagement', 0)}")
    print(f"Dernière mise à jour: {metadata.get('last_update', 'N/A')}")
    print(f"Page: {metadata.get('page', 'N/A')}")
    
    # Calculer les moyennes
    if posts:
        avg_likes = sum(p['likes'] for p in posts) / len(posts)
        avg_comments = sum(p['comments'] for p in posts) / len(posts)
        avg_shares = sum(p['shares'] for p in posts) / len(posts)
        
        print(f"\n📈 MOYENNES:")
        print(f"   Likes moyens: {avg_likes:.1f}")
        print(f"   Commentaires moyens: {avg_comments:.1f}")
        print(f"   Partages moyens: {avg_shares:.1f}")
    
    print("="*70)


def display_top_posts(data, top_n=5):
    """Affiche le top N des posts par engagement"""
    if not data or 'posts' not in data:
        return
    
    posts = data['posts']
    
    if not posts:
        print("\n❌ Aucun post disponible")
        return
    
    # Trier par engagement
    sorted_posts = sorted(posts, key=lambda x: x['engagement_total'], reverse=True)
    
    print(f"\n🏆 TOP {top_n} POSTS PAR ENGAGEMENT")
    print("="*70)
    
    for i, post in enumerate(sorted_posts[:top_n], 1):
        print(f"\n{i}. {post['contenu'][:100]}...")
        print(f"   URL: {post['url']}")
        print(f"   👍 {post['likes']} | 💬 {post['comments']} | 🔄 {post['shares']} = 📊 {post['engagement_total']}")
        print(f"   Publié: {post.get('date_post', 'N/A')}")
        
        # Afficher les commentaires s'il y en a
        if post.get('commentaires') and len(post['commentaires']) > 0:
            print(f"   📝 {len(post['commentaires'])} commentaires extraits:")
            for comment in post['commentaires'][:3]:  # Afficher les 3 premiers
                print(f"      • [{comment['auteur']}] {comment['texte'][:60]}...")


def display_recent_posts(data, recent_n=5):
    """Affiche les N posts les plus récents"""
    if not data or 'posts' not in data:
        return
    
    posts = data['posts']
    
    if not posts:
        return
    
    # Les posts sont déjà triés par date (plus récents en premier)
    print(f"\n🕐 {recent_n} POSTS LES PLUS RÉCENTS")
    print("="*70)
    
    for i, post in enumerate(posts[:recent_n], 1):
        print(f"\n{i}. {post['contenu'][:100]}...")
        print(f"   👍 {post['likes']} | 💬 {post['comments']} | 🔄 {post['shares']} = 📊 {post['engagement_total']}")


def watch_file(filename='burkina24_realtime.json', interval=5):
    """Surveille le fichier et affiche les mises à jour en temps réel"""
    import time
    
    print("="*70)
    print("👁️ MODE SURVEILLANCE EN TEMPS RÉEL")
    print("="*70)
    print(f"Fichier surveillé: {filename}")
    print(f"Intervalle de rafraîchissement: {interval} secondes")
    print(f"Appuyez sur Ctrl+C pour arrêter")
    print("="*70)
    
    last_update = None
    
    try:
        while True:
            data = load_data(filename)
            
            if data:
                current_update = data.get('metadata', {}).get('last_update')
                
                if current_update != last_update:
                    # Effacer l'écran (Windows)
                    os.system('cls' if os.name == 'nt' else 'clear')
                    
                    print(f"\n🔄 Mise à jour détectée: {datetime.now().strftime('%H:%M:%S')}\n")
                    
                    display_statistics(data)
                    display_top_posts(data, top_n=5)
                    display_recent_posts(data, recent_n=5)
                    
                    last_update = current_update
                    print(f"\n⏳ Prochaine vérification dans {interval} secondes...")
            
            time.sleep(interval)
    
    except KeyboardInterrupt:
        print("\n\n👋 Surveillance arrêtée")


def main():
    """Fonction principale"""
    import sys
    
    print("="*70)
    print("📊 VISUALISEUR DE DONNÉES - Burkina24")
    print("="*70)
    
    filename = 'burkina24_realtime.json'
    
    # Charger les données
    data = load_data(filename)
    
    if not data:
        print("\n❌ Aucune donnée disponible")
        print("💡 Lancez d'abord le monitoring avec: python burkina24_realtime_monitor.py")
        return
    
    # Afficher les statistiques
    display_statistics(data)
    display_top_posts(data, top_n=5)
    display_recent_posts(data, recent_n=5)
    
    # Proposer le mode surveillance
    print("\n" + "="*70)
    print("OPTIONS:")
    print("1. Rafraîchir l'affichage")
    print("2. Mode surveillance en temps réel")
    print("3. Quitter")
    
    try:
        choice = input("\nVotre choix (1-3): ").strip()
        
        if choice == '1':
            main()
        elif choice == '2':
            watch_file(filename, interval=5)
        else:
            print("👋 Au revoir!")
    
    except KeyboardInterrupt:
        print("\n\n👋 Au revoir!")


if __name__ == "__main__":
    main()
