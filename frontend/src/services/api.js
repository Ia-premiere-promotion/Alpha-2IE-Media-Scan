// Service API pour gérer les appels au backend
const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

// Fonction helper pour gérer les requêtes
async function fetchAPI(endpoint, options = {}) {
  const token = localStorage.getItem('access_token');
  
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
      ...options.headers,
    },
    ...options,
  };

  const response = await fetch(`${API_URL}${endpoint}`, config);
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || 'Une erreur est survenue');
  }

  return data;
}

// API Authentication
export const authAPI = {
  // Connexion
  async login(email, password) {
    const data = await fetchAPI('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });

    // Stocker les tokens dans localStorage
    if (data.access_token) {
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      localStorage.setItem('user', JSON.stringify(data.user));
    }

    return data;
  },

  // Déconnexion
  async logout() {
    try {
      await fetchAPI('/api/auth/logout', {
        method: 'POST',
      });
    } catch (error) {
      console.error('Erreur lors de la déconnexion:', error);
    } finally {
      // Nettoyer localStorage dans tous les cas
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
    }
  },

  // Récupérer l'utilisateur actuel
  async getCurrentUser() {
    return await fetchAPI('/api/auth/me');
  },

  // Rafraîchir le token
  async refreshToken() {
    const refresh_token = localStorage.getItem('refresh_token');
    
    if (!refresh_token) {
      throw new Error('Pas de refresh token disponible');
    }

    const data = await fetchAPI('/api/auth/refresh', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${refresh_token}`,
      },
    });

    if (data.access_token) {
      localStorage.setItem('access_token', data.access_token);
    }

    return data;
  },

  // Vérifier si l'utilisateur est connecté
  isAuthenticated() {
    return !!localStorage.getItem('access_token');
  },

  // Récupérer l'utilisateur depuis localStorage
  getUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },

  // Vérifier si l'utilisateur est admin
  isAdmin() {
    const user = this.getUser();
    return user?.role === 'admin';
  },
};

// API Users Management
export const usersAPI = {
  // Récupérer tous les utilisateurs
  async getAll() {
    return await fetchAPI('/api/users');
  },

  // Récupérer les statistiques
  async getStats() {
    return await fetchAPI('/api/users/stats');
  },

  // Créer un nouvel utilisateur
  async create(userData) {
    return await fetchAPI('/api/users', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  },

  // Mettre à jour un utilisateur
  async update(userId, userData) {
    return await fetchAPI(`/api/users/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(userData),
    });
  },

  // Supprimer un utilisateur
  async delete(userId) {
    return await fetchAPI(`/api/users/${userId}`, {
      method: 'DELETE',
    });
  },

  // Bloquer/Débloquer un utilisateur
  async toggleStatus(userId, actif) {
    return await fetchAPI(`/api/users/${userId}`, {
      method: 'PUT',
      body: JSON.stringify({ actif }),
    });
  },
};

export default authAPI;
