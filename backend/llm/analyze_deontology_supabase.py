#!/usr/bin/env python3
"""
Script d'analyse déontologique des articles journalistiques (Version Supabase)
Utilise Mistral AI pour évaluer le respect des principes déontologiques
"""

import os
import json
import sys
from supabase import create_client, Client
from mistralai import Mistral
from datetime import datetime
from typing import Dict, List, Optional


class DeontologyAnalyzer:
    """Analyseur déontologique pour articles de presse"""
    
    def __init__(self, supabase_url: str, supabase_key: str, mistral_api_key: str):
        """
        Initialise l'analyseur
        
        Args:
            supabase_url: URL du projet Supabase
            supabase_key: Clé API Supabase (service_role ou anon)
            mistral_api_key: Clé API Mistral
        """
        # Connexion Supabase
        self.supabase: Client = create_client(supabase_url, supabase_key)
        print("✓ Connexion à Supabase établie")
        
        # Configuration de Mistral
        self.client = Mistral(api_key=mistral_api_key)
        self.agent_id = "ag_019a926beb4374319d62c50ea1c5d9b3"
        print("✓ Client Mistral initialisé")

    def get_articles(self, limit: Optional[int] = None, article_id: Optional[str] = None) -> List[Dict]:
        """
        Récupère les articles de la base de données Supabase
        
        Args:
            limit: Nombre maximum d'articles à récupérer
            article_id: ID spécifique d'un article (optionnel)
            
        Returns:
            Liste des articles avec leurs informations
        """
        try:
            query = self.supabase.table('articles').select(
                'id, titre, contenu, url, date, '
                'medias(name, type), '
                'categories(nom)'
            )
            
            # Filtre : articles avec contenu non nul
            query = query.not_.is_('contenu', 'null')
            
            if article_id:
                query = query.eq('id', article_id)
            else:
                query = query.order('date', desc=True)
                if limit:
                    query = query.limit(limit)
            
            response = query.execute()
            
            # Transformation des données
            articles = []
            for item in response.data:
                articles.append({
                    'id': item['id'],
                    'titre': item['titre'],
                    'contenu': item['contenu'],
                    'url': item['url'],
                    'date': item['date'],
                    'media_name': item['medias']['name'] if item.get('medias') else None,
                    'media_type': item['medias']['type'] if item.get('medias') else None,
                    'categorie': item['categories']['nom'] if item.get('categories') else None
                })
            
            return articles
                
        except Exception as e:
            print(f"✗ Erreur lors de la récupération des articles : {e}")
            return []

    def analyze_content(self, titre: str, contenu: str) -> Dict:
        """
        Analyse le contenu d'un article avec Mistral
        
        Args:
            titre: Titre de l'article
            contenu: Contenu de l'article
            
        Returns:
            Dictionnaire avec interpretation et score
        """
        try:
            # Vérifier la longueur du contenu
            MAX_CHARS = 15000
            texte_a_analyser = contenu
            
            if len(contenu) > MAX_CHARS:
                print(f"  ⚠️  Article long ({len(contenu)} chars), troncature...")
                texte_a_analyser = contenu[:MAX_CHARS]
            
            # Préparation du prompt
            prompt = f"""Tu es un expert en analyse déontologique du contenu journalistique.

Analyse ce texte et réponds UNIQUEMENT avec un JSON strict :

{{
  "interpretation": "Description en 2 lignes de l'analyse déontologique",
  "score": 0-10
}}

Critères : véracité, diffamation, incitation à la haine, insultes, manipulation, ton biaisé, intégrité.

Score : 10=excellent, 7-9=bon, 4-6=problèmes, 0-3=graves manquements, -1=impossible d'analyser

TITRE : {titre}

CONTENU : {texte_a_analyser}

Réponds UNIQUEMENT avec le JSON, rien d'autre."""

            # Appel à Mistral
            response = self.client.chat.complete(
                model="open-mistral-7b",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # FALLBACK : Vérifier si la réponse existe
            if not response or not response.choices:
                print(f"  ⚠️  Réponse vide du modèle")
                return {
                    'interpretation': "Réponse vide du modèle",
                    'score': -1
                }
            
            # Extraction de la réponse
            response_text = response.choices[0].message.content.strip()
            
            # FALLBACK : Si le texte est vide
            if not response_text:
                return {
                    'interpretation': "Réponse textuelle vide",
                    'score': -1
                }
            
            # Nettoyer la réponse si elle contient des marqueurs markdown
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            result = json.loads(response_text)
            
            # Validation du format
            if 'interpretation' not in result or 'score' not in result:
                raise ValueError("Format de réponse invalide")
            
            # Validation du score
            score = int(result['score'])
            if score < -1 or score > 10:
                raise ValueError(f"Score invalide : {score}")
            
            return {
                'interpretation': result['interpretation'],
                'score': score
            }
            
        except json.JSONDecodeError as e:
            print(f"✗ Erreur de parsing JSON : {e}")
            print(f"Réponse brute : {response_text[:200] if 'response_text' in locals() else 'N/A'}")
            return {
                'interpretation': "Erreur de parsing JSON : réponse invalide du modèle",
                'score': -1
            }
        except Exception as e:
            print(f"✗ Erreur lors de l'analyse Mistral : {e}")
            return {
                'interpretation': f"Erreur d'analyse : {str(e)[:100]}",
                'score': -1
            }

    def analyze_article(self, article: Dict) -> Dict:
        """
        Analyse un article complet
        
        Args:
            article: Dictionnaire contenant les informations de l'article
            
        Returns:
            Résultat complet de l'analyse
        """
        print(f"\n→ Analyse de l'article : {article['id']}")
        print(f"  Titre : {article['titre'][:60]}...")
        
        # Analyse déontologique
        analysis = self.analyze_content(article['titre'], article['contenu'])
        
        # Résultat complet
        result = {
            'article_id': article['id'],
            'titre': article['titre'],
            'media': article['media_name'],
            'categorie': article['categorie'],
            'date': article['date'],
            'url': article['url'],
            'analyse': analysis,
            'timestamp_analyse': datetime.now().isoformat()
        }
        
        return result

    def run(self, limit: Optional[int] = None, article_id: Optional[str] = None, output_file: Optional[str] = None):
        """
        Execute l'analyse sur les articles
        
        Args:
            limit: Nombre d'articles à analyser
            article_id: ID d'un article spécifique
            output_file: Fichier de sortie pour les résultats (optionnel)
        """
        try:
            # Récupération des articles
            articles = self.get_articles(limit=limit, article_id=article_id)
            
            if not articles:
                print("✗ Aucun article trouvé")
                return
            
            print(f"\n📊 {len(articles)} article(s) à analyser\n")
            print("=" * 80)
            
            # Analyse de chaque article
            results = []
            for i, article in enumerate(articles, 1):
                print(f"\n[{i}/{len(articles)}]")
                result = self.analyze_article(article)
                results.append(result)
                
                # Affichage du résultat
                print(f"  ✓ Score déontologique : {result['analyse']['score']}/10")
                print(f"  📝 {result['analyse']['interpretation']}")
            
            print("\n" + "=" * 80)
            print("\n📄 RÉSUMÉ DES ANALYSES\n")
            
            # Affichage du résumé
            for result in results:
                score = result['analyse']['score']
                emoji = self._get_score_emoji(score)
                print(f"{emoji} {score}/10 - {result['titre'][:50]}...")
            
            # Statistiques
            valid_scores = [r['analyse']['score'] for r in results if r['analyse']['score'] >= 0]
            if valid_scores:
                avg_score = sum(valid_scores) / len(valid_scores)
                print(f"\n📈 Score moyen : {avg_score:.1f}/10")
            
            # Sauvegarde dans un fichier si demandé
            if output_file:
                self._save_results(results, output_file)
            
            # Affichage JSON complet
            print("\n" + "=" * 80)
            print("📋 RÉSULTATS COMPLETS (JSON)\n")
            print(json.dumps(results, indent=2, ensure_ascii=False))
            
        except Exception as e:
            print(f"✗ Erreur lors de l'exécution : {e}")
            import traceback
            traceback.print_exc()

    def _get_score_emoji(self, score: int) -> str:
        """Retourne un emoji selon le score"""
        if score >= 8:
            return "✅"
        elif score >= 6:
            return "⚠️"
        elif score >= 4:
            return "⚠️"
        elif score >= 0:
            return "❌"
        else:
            return "⚠️"

    def _save_results(self, results: List[Dict], filename: str):
        """Sauvegarde les résultats dans un fichier JSON"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n✓ Résultats sauvegardés dans : {filename}")
        except Exception as e:
            print(f"\n✗ Erreur lors de la sauvegarde : {e}")


def main():
    """Point d'entrée principal"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Analyse déontologique d'articles journalistiques avec Mistral AI"
    )
    parser.add_argument(
        '--limit', 
        type=int, 
        help="Nombre d'articles à analyser (défaut: tous)"
    )
    parser.add_argument(
        '--article-id', 
        type=str, 
        help="ID d'un article spécifique à analyser"
    )
    parser.add_argument(
        '--output', 
        type=str, 
        help="Fichier de sortie pour les résultats JSON"
    )
    parser.add_argument(
        '--env',
        type=str,
        default='.env',
        help="Fichier .env (défaut: .env)"
    )
    
    args = parser.parse_args()
    
    # Chargement depuis .env
    try:
        if os.path.exists(args.env):
            from dotenv import load_dotenv
            load_dotenv(args.env)
            
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_ANON_KEY')
            mistral_api_key = os.getenv('MISTRAL_API_KEY')
            
            if not supabase_url or not supabase_key:
                print("✗ Variables SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY/SUPABASE_ANON_KEY requises dans .env")
                sys.exit(1)
            
            if not mistral_api_key:
                print("✗ Variable MISTRAL_API_KEY requise dans .env")
                print("\nAjoutez dans votre .env :")
                print("MISTRAL_API_KEY=votre_clé_mistral")
                sys.exit(1)
        else:
            print(f"✗ Fichier '{args.env}' introuvable")
            sys.exit(1)
    except Exception as e:
        print(f"✗ Erreur lors de la lecture de .env : {e}")
        sys.exit(1)
    
    # Initialisation et exécution
    try:
        analyzer = DeontologyAnalyzer(
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            mistral_api_key=mistral_api_key
        )
        
        analyzer.run(
            limit=args.limit,
            article_id=args.article_id,
            output_file=args.output
        )
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Analyse interrompue par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Erreur fatale : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
