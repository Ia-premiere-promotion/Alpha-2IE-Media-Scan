#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de prédiction de catégories avec ML
Utilise un modèle pré-entraîné pour classifier automatiquement les articles
Supporte: pickle (.pkl) et TensorFlow Lite (.tflite)
"""

import pickle
import os
from pathlib import Path
import numpy as np

class CategoryPredictor:
    """Prédit la catégorie d'un article avec un modèle ML"""
    
    def __init__(self, model_path=None, vectorizer_path=None, tflite_model_path=None):
        """
        Initialise le prédicteur avec le modèle et le vectorizer
        
        Args:
            model_path: Chemin vers model.pkl
            vectorizer_path: Chemin vers vectorizer.pkl  
            tflite_model_path: Chemin vers model.tflite (optionnel)
        """
        self.model = None
        self.vectorizer = None
        self.tflite_interpreter = None
        self.tflite_input_details = None
        self.tflite_output_details = None
        
        # Chercher model.tflite en priorité
        if not tflite_model_path:
            tflite_path = Path(__file__).parent / "model.tflite"
            if tflite_path.exists():
                tflite_model_path = str(tflite_path)
        
        # Charger TFLite si disponible
        if tflite_model_path and os.path.exists(tflite_model_path):
            try:
                import tensorflow as tf
                self.tflite_interpreter = tf.lite.Interpreter(model_path=tflite_model_path)
                self.tflite_interpreter.allocate_tensors()
                self.tflite_input_details = self.tflite_interpreter.get_input_details()
                self.tflite_output_details = self.tflite_interpreter.get_output_details()
                print(f"✅ Modèle TFLite chargé: {tflite_model_path}")
            except Exception as e:
                print(f"⚠️ Erreur chargement TFLite: {e}")
                self.tflite_interpreter = None
        
        # Chercher les fichiers pickle si TFLite non disponible
        if not self.tflite_interpreter:
            if not model_path:
                possible_paths = [
                    Path(__file__).parent / "model.pkl",
                    Path.home() / "Téléchargements/pipeline_stream_web/smedia_scan/ml/model.pkl"
                ]
                for path in possible_paths:
                    if path.exists():
                        model_path = str(path)
                        break
            
            if not vectorizer_path:
                possible_paths = [
                    Path(__file__).parent / "vectorizer.pkl",
                    Path.home() / "Téléchargements/pipeline_stream_web/smedia_scan/ml/vectorizer.pkl"
                ]
                for path in possible_paths:
                    if path.exists():
                        vectorizer_path = str(path)
                        break
            
            # Charger le modèle et le vectorizer pickle
            if model_path and os.path.exists(model_path):
                try:
                    with open(model_path, 'rb') as f:
                        self.model = pickle.load(f)
                    print(f"✅ Modèle chargé: {model_path}")
                except Exception as e:
                    print(f"❌ Erreur chargement modèle: {e}")
            else:
                print(f"⚠️ Modèle non trouvé: {model_path}")
            
            if vectorizer_path and os.path.exists(vectorizer_path):
                try:
                    with open(vectorizer_path, 'rb') as f:
                        self.vectorizer = pickle.load(f)
                    print(f"✅ Vectorizer chargé: {vectorizer_path}")
                except Exception as e:
                    print(f"❌ Erreur chargement vectorizer: {e}")
            else:
                print(f"⚠️ Vectorizer non trouvé: {vectorizer_path}")
        
        # Catégories EXACTES du modèle CamemBERT (8 classes)
        self.default_categories = [
            'Politique', 'Économie', 'Sécurité', 'Santé', 
            'Culture', 'Sport', 'Éducation', 'Autres'
        ]
        
        # Mapping des indices TFLite vers catégories (ordre exact du modèle)
        self.tflite_categories = [
            'Politique',   # 0
            'Économie',    # 1
            'Sécurité',    # 2
            'Santé',       # 3
            'Culture',     # 4
            'Sport',       # 5
            'Éducation',   # 6
            'Autres'       # 7
        ]
    
    def predict(self, text):
        """
        Prédit la catégorie d'un texte
        
        Args:
            text: Texte de l'article (titre + contenu)
        
        Returns:
            str: Catégorie prédite
        """
        if not text or not isinstance(text, str):
            return 'Autre'
        
        # Essayer TFLite en priorité
        if self.tflite_interpreter:
            try:
                # Préparer les inputs CamemBERT (3 tenseurs INT32)
                inputs = self._prepare_tflite_input(text)
                
                # Set les 3 tenseurs d'entrée
                self.tflite_interpreter.set_tensor(
                    self.tflite_input_details[0]['index'], 
                    inputs['input_ids']
                )
                self.tflite_interpreter.set_tensor(
                    self.tflite_input_details[1]['index'], 
                    inputs['attention_mask']
                )
                if len(self.tflite_input_details) > 2:
                    self.tflite_interpreter.set_tensor(
                        self.tflite_input_details[2]['index'], 
                        inputs['token_type_ids']
                    )
                
                # Exécuter l'inférence
                self.tflite_interpreter.invoke()
                
                # Récupérer le résultat
                output_data = self.tflite_interpreter.get_tensor(self.tflite_output_details[0]['index'])
                predicted_index = np.argmax(output_data[0])
                
                if predicted_index < len(self.tflite_categories):
                    return self.tflite_categories[predicted_index]
                else:
                    return 'Autre'
            except Exception as e:
                print(f"⚠️ Erreur prédiction TFLite: {e}, fallback vers keywords")
                return self._fallback_prediction(text)
        
        # Sinon utiliser pickle
        if self.model and self.vectorizer:
            try:
                # Vectoriser le texte
                X = self.vectorizer.transform([text])
                
                # Prédire
                category = self.model.predict(X)[0]
                
                return category
            except Exception as e:
                print(f"❌ Erreur prédiction: {e}")
                return self._fallback_prediction(text)
        else:
            return self._fallback_prediction(text)
    
    def _prepare_tflite_input(self, text):
        """
        Prépare l'input pour le modèle TFLite CamemBERT
        Le modèle attend 3 tenseurs INT32: input_ids, attention_mask, token_type_ids
        """
        max_length = 256  # Longueur max du modèle
        
        # Tokenization simplifiée (sans transformers pour éviter dépendance lourde)
        # Convertir texte en tokens basiques
        tokens = [ord(c) % 30000 for c in text[:max_length]]  # Vocabulaire CamemBERT ~32k
        tokens = tokens + [0] * (max_length - len(tokens))  # Padding
        
        # Créer les 3 tenseurs requis par CamemBERT
        input_ids = np.array([tokens], dtype=np.int32)  # INT32 requis !
        attention_mask = np.array([[1 if t != 0 else 0 for t in tokens]], dtype=np.int32)
        token_type_ids = np.array([[0] * max_length], dtype=np.int32)
        
        return {
            'input_ids': input_ids,
            'attention_mask': attention_mask,
            'token_type_ids': token_type_ids
        }
    
    def _fallback_prediction(self, text):
        """Prédiction basique par mots-clés si le modèle n'est pas disponible"""
        text_lower = text.lower()
        
        # Keywords ultra-spécifiques (inspirés du notebook d'entraînement)
        keywords = {
            'Politique': [
                'président', 'gouvernement', 'ministre', 'ministère', 'parti', 'politique',
                'élection', 'député', 'assemblée', 'vote', 'parlement', 'sénat',
                'conseil des ministres', 'cabinet', 'pouvoir', 'opposition',
                'ibrahima traore', 'kaboré', 'mpd', 'cdp', 'unir'
            ],
            'Économie': [
                'économie', 'économique', 'entreprise', 'commerce', 'commercial',
                'banque', 'investissement', 'budget', 'fiscal', 'finance', 'financier',
                'franc cfa', 'bceao', 'monnaie', 'inflation', 'croissance',
                'import', 'export', 'douane', 'marchandise', 'marché',
                'startup', 'pme', 'industrie', 'emploi', 'chômage', 'travail',
                'agriculture', 'coton', 'mil', 'sorgho', 'élevage',
                'mine', 'or', 'manganèse', 'zinc', 'orpaillage'
            ],
            'Sécurité': [
                'terrorisme', 'terroriste', 'djihadiste', 'jihadiste', 'extrémiste',
                'attentat', 'attaque', 'assaut', 'offensive', 'incursion',
                'vdp', 'volontaires défense', 'koglweogo', 'dozos',
                'fds', 'forces défense', 'armée', 'militaire', 'soldat', 'gendarme',
                'gendarmerie', 'police', 'sécurité', 'insécurité',
                'conflit', 'violence', 'affrontement', 'combats', 'bataille',
                'groupe armé', 'rebelle', 'milice', 'embuscade', 'raid',
                'sahel', 'nord burkina', 'est burkina', 'zone rouge',
                'aqmi', 'eigs', 'ansarul islam', 'jnim', 'état islamique',
                'déplacés', 'réfugiés', 'pdi', 'victime', 'tué', 'mort', 'blessé',
                'opération militaire', 'contre-terrorisme', 'couvre-feu', 'état urgence'
            ],
            'Sport': [
                'football', 'foot', 'ballon', 'soccer', 'sport', 'sportif',
                'championnat', 'coupe', 'trophée', 'tournoi', 'compétition',
                'can', 'afcon', 'éliminatoires', 'qualification',
                'étalons', 'stallions', 'équipe nationale',
                'match', 'rencontre', 'victoire', 'défaite', 'nul', 'score', 'but', 'goal',
                'entraîneur', 'coach', 'sélectionneur', 'joueur', 'athlète',
                'stade', '4 août', 'municipal', 'terrain',
                'cyclisme', 'tour faso', 'basketball', 'handball', 'athlétisme'
            ],
            'Culture': [
                'culture', 'culturel', 'patrimoine', 'tradition', 'identité',
                'festival', 'fespaco', 'siao', 'festima', 'jat',
                'musique', 'musicien', 'artiste', 'concert', 'spectacle', 'chanson',
                'cinéma', 'film', 'réalisateur', 'acteur', '7e art', 'projection',
                'théâtre', 'danse', 'ballet', 'chorégraphie', 'performance', 'scène',
                'fête', 'cérémonie', 'manifestation culturelle', 'événement culturel',
                'artisan', 'artisanat', 'sculpture', 'peinture', 'exposition', 'galerie',
                'livre', 'littérature', 'écrivain', 'auteur', 'poète', 'roman', 'bibliothèque',
                'musée', 'monument', 'site historique', 'conte', 'griot', 'légende',
                'mode', 'styliste', 'défilé', 'fashion', 'photographie'
            ],
            'Santé': [
                'santé', 'sanitaire', 'médical', 'soins',
                'hôpital', 'chu', 'csps', 'centre santé', 'clinique',
                'médecin', 'infirmier', 'personnel soignant', 'docteur',
                'maladie', 'pathologie', 'épidémie', 'pandémie',
                'covid', 'coronavirus', 'vaccin', 'vaccination', 'immunisation',
                'paludisme', 'malaria', 'méningite', 'tuberculose', 'vih', 'sida',
                'patient', 'malade', 'consultation', 'diagnostic', 'traitement',
                'médicament', 'pharmacie', 'ordonnance', 'prescription',
                'nutrition', 'malnutrition', 'santé maternelle', 'planning familial'
            ],
            'Éducation': [
                'école', 'éducation', 'éducatif', 'scolaire',
                'université', 'étudiant', 'enseignant', 'professeur', 'instituteur',
                'formation', 'examen', 'bac', 'baccalauréat', 'cepe', 'bepc',
                'classe', 'cours', 'leçon', 'programme', 'curriculum',
                'élève', 'apprenant', 'apprentissage', 'scolarité',
                'rentrée', 'année scolaire', 'trimestre', 'vacances scolaires',
                'diplôme', 'certificat', 'licence', 'master', 'doctorat',
                'alphabétisation', 'éducation non formelle'
            ]
        }
        
        scores = {}
        for category, words in keywords.items():
            score = sum(1 for word in words if word in text_lower)
            scores[category] = score
        
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        return 'Autres'
    
    def predict_batch(self, articles):
        """
        Prédit les catégories pour une liste d'articles
        
        Args:
            articles: Liste de dictionnaires avec 'titre' et 'contenu'
        
        Returns:
            Liste d'articles avec 'categorie' ajoutée
        """
        print(f"\n🤖 Prédiction des catégories pour {len(articles)} articles...")
        
        for article in articles:
            # Combiner titre et contenu pour la prédiction
            text = f"{article.get('titre', '')} {article.get('contenu', '')}"
            
            # Prédire la catégorie
            category = self.predict(text)
            article['categorie'] = category
        
        # Stats
        categories = {}
        for article in articles:
            cat = article.get('categorie', 'Autre')
            categories[cat] = categories.get(cat, 0) + 1
        
        print(f"✅ Catégories prédites:")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"   - {cat}: {count}")
        
        return articles


if __name__ == "__main__":
    # Test
    predictor = CategoryPredictor()
    
    test_articles = [
        {"titre": "Le président inaugure un nouveau hôpital", "contenu": "Le chef de l'État a procédé ce matin à l'inauguration..."},
        {"titre": "Victoire des Étalons 2-0", "contenu": "L'équipe nationale a remporté le match..."},
        {"titre": "Nouvelle loi sur l'éducation", "contenu": "Le gouvernement adopte une réforme du système éducatif..."}
    ]
    
    results = predictor.predict_batch(test_articles)
    for article in results:
        print(f"{article['titre'][:50]}... → {article['categorie']}")
