"""
Script Principal de Monitoring en Temps Réel - Tous les Médias
Lance tous les scrapers en parallèle pour surveiller tous les médias simultanément
"""

import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime
import threading
import time

# Fix encoding issues on Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


class MasterRealtimeMonitor:
    """Gestion centralisée du monitoring de tous les médias"""
    
    def __init__(self, enable_aggregator: bool = True):
        self.base_path = Path(__file__).parent
        self.enable_aggregator = enable_aggregator
        self.aggregator_process = None
        self.aggregator_thread = None
        
        self.monitors = {
            'Burkina24': {
                'folder': 'facebook_burkina24',
                'script': 'burkina24_realtime_monitor.py',
                'process': None,
                'thread': None
            },
            'Lefaso.net': {
                'folder': 'facebook_fasonet',
                'script': 'lefaso_realtime_monitor.py',
                'process': None,
                'thread': None
            },
            'Fasopresse': {
                'folder': 'facebook_fasopresse',
                'script': 'fasopresse_realtime_monitor.py',
                'process': None,
                'thread': None
            },
            'ESidwaya': {
                'folder': 'faccebook_sidwaya',
                'script': 'esidwaya_realtime_monitor.py',
                'process': None,
                'thread': None
            },
            'Observateur Paalga': {
                'folder': 'facebook_observateurpaalga',
                'script': 'facebook_realtime_monitor.py',
                'process': None,
                'thread': None
            }
        }
        self.running = True
    
    def print_header(self):
        """Affiche l'en-tête du programme"""
        print("=" * 80)
        print(" " * 20 + "MONITORING TEMPS RÉEL - TOUS LES MÉDIAS")
        print("=" * 80)
        print(f"\n🕐 Démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n📡 Médias surveillés: {len(self.monitors)}")
        for media in self.monitors.keys():
            print(f"   • {media}")
        
        if self.enable_aggregator:
            print(f"\n📊 Agrégation automatique: ACTIVÉE")
            print(f"   → Fichier consolidé: all_media_consolidated.json")
            print(f"   → Mis à jour automatiquement toutes les 60 secondes")
        
        print("\n" + "=" * 80)
        print("⚠️  IMPORTANT: Chaque média s'exécute dans son propre processus")
        print("⚠️  Appuyez sur Ctrl+C pour arrêter tous les monitors")
        print("=" * 80 + "\n")
    
    def run_monitor(self, media_name: str, config: dict):
        """
        Exécute un monitor dans un thread séparé
        
        Args:
            media_name: Nom du média
            config: Configuration du monitor
        """
        folder_path = self.base_path / config['folder']
        script_path = folder_path / config['script']
        
        if not script_path.exists():
            print(f"❌ [{media_name}] Script non trouvé: {script_path}")
            return
        
        print(f"🚀 [{media_name}] Démarrage du monitor...")
        print(f"   📁 Dossier: {folder_path}")
        print(f"   📄 Script: {config['script']}\n")
        
        try:
            # Lancer le processus Python dans le dossier du média
            process = subprocess.Popen(
                [sys.executable, config['script']],
                cwd=str(folder_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace'  # Remplace les caractères non décodables
            )
            
            config['process'] = process
            
            # Lire et afficher la sortie en temps réel
            while self.running and process.poll() is None:
                # Lire stdout
                line = process.stdout.readline()
                if line:
                    print(f"[{media_name}] {line.rstrip()}")
                
                # Vérifier stderr
                # Note: On ne lit pas stderr en continu pour éviter les blocages
                
                time.sleep(0.1)
            
            # Lire les dernières lignes après arrêt
            if process.poll() is not None:
                remaining_output = process.stdout.read()
                if remaining_output:
                    for line in remaining_output.split('\n'):
                        if line.strip():
                            print(f"[{media_name}] {line}")
                
                remaining_error = process.stderr.read()
                if remaining_error:
                    print(f"⚠️ [{media_name}] Erreurs:\n{remaining_error}")
                
                if process.returncode != 0:
                    print(f"❌ [{media_name}] Terminé avec code d'erreur: {process.returncode}")
                else:
                    print(f"✅ [{media_name}] Terminé avec succès")
        
        except Exception as e:
            print(f"❌ [{media_name}] Erreur: {e}")
    
    def run_aggregator(self):
        """Exécute l'agrégateur dans un thread séparé"""
        aggregator_script = self.base_path / 'aggregate_all_media.py'
        
        if not aggregator_script.exists():
            print("⚠️  [Agrégateur] Script non trouvé, agrégation désactivée")
            return
        
        print("🚀 [Agrégateur] Démarrage de l'agrégation automatique...")
        print(f"   📁 Script: aggregate_all_media.py")
        print(f"   💾 Fichier: all_media_consolidated.json\n")
        
        try:
            process = subprocess.Popen(
                [sys.executable, 'aggregate_all_media.py', '--interval', '60'],
                cwd=str(self.base_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace'
            )
            
            self.aggregator_process = process
            
            # Lire et afficher la sortie en temps réel
            while self.running and process.poll() is None:
                line = process.stdout.readline()
                if line:
                    print(f"[Agrégateur] {line.rstrip()}")
                
                time.sleep(0.1)
            
            # Lire les dernières lignes après arrêt
            if process.poll() is not None:
                remaining_output = process.stdout.read()
                if remaining_output:
                    for line in remaining_output.split('\n'):
                        if line.strip():
                            print(f"[Agrégateur] {line}")
        
        except Exception as e:
            print(f"❌ [Agrégateur] Erreur: {e}")
    
    def start_all_monitors(self):
        """Démarre tous les monitors en parallèle"""
        threads = []
        
        # Démarrer l'agrégateur si activé
        if self.enable_aggregator:
            aggregator_thread = threading.Thread(
                target=self.run_aggregator,
                daemon=True
            )
            aggregator_thread.start()
            self.aggregator_thread = aggregator_thread
            threads.append(aggregator_thread)
            time.sleep(1)  # Laisser l'agrégateur démarrer
        
        for media_name, config in self.monitors.items():
            thread = threading.Thread(
                target=self.run_monitor,
                args=(media_name, config),
                daemon=True
            )
            thread.start()
            threads.append(thread)
            config['thread'] = thread
            time.sleep(2)  # Petit délai entre chaque démarrage
        
        return threads
    
    def stop_all_monitors(self):
        """Arrête tous les monitors en cours"""
        print("\n" + "=" * 80)
        print("🛑 Arrêt de tous les monitors en cours...")
        print("=" * 80 + "\n")
        
        self.running = False
        
        # Arrêter l'agrégateur en premier
        if self.aggregator_process and self.aggregator_process.poll() is None:
            print("⏹️  Arrêt de [Agrégateur]...")
            try:
                self.aggregator_process.terminate()
                self.aggregator_process.wait(timeout=5)
                print("✅ [Agrégateur] Arrêté")
            except subprocess.TimeoutExpired:
                print("⚠️  [Agrégateur] Force l'arrêt...")
                self.aggregator_process.kill()
                print("✅ [Agrégateur] Arrêté de force")
            except Exception as e:
                print(f"❌ [Agrégateur] Erreur lors de l'arrêt: {e}")
        
        # Arrêter les monitors
        for media_name, config in self.monitors.items():
            if config['process'] and config['process'].poll() is None:
                print(f"⏹️  Arrêt de [{media_name}]...")
                try:
                    config['process'].terminate()
                    config['process'].wait(timeout=5)
                    print(f"✅ [{media_name}] Arrêté")
                except subprocess.TimeoutExpired:
                    print(f"⚠️  [{media_name}] Force l'arrêt...")
                    config['process'].kill()
                    print(f"✅ [{media_name}] Arrêté de force")
                except Exception as e:
                    print(f"❌ [{media_name}] Erreur lors de l'arrêt: {e}")
    
    def check_dependencies(self):
        """Vérifie que les dépendances sont installées"""
        print("🔍 Vérification des dépendances...\n")
        
        missing_folders = []
        for media_name, config in self.monitors.items():
            folder_path = self.base_path / config['folder']
            script_path = folder_path / config['script']
            
            if not folder_path.exists():
                missing_folders.append(f"❌ Dossier manquant: {config['folder']}")
            elif not script_path.exists():
                missing_folders.append(f"❌ Script manquant: {script_path}")
            else:
                print(f"✅ [{media_name}] OK")
        
        if missing_folders:
            print("\n⚠️  PROBLÈMES DÉTECTÉS:")
            for msg in missing_folders:
                print(f"   {msg}")
            print("\n❌ Impossible de continuer. Vérifiez la structure des dossiers.\n")
            return False
        
        print("\n✅ Tous les scripts sont disponibles!\n")
        return True
    
    def run(self):
        """Fonction principale d'exécution"""
        self.print_header()
        
        # Vérifier les dépendances
        if not self.check_dependencies():
            return
        
        try:
            # Démarrer tous les monitors
            threads = self.start_all_monitors()
            
            # Attendre que tous les threads se terminent ou Ctrl+C
            print("\n" + "=" * 80)
            print("✅ Tous les monitors sont lancés!")
            print("📊 Les logs de chaque média s'afficheront ci-dessous")
            print("⌨️  Appuyez sur Ctrl+C pour arrêter tous les monitors")
            print("=" * 80 + "\n")
            
            # Attendre indéfiniment (jusqu'à Ctrl+C)
            for thread in threads:
                thread.join()
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Interruption détectée (Ctrl+C)")
        
        finally:
            self.stop_all_monitors()
            print("\n" + "=" * 80)
            print(f"🏁 Monitoring arrêté à {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 80 + "\n")


def main():
    """Point d'entrée du programme"""
    monitor = MasterRealtimeMonitor()
    monitor.run()


if __name__ == '__main__':
    main()
