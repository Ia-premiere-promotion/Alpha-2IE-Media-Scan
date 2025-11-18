from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import bcrypt
from supabase_client import get_supabase_client
from datetime import datetime
from functools import wraps

users_bp = Blueprint('users', __name__, url_prefix='/api/users')


def jwt_required_conditional(f):
    """Decorator that applies JWT requirement only for non-OPTIONS requests"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'OPTIONS':
            return '', 200
        return jwt_required()(f)(*args, **kwargs)
    return decorated_function


@users_bp.route('', methods=['GET', 'OPTIONS'])
@users_bp.route('/', methods=['GET', 'OPTIONS'])
@jwt_required_conditional
def get_all_users():
    """Récupérer tous les utilisateurs (admin uniquement)"""
    try:
        current_user_id = get_jwt_identity()
        supabase = get_supabase_client()
        
        # Vérifier que l'utilisateur actuel est admin
        current_user_response = supabase.table('users').select('*').eq('id', current_user_id).execute()
        if not current_user_response.data or current_user_response.data[0]['role'] != 'admin':
            return jsonify({'error': 'Accès non autorisé. Droits administrateur requis.'}), 403
        
        # Récupérer tous les utilisateurs
        response = supabase.table('users').select('*').order('created_at', desc=True).execute()
        
        # Préparer les données (sans password_hash)
        users_data = []
        for user in response.data:
            users_data.append({
                'id': user['id'],
                'email': user['email'],
                'nom': user.get('nom'),
                'prenom': user.get('prenom'),
                'role': user['role'],
                'telephone': user.get('telephone'),
                'actif': user.get('actif', True),
                'created_at': user.get('created_at'),
                'updated_at': user.get('updated_at')
            })
        
        return jsonify({
            'users': users_data,
            'total': len(users_data)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@users_bp.route('', methods=['POST', 'OPTIONS'])
@users_bp.route('/', methods=['POST', 'OPTIONS'])
@jwt_required_conditional
def create_user():
    """Créer un nouvel utilisateur (admin uniquement)"""
    try:
        current_user_id = get_jwt_identity()
        supabase = get_supabase_client()
        
        # Vérifier que l'utilisateur actuel est admin
        current_user_response = supabase.table('users').select('*').eq('id', current_user_id).execute()
        if not current_user_response.data or current_user_response.data[0]['role'] != 'admin':
            return jsonify({'error': 'Accès non autorisé. Droits administrateur requis.'}), 403
        
        data = request.get_json()
        
        # Validation
        if not data or not data.get('email') or not data.get('nom') or not data.get('prenom'):
            return jsonify({'error': 'Email, nom et prénom requis'}), 400
        
        # Vérifier si l'email existe déjà
        existing_user = supabase.table('users').select('*').eq('email', data['email']).execute()
        if existing_user.data and len(existing_user.data) > 0:
            return jsonify({'error': 'Cet email est déjà utilisé'}), 409
        
        # Hash du mot de passe (par défaut 12345678)
        password = data.get('password', '12345678')
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Créer l'utilisateur
        new_user = {
            'email': data['email'],
            'password_hash': password_hash,
            'nom': data['nom'],
            'prenom': data['prenom'],
            'role': data.get('role', 'user'),
            'telephone': data.get('telephone', ''),
            'actif': True
        }
        
        response = supabase.table('users').insert(new_user).execute()
        
        if response.data:
            user_data = response.data[0]
            return jsonify({
                'message': 'Utilisateur créé avec succès',
                'user': {
                    'id': user_data['id'],
                    'email': user_data['email'],
                    'nom': user_data.get('nom'),
                    'prenom': user_data.get('prenom'),
                    'role': user_data['role'],
                    'telephone': user_data.get('telephone'),
                    'actif': user_data.get('actif', True)
                }
            }), 201
        else:
            return jsonify({'error': 'Erreur lors de la création de l\'utilisateur'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@users_bp.route('/<user_id>', methods=['PUT', 'OPTIONS'])
@jwt_required_conditional
def update_user(user_id):
    """Mettre à jour un utilisateur (admin uniquement)"""
    try:
        current_user_id = get_jwt_identity()
        supabase = get_supabase_client()
        
        # Vérifier que l'utilisateur actuel est admin
        current_user_response = supabase.table('users').select('*').eq('id', current_user_id).execute()
        if not current_user_response.data or current_user_response.data[0]['role'] != 'admin':
            return jsonify({'error': 'Accès non autorisé. Droits administrateur requis.'}), 403
        
        data = request.get_json()
        
        # Préparer les données à mettre à jour
        update_data = {}
        if 'actif' in data:
            update_data['actif'] = data['actif']
        if 'role' in data:
            update_data['role'] = data['role']
        if 'nom' in data:
            update_data['nom'] = data['nom']
        if 'prenom' in data:
            update_data['prenom'] = data['prenom']
        if 'telephone' in data:
            update_data['telephone'] = data['telephone']
        
        if not update_data:
            return jsonify({'error': 'Aucune donnée à mettre à jour'}), 400
        
        update_data['updated_at'] = datetime.utcnow().isoformat()
        
        # Mettre à jour l'utilisateur
        response = supabase.table('users').update(update_data).eq('id', user_id).execute()
        
        if response.data:
            user_data = response.data[0]
            return jsonify({
                'message': 'Utilisateur mis à jour avec succès',
                'user': {
                    'id': user_data['id'],
                    'email': user_data['email'],
                    'nom': user_data.get('nom'),
                    'prenom': user_data.get('prenom'),
                    'role': user_data['role'],
                    'telephone': user_data.get('telephone'),
                    'actif': user_data.get('actif', True)
                }
            }), 200
        else:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@users_bp.route('/<user_id>', methods=['DELETE', 'OPTIONS'])
@jwt_required_conditional
def delete_user(user_id):
    """Supprimer un utilisateur (admin uniquement)"""
    try:
        current_user_id = get_jwt_identity()
        supabase = get_supabase_client()
        
        # Vérifier que l'utilisateur actuel est admin
        current_user_response = supabase.table('users').select('*').eq('id', current_user_id).execute()
        if not current_user_response.data or current_user_response.data[0]['role'] != 'admin':
            return jsonify({'error': 'Accès non autorisé. Droits administrateur requis.'}), 403
        
        # Empêcher la suppression de son propre compte
        if user_id == current_user_id:
            return jsonify({'error': 'Vous ne pouvez pas supprimer votre propre compte'}), 400
        
        # Supprimer l'utilisateur
        response = supabase.table('users').delete().eq('id', user_id).execute()
        
        if response.data:
            return jsonify({'message': 'Utilisateur supprimé avec succès'}), 200
        else:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@users_bp.route('/stats', methods=['GET', 'OPTIONS'])
@jwt_required_conditional
def get_user_stats():
    """Obtenir les statistiques des utilisateurs (admin uniquement)"""
    try:
        current_user_id = get_jwt_identity()
        supabase = get_supabase_client()
        
        # Vérifier que l'utilisateur actuel est admin
        current_user_response = supabase.table('users').select('*').eq('id', current_user_id).execute()
        if not current_user_response.data or current_user_response.data[0]['role'] != 'admin':
            return jsonify({'error': 'Accès non autorisé. Droits administrateur requis.'}), 403
        
        # Récupérer tous les utilisateurs
        all_users = supabase.table('users').select('*').execute()
        
        total = len(all_users.data)
        admins = sum(1 for user in all_users.data if user['role'] == 'admin')
        users = sum(1 for user in all_users.data if user['role'] == 'user')
        active = sum(1 for user in all_users.data if user.get('actif', True))
        inactive = total - active
        
        return jsonify({
            'total': total,
            'admins': admins,
            'users': users,
            'active': active,
            'inactive': inactive
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
