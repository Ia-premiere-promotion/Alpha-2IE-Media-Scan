"""
Script d'Agrégation Automatique - Tous les Médias
Consolide tous les fichiers JSON des médias dans un seul fichier
Se met à jour automatiquement en temps réel
"""

import json
import os
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List


class MediaDataAggregator:
    """Agrégateur automatique de données de tous les médias"""
    
    def __init__(self, output_file: str = 'all_media_consolidated.json', watch_interval: int = 60):
        """
        Initialise l'agrégateur
        
        Args:
            output_file: Nom du fichier JSON consolidé
            watch_interval: Intervalle de mise à jour en secondes (défaut: 60s = 1 min)
        """
        self.base_path = Path(__file__).parent
        self.output_file = self.base_path / output_file
        self.watch_interval = watch_interval
        
        # Configuration des médias et leurs fichiers JSON
        self.media_sources = {
            'Burkina24': {
                'folder': 'facebook_burkina24',
                'file': 'burkina24_realtime.json',
                'page_url': 'https://web.facebook.com/Burkina24'
            },
            'Lefaso.net': {
                'folder': 'facebook_fasonet',
                'file': 'lefaso_realtime.json',
                'page_url': 'https://web.facebook.com/lefaso.net'
            },
            'Fasopresse': {
                'folder': 'facebook_fasopresse',
                'file': 'fasopresse_realtime.json',
                'page_url': 'https://web.facebook.com/p/Fasopresse-Lactualité-du-Burkina-Faso-100067981629793/'
            },
            'ESidwaya': {
                'folder': 'faccebook_sidwaya',
                'file': 'esidwaya_realtime.json',
                'page_url': 'https://web.facebook.com/ESidwaya'
            },
            'Observateur Paalga': {
                'folder': 'facebook_observateurpaalga',
                'file': 'observateur_paalga_stream.json',
                'page_url': 'https://web.facebook.com/lobspaalgaBF'
            }
        }
        
        self.last_modified_times = {}
    
    def read_media_file(self, media_name: str, config: Dict) -> Dict:
        """
        Lit le fichier JSON d'un média
        
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
                'total_posts': 0,
                'last_update': None
            }
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                posts = data.get('posts', [])
                
                # Ajouter le nom du média à chaque post
                for post in posts:
                    post['media_source'] = media_name
                    post['media_page_url'] = config['page_url']
                
                return {
                    'status': 'ok',
                    'posts': posts,
                    'total_posts': len(posts),
                    'last_update': data.get('metadata', {}).get('last_update', None),
                    'metadata': data.get('metadata', {})
                }
        except Exception as e:
            print(f"❌ [{media_name}] Erreur de lecture: {e}")
            return {
                'status': 'error',
                'posts': [],
                'total_posts': 0,
                'last_update': None,
                'error': str(e)
            }
    
    def aggregate_all_data(self) -> Dict:
        """
        Agrège les données de tous les médias
        
        Returns:
            Dictionnaire consolidé de toutes les données
        """
        all_posts = []
        media_stats = {}
        
        for media_name, config in self.media_sources.items():
            data = self.read_media_file(media_name, config)
            
            if data['status'] == 'ok':
                all_posts.extend(data['posts'])
                media_stats[media_name] = {
                    'total_posts': data['total_posts'],
                    'last_update': data['last_update'],
                    'page_url': config['page_url'],
                    'status': 'active'
                }
                
                # Calculer les métriques si disponibles
                if data.get('metadata'):
                    metadata = data['metadata']
                    media_stats[media_name].update({
                        'total_reactions': metadata.get('total_reactions', metadata.get('total_likes', metadata.get('total_engagement', 0))),
                        'total_comments': metadata.get('total_comments', 0),
                        'total_shares': metadata.get('total_shares', 0)
                    })
            else:
                media_stats[media_name] = {
                    'total_posts': 0,
                    'last_update': None,
                    'page_url': config['page_url'],
                    'status': data['status']
                }
        
        # Trier tous les posts par date (plus récents en premier)
        all_posts.sort(key=lambda x: x.get('date_post', ''), reverse=True)
        
        # Calculer les statistiques globales
        total_reactions = sum(p.get('reactions', p.get('likes', p.get('engagement_total', 0))) for p in all_posts)
        total_comments = sum(p.get('comments', 0) for p in all_posts)
        total_shares = sum(p.get('shares', 0) for p in all_posts)
        total_engagement = total_reactions + total_comments + total_shares
        
        # Construire le document consolidé
        consolidated = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_medias': len(self.media_sources),
                'active_medias': sum(1 for stat in media_stats.values() if stat['status'] == 'ok'),
                'total_posts': len(all_posts),
                'total_reactions': total_reactions,
                'total_comments': total_comments,
                'total_shares': total_shares,
                'total_engagement': total_engagement,
                'watch_interval_seconds': self.watch_interval
            },
            'media_stats': media_stats,
            'all_posts': all_posts
        }
        
        return consolidated
    
    def save_consolidated_data(self, data: Dict) -> bool:
        """
        Sauvegarde les données consolidées
        
        Args:
            data: Données consolidées à sauvegarder
            
        Returns:
            True si succès, False sinon
        """
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")
            return False
    
    def check_for_updates(self) -> bool:
        """
        Vérifie si des fichiers sources ont été modifiés
        
        Returns:
            True si au moins un fichier a changé, False sinon
        """
        has_updates = False
        
        for media_name, config in self.media_sources.items():
            json_path = self.base_path / config['folder'] / config['file']
            
            if json_path.exists():
                current_mtime = json_path.stat().st_mtime
                last_mtime = self.last_modified_times.get(media_name, 0)
                
                if current_mtime > last_mtime:
                    has_updates = True
                    self.last_modified_times[media_name] = current_mtime
        
        return has_updates
    
    def print_stats(self, data: Dict):
        """
        Affiche les statistiques de l'agrégation
        
        Args:
            data: Données consolidées
        """
        metadata = data['metadata']
        
        print(f"\n{'=' * 80}")
        print(f"📊 AGRÉGATION COMPLÉTÉE - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'=' * 80}")
        print(f"📡 Médias actifs: {metadata['active_medias']}/{metadata['total_medias']}")
        print(f"📝 Total posts: {metadata['total_posts']:,}")
        print(f"❤️  Total réactions: {metadata['total_reactions']:,}")
        print(f"💬 Total commentaires: {metadata['total_comments']:,}")
        print(f"🔄 Total partages: {metadata['total_shares']:,}")
        print(f"📊 Engagement total: {metadata['total_engagement']:,}")
        print(f"\n💾 Fichier: {self.output_file}")
        print(f"⏱️  Prochain update: {self.watch_interval}s")
        print(f"{'=' * 80}\n")
        
        # Détails par média
        for media_name, stats in data['media_stats'].items():
            status_icon = "✅" if stats['status'] == 'active' else "⚠️"
            print(f"{status_icon} {media_name:20s} - {stats['total_posts']:4d} posts")
    
    def run_once(self):
        """Exécute une seule agrégation"""
        print("\n🔄 Agrégation des données...")
        data = self.aggregate_all_data()
        
        if self.save_consolidated_data(data):
            self.print_stats(data)
            return True
        return False
    
    def run_continuous(self):
        """Exécute l'agrégation en continu avec surveillance des changements"""
        print("=" * 80)
        print(" " * 20 + "AGRÉGATEUR AUTOMATIQUE - TOUS LES MÉDIAS")
        print("=" * 80)
        print(f"\n⏱️  Intervalle de mise à jour: {self.watch_interval} secondes")
        print(f"💾 Fichier de sortie: {self.output_file}")
        print(f"📡 Médias surveillés: {len(self.media_sources)}")
        print("\n⚠️  Appuyez sur Ctrl+C pour arrêter\n")
        print("=" * 80)
        
        iteration = 0
        
        try:
            while True:
                iteration += 1
                print(f"\n🔄 Itération #{iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Vérifier les mises à jour
                if iteration == 1 or self.check_for_updates():
                    if iteration > 1:
                        print("✨ Nouveaux changements détectés!")
                    
                    # Agréger et sauvegarder
                    data = self.aggregate_all_data()
                    
                    if self.save_consolidated_data(data):
                        self.print_stats(data)
                    else:
                        print("❌ Erreur lors de la sauvegarde")
                else:
                    print("⏭️  Aucun changement détecté, attente...")
                
                # Attendre avant la prochaine vérification
                print(f"💤 Attente de {self.watch_interval} secondes...\n")
                time.sleep(self.watch_interval)
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Arrêt demandé (Ctrl+C)")
            print("\n" + "=" * 80)
            print("🏁 Agrégateur arrêté")
            print("=" * 80 + "\n")


def main():
    """Point d'entrée du programme"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Agrégateur automatique de données médias')
    parser.add_argument(
        '--output',
        default='all_media_consolidated.json',
        help='Nom du fichier JSON consolidé (défaut: all_media_consolidated.json)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Intervalle de mise à jour en secondes (défaut: 60)'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Exécuter une seule fois puis arrêter'
    )
    
    args = parser.parse_args()
    
    aggregator = MediaDataAggregator(
        output_file=args.output,
        watch_interval=args.interval
    )
    
    if args.once:
        # Mode une seule fois
        aggregator.run_once()
    else:
        # Mode continu (par défaut)
        aggregator.run_continuous()


if __name__ == '__main__':
    main()
