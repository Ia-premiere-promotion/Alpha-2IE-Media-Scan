from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from datetime import datetime
import bcrypt
from supabase_client import get_supabase_client

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    """Inscription d'un nouvel utilisateur"""
    try:
        data = request.get_json()
        
        # Validation
        if not data or not data.get('email') or not data.get('password') or not data.get('name'):
            return jsonify({'error': 'Email, mot de passe et nom requis'}), 400
        
        # Vérifier si l'utilisateur existe déjà
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Cet email est déjà utilisé'}), 409
        
        # Créer le nouvel utilisateur
        user = User(
            email=data['email'],
            name=data['name'],
            organization=data.get('organization', ''),
            role=data.get('role', 'user')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'Utilisateur créé avec succès',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Connexion d'un utilisateur via la table users"""
    try:
        data = request.get_json()
        
        # Validation
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email et mot de passe requis'}), 400
        
        supabase = get_supabase_client()
        
        # Récupérer l'utilisateur par email depuis la table users
        user_result = supabase.table('users').select('*').eq('email', data['email']).execute()
        
        if not user_result.data or len(user_result.data) == 0:
            return jsonify({'error': 'Email ou mot de passe incorrect'}), 401
        
        user = user_result.data[0]
        
        # Vérifier le mot de passe
        if not bcrypt.checkpw(data['password'].encode('utf-8'), user['password_hash'].encode('utf-8')):
            return jsonify({'error': 'Email ou mot de passe incorrect'}), 401
        
        if not user.get('actif', True):
            return jsonify({'error': 'Compte désactivé'}), 403
        
        # Mettre à jour la dernière connexion
        supabase.table('users').update({
            'derniere_connexion': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }).eq('id', user['id']).execute()
        
        # Créer les tokens JWT
        access_token = create_access_token(identity=str(user['id']))
        refresh_token = create_refresh_token(identity=str(user['id']))
        
        # Préparer les données utilisateur (sans le password_hash)
        user_data = {
            'id': user['id'],
            'email': user['email'],
            'nom': user.get('nom'),
            'prenom': user.get('prenom'),
            'role': user.get('role', 'user'),
            'telephone': user.get('telephone'),
            'is_active': user.get('actif', True)
        }
        
        return jsonify({
            'message': 'Connexion réussie',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user_data
        }), 200
        
    except Exception as e:
        print(f"Erreur de connexion: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Rafraîchir le token d'accès"""
    try:
        current_user_id = get_jwt_identity()
        access_token = create_access_token(identity=current_user_id)
        
        return jsonify({
            'access_token': access_token
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Récupérer les informations de l'utilisateur connecté"""
    try:
        current_user_id = get_jwt_identity()
        supabase = get_supabase_client()
        
        response = supabase.table('users').select('*').eq('id', current_user_id).execute()
        
        if not response.data or len(response.data) == 0:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        
        user = response.data[0]
        
        # Préparer les données utilisateur (sans le password_hash)
        user_data = {
            'id': user['id'],
            'email': user['email'],
            'nom': user.get('nom'),
            'prenom': user.get('prenom'),
            'role': user['role'],
            'telephone': user.get('telephone'),
            'actif': user.get('actif', True)
        }
        
        return jsonify({
            'user': user_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Déconnexion (côté client principalement)"""
    return jsonify({
        'message': 'Déconnexion réussie'
    }), 200
