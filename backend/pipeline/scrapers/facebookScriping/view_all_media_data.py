"""
Visualisation Consolidée de Toutes les Données des Médias
Affiche un résumé des posts collectés pour tous les médias
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List


class AllMediaDataViewer:
    """Visualisateur consolidé pour tous les médias"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.media_configs = {
            'Burkina24': {
                'folder': 'Jesus_aide_moi_burkina24',
                'file': 'burkina24_realtime.json'
            },
            'Lefaso.net': {
                'folder': 'Jesus_aide_moi_fasonet',
                'file': 'lefaso_realtime.json'
            },
            'Fasopresse': {
                'folder': 'Jesus_aide_moi_fasopresse',
                'file': 'fasopresse_realtime.json'
            },
            'ESidwaya': {
                'folder': 'Jesus_aide_moi_sidwaya',
                'file': 'esidwaya_realtime.json'
            },
            'Observateur Paalga': {
                'folder': 'Jesus_aide_moi_observateurpaalga',
                'file': 'observateur_paalga_stream.json'
            }
        }
        self.all_data = {}
    
    def load_media_data(self, media_name: str, config: Dict) -> Dict:
        """
        Charge les données d'un média
        
        Args:
            media_name: Nom du média
            config: Configuration du média
            
        Returns:
            Dictionnaire avec les données du média
        """
        json_path = self.base_path / config['folder'] / config['file']
        
        if not json_path.exists():
            return {
                'status': 'missing',
                'posts': [],
                'total': 0,
                'message': f"Fichier non trouvé: {config['file']}"
            }
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                posts = data.get('posts', [])
                return {
                    'status': 'ok',
                    'posts': posts,
                    'total': len(posts),
                    'metadata': data.get('metadata', {}),
                    'file': str(json_path)
                }
        except Exception as e:
            return {
                'status': 'error',
                'posts': [],
                'total': 0,
                'message': f"Erreur de lecture: {e}"
            }
    
    def load_all_data(self):
        """Charge les données de tous les médias"""
        print("\n🔄 Chargement des données de tous les médias...\n")
        
        for media_name, config in self.media_configs.items():
            self.all_data[media_name] = self.load_media_data(media_name, config)
            
            status = self.all_data[media_name]['status']
            total = self.all_data[media_name]['total']
            
            if status == 'ok':
                print(f"✅ {media_name:20s} - {total:4d} posts")
            elif status == 'missing':
                print(f"⚠️  {media_name:20s} - Pas de données")
            else:
                print(f"❌ {media_name:20s} - Erreur")
        
        print()
    
    def print_summary(self):
        """Affiche un résumé global"""
        print("=" * 100)
        print(" " * 35 + "RÉSUMÉ GLOBAL DES MÉDIAS")
        print("=" * 100)
        
        total_posts = sum(data['total'] for data in self.all_data.values())
        active_medias = sum(1 for data in self.all_data.values() if data['status'] == 'ok' and data['total'] > 0)
        
        print(f"\n📊 Total des posts collectés: {total_posts}")
        print(f"📡 Médias actifs: {active_medias}/{len(self.media_configs)}")
        print(f"🕐 Date de consultation: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        print("=" * 100)
    
    def print_media_details(self, media_name: str, limit: int = 5):
        """
        Affiche les détails d'un média
        
        Args:
            media_name: Nom du média
            limit: Nombre de posts récents à afficher
        """
        data = self.all_data.get(media_name, {})
        
        print(f"\n{'=' * 100}")
        print(f"  📰 {media_name}")
        print(f"{'=' * 100}")
        
        if data['status'] != 'ok':
            print(f"\n⚠️  {data.get('message', 'Données non disponibles')}\n")
            return
        
        posts = data['posts']
        total = data['total']
        
        print(f"\n📊 Total de posts: {total}")
        
        if data.get('metadata'):
            metadata = data['metadata']
            print(f"📅 Dernière mise à jour: {metadata.get('last_updated', 'N/A')}")
            if 'total_reactions' in metadata:
                print(f"❤️  Total réactions: {metadata.get('total_reactions', 0):,}")
            if 'total_comments' in metadata:
                print(f"💬 Total commentaires: {metadata.get('total_comments', 0):,}")
            if 'total_shares' in metadata:
                print(f"🔄 Total partages: {metadata.get('total_shares', 0):,}")
        
        if not posts:
            print("\n📭 Aucun post disponible\n")
            return
        
        # Afficher les posts récents
        print(f"\n📝 {min(limit, len(posts))} posts les plus récents:\n")
        
        for i, post in enumerate(posts[:limit], 1):
            print(f"  [{i}] Post ID: {post.get('post_id', 'N/A')}")
            print(f"      📅 Date: {post.get('date_post', 'N/A')}")
            
            # Texte du post (tronqué)
            text = post.get('text', '')
            if text:
                text_preview = text[:100] + "..." if len(text) > 100 else text
                print(f"      📄 Texte: {text_preview}")
            
            # Métriques
            reactions = post.get('reactions', 0)
            comments = post.get('comments', 0)
            shares = post.get('shares', 0)
            
            print(f"      📊 Métriques: ❤️  {reactions:,} | 💬 {comments:,} | 🔄 {shares:,}")
            
            # URL si disponible
            if 'url' in post:
                print(f"      🔗 URL: {post['url']}")
            
            print()
    
    def print_all_details(self, posts_per_media: int = 3):
        """
        Affiche les détails de tous les médias
        
        Args:
            posts_per_media: Nombre de posts à afficher par média
        """
        for media_name in self.media_configs.keys():
            self.print_media_details(media_name, limit=posts_per_media)
    
    def print_latest_posts_all_media(self, limit: int = 10):
        """
        Affiche les derniers posts de tous les médias mélangés
        
        Args:
            limit: Nombre total de posts à afficher
        """
        print(f"\n{'=' * 100}")
        print(f"  🔥 {limit} DERNIERS POSTS - TOUS MÉDIAS CONFONDUS")
        print(f"{'=' * 100}\n")
        
        # Collecter tous les posts avec leur média
        all_posts = []
        for media_name, data in self.all_data.items():
            if data['status'] == 'ok':
                for post in data['posts']:
                    post_with_media = post.copy()
                    post_with_media['media_name'] = media_name
                    all_posts.append(post_with_media)
        
        if not all_posts:
            print("📭 Aucun post disponible\n")
            return
        
        # Trier par date (plus récents en premier)
        all_posts.sort(key=lambda x: x.get('date_post', ''), reverse=True)
        
        # Afficher les N premiers
        for i, post in enumerate(all_posts[:limit], 1):
            media = post['media_name']
            print(f"  [{i}] 📰 {media}")
            print(f"      Post ID: {post.get('post_id', 'N/A')}")
            print(f"      📅 Date: {post.get('date_post', 'N/A')}")
            
            text = post.get('text', '')
            if text:
                text_preview = text[:80] + "..." if len(text) > 80 else text
                print(f"      📄 {text_preview}")
            
            reactions = post.get('reactions', 0)
            comments = post.get('comments', 0)
            shares = post.get('shares', 0)
            
            print(f"      📊 ❤️  {reactions:,} | 💬 {comments:,} | 🔄 {shares:,}")
            print()
    
    def export_consolidated_json(self, output_file: str = 'all_media_consolidated.json'):
        """
        Exporte toutes les données dans un seul fichier JSON
        
        Args:
            output_file: Nom du fichier de sortie
        """
        output_path = self.base_path / output_file
        
        consolidated = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_medias': len(self.media_configs),
                'total_posts': sum(data['total'] for data in self.all_data.values())
            },
            'medias': {}
        }
        
        for media_name, data in self.all_data.items():
            if data['status'] == 'ok':
                consolidated['medias'][media_name] = {
                    'total_posts': data['total'],
                    'posts': data['posts'],
                    'metadata': data.get('metadata', {})
                }
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(consolidated, f, ensure_ascii=False, indent=2)
            print(f"\n✅ Données consolidées exportées vers: {output_path}\n")
        except Exception as e:
            print(f"\n❌ Erreur lors de l'export: {e}\n")
    
    def interactive_menu(self):
        """Menu interactif pour naviguer dans les données"""
        while True:
            print("\n" + "=" * 100)
            print(" " * 35 + "MENU PRINCIPAL")
            print("=" * 100)
            print("\n  1. Afficher le résumé global")
            print("  2. Afficher les détails de tous les médias")
            print("  3. Afficher les détails d'un média spécifique")
            print("  4. Afficher les derniers posts (tous médias)")
            print("  5. Exporter les données consolidées (JSON)")
            print("  6. Recharger les données")
            print("  0. Quitter")
            print("\n" + "=" * 100)
            
            choice = input("\n👉 Votre choix: ").strip()
            
            if choice == '1':
                self.print_summary()
            
            elif choice == '2':
                limit = input("\n📝 Nombre de posts par média (défaut: 3): ").strip()
                limit = int(limit) if limit.isdigit() else 3
                self.print_all_details(posts_per_media=limit)
            
            elif choice == '3':
                print("\n📰 Médias disponibles:")
                for i, media_name in enumerate(self.media_configs.keys(), 1):
                    total = self.all_data[media_name]['total']
                    print(f"  {i}. {media_name} ({total} posts)")
                
                media_choice = input("\n👉 Numéro du média: ").strip()
                if media_choice.isdigit():
                    idx = int(media_choice) - 1
                    media_names = list(self.media_configs.keys())
                    if 0 <= idx < len(media_names):
                        limit = input("📝 Nombre de posts à afficher (défaut: 5): ").strip()
                        limit = int(limit) if limit.isdigit() else 5
                        self.print_media_details(media_names[idx], limit=limit)
            
            elif choice == '4':
                limit = input("\n📝 Nombre de posts à afficher (défaut: 10): ").strip()
                limit = int(limit) if limit.isdigit() else 10
                self.print_latest_posts_all_media(limit=limit)
            
            elif choice == '5':
                filename = input("\n📁 Nom du fichier (défaut: all_media_consolidated.json): ").strip()
                filename = filename if filename else 'all_media_consolidated.json'
                self.export_consolidated_json(filename)
            
            elif choice == '6':
                self.load_all_data()
                self.print_summary()
            
            elif choice == '0':
                print("\n👋 Au revoir!\n")
                break
            
            else:
                print("\n❌ Choix invalide. Veuillez réessayer.")
    
    def run(self):
        """Fonction principale"""
        print("\n" + "=" * 100)
        print(" " * 25 + "VISUALISATION CONSOLIDÉE - TOUS LES MÉDIAS")
        print("=" * 100)
        
        self.load_all_data()
        self.print_summary()
        self.interactive_menu()


def main():
    """Point d'entrée du programme"""
    viewer = AllMediaDataViewer()
    viewer.run()


if __name__ == '__main__':
    main()
