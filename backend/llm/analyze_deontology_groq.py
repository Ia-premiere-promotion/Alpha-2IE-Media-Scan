#!/usr/bin/env python3
"""
Script d'analyse déontologique des articles journalistiques (Version Groq)
Utilise Groq avec Mixtral pour évaluer le respect des principes déontologiques
"""

import os
import json
import sys
from supabase import create_client, Client
from groq import Groq
from datetime import datetime
from typing import Dict, List, Optional
import argparse
from dotenv import load_dotenv


class DeontologyAnalyzer:
    """Analyseur déontologique pour articles de presse"""
    
    def __init__(self, supabase_url: str, supabase_key: str, groq_api_key: str):
        """
        Initialise l'analyseur
        
        Args:
            supabase_url: URL du projet Supabase
            supabase_key: Clé API Supabase (service_role ou anon)
            groq_api_key: Clé API Groq
        """
        # Connexion Supabase
        self.supabase: Client = create_client(supabase_url, supabase_key)
        print("✓ Connexion à Supabase établie")
        
        # Configuration de Groq
        self.client = Groq(api_key=groq_api_key)
        print("✓ Client Groq initialisé")
    
    def get_articles(self, limit: Optional[int] = None, article_id: Optional[str] = None) -> List[Dict]:
        """
        Récupère les articles depuis Supabase
        
        Args:
            limit: Nombre maximum d'articles à récupérer
            article_id: ID spécifique d'un article (optionnel)
            
        Returns:
            Liste des articles
        """
        try:
            query = self.supabase.table('articles').select(
                'id, titre, contenu, date, url, media_id, categorie_id'
            )
            
            if article_id:
                query = query.eq('id', article_id)
            else:
                query = query.order('date', desc=True)
                if limit:
                    query = query.limit(limit)
            
            response = query.execute()
            
            # Récupération des informations des médias et catégories
            articles = []
            for row in response.data:
                # Récupérer le nom du média
                media_name = 'Inconnu'
                if row.get('media_id'):
                    try:
                        media_response = self.supabase.table('medias').select('nom').eq('id', row['media_id']).execute()
                        if media_response.data:
                            media_name = media_response.data[0]['nom']
                    except:
                        pass
                
                # Récupérer le nom de la catégorie
                categorie_name = 'Non catégorisé'
                if row.get('categorie_id'):
                    try:
                        cat_response = self.supabase.table('categories').select('nom').eq('id', row['categorie_id']).execute()
                        if cat_response.data:
                            categorie_name = cat_response.data[0]['nom']
                    except:
                        pass
                
                articles.append({
                    'id': row['id'],
                    'titre': row['titre'],
                    'contenu': row['contenu'],
                    'date': row['date'],
                    'url': row['url'],
                    'media_name': media_name,
                    'categorie': categorie_name
                })
            
            return articles
            
        except Exception as e:
            print(f"✗ Erreur lors de la récupération des articles : {e}")
            return []
    
    def analyze_content(self, titre: str, contenu: str) -> Dict:
        """
        Analyse le contenu d'un article avec Groq (Mixtral)
        
        Args:
            titre: Titre de l'article
            contenu: Contenu de l'article
            
        Returns:
            Dictionnaire avec interpretation et score
        """
        try:
            # Vérifier la longueur du contenu (Groq supporte jusqu'à ~32k tokens)
            MAX_CHARS = 30000
            texte_a_analyser = contenu
            
            if len(contenu) > MAX_CHARS:
                print(f"  ⚠️  Article long ({len(contenu)} chars), troncature à {MAX_CHARS}...")
                texte_a_analyser = contenu[:MAX_CHARS]
            
            # Préparation du prompt
            system_prompt = """Tu es un expert en analyse déontologique du contenu journalistique.

Tu dois analyser les articles selon ces critères déontologiques :
- Véracité (affirmations fausses, non vérifiées, trompeuses)
- Diffamation (accusations sans preuve)
- Incitation à la haine, violence ou discrimination
- Insultes, attaques personnelles, propos injurieux
- Manipulation ou insinuations sans base factuelle
- Ton agressif ou fortement biaisé
- Intégrité journalistique

Tu dois TOUJOURS répondre avec un JSON strictement valide contenant :
{
  "interpretation": "Description en 2 lignes maximum de l'analyse déontologique",
  "score": 0-10
}

Score sur 10 :
- 10 = Respect total de la déontologie
- 7-9 = Bon avec légères réserves
- 4-6 = Problèmes notables
- 0-3 = Manquements graves
- -1 = Impossible d'analyser

Réponds UNIQUEMENT avec le JSON, rien d'autre."""

            user_prompt = f"""Analyse ce texte journalistique :

TITRE : {titre}

CONTENU : {texte_a_analyser}

Réponds uniquement avec le JSON."""

            # Appel à Groq avec Mixtral
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                temperature=0.0,  # Température à 0 pour des résultats déterministes
                max_tokens=300,
                top_p=1.0,  # top_p à 1.0 pour désactiver le nucleus sampling
                seed=42  # Seed fixe pour garantir la reproductibilité
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
            print(f"✗ Erreur lors de l'analyse Groq : {e}")
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
    
    def _get_score_emoji(self, score: int) -> str:
        """Retourne un emoji selon le score"""
        if score == -1:
            return "⚠️"
        elif score >= 8:
            return "✅"
        elif score >= 6:
            return "🟡"
        elif score >= 4:
            return "🟠"
        else:
            return "❌"
    
    def _save_results(self, results: List[Dict], output_file: str):
        """Sauvegarde les résultats dans un fichier JSON"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Résultats sauvegardés dans : {output_file}")
        except Exception as e:
            print(f"✗ Erreur lors de la sauvegarde : {e}")


def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(
        description="Analyse déontologique d'articles journalistiques avec Groq Mixtral"
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Nombre d\'articles à analyser (par défaut : tous)'
    )
    parser.add_argument(
        '--article-id',
        type=str,
        help='ID d\'un article spécifique à analyser'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Fichier de sortie pour sauvegarder les résultats JSON'
    )
    
    args = parser.parse_args()
    
    # Charger les variables d'environnement
    load_dotenv()
    
    try:
        # Configuration
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_ANON_KEY')
        groq_api_key = os.getenv('GROQ_API_KEY')
        
        if not supabase_url or not supabase_key:
            print("✗ Variables SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY/SUPABASE_ANON_KEY requises dans .env")
            sys.exit(1)
        
        if not groq_api_key:
            print("✗ Variable GROQ_API_KEY requise dans .env")
            print("\nPour obtenir votre clé API Groq :")
            print("1. Allez sur https://console.groq.com/")
            print("2. Créez un compte gratuit")
            print("3. Générez une clé API dans 'API Keys'")
            print("4. Ajoutez dans votre .env : GROQ_API_KEY=votre_clé")
            sys.exit(1)
        
        # Création de l'analyseur
        analyzer = DeontologyAnalyzer(
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            groq_api_key=groq_api_key
        )
        
        # Exécution
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
        sys.exit(1)


if __name__ == "__main__":
    main()
