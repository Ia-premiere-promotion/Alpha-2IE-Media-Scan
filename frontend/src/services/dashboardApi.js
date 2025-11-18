/**
 * Service API pour le Dashboard - Monitoring Médiatique
 * Consomme les endpoints backend pour afficher les données en temps réel
 */

// Configuration de l'API à partir des variables d'environnement
const API_BASE_URL = `${import.meta.env.VITE_API_BASE_URL}/api/dashboard`;

/**
 * Fonction helper pour gérer les requêtes avec authentification
 */
async function fetchWithAuth(url, options = {}) {
  const token = localStorage.getItem('access_token');
  
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
      ...options.headers,
    },
    ...options,
  };

  const response = await fetch(url, config);
  
  if (!response.ok) {
    throw new Error(`Erreur ${response.status}: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Récupère les statistiques globales
 * @param {string} timeRange - '1h', '6h', '24h', '7d', '30d'
 */
export const getStats = async (timeRange = '24h') => {
  return await fetchWithAuth(`${API_BASE_URL}/stats?time_range=${timeRange}`);
};

/**
 * Récupère la liste de tous les médias avec leurs stats
 * @param {string} timeRange - '1h', '6h', '24h', '7d', '30d'
 */
export const getMediaList = async (timeRange = '24h') => {
  return await fetchWithAuth(`${API_BASE_URL}/medias?time_range=${timeRange}`);
};

/**
 * Récupère les détails d'un média spécifique
 * @param {number} mediaId - ID du média
 * @param {string} timeRange - '1h', '6h', '24h', '7d', '30d'
 */
export const getMediaDetails = async (mediaId, timeRange = '24h') => {
  console.log(`🌐 API Call: getMediaDetails(${mediaId}, ${timeRange})`);
  const url = `${API_BASE_URL}/medias/${mediaId}?time_range=${timeRange}`;
  console.log(`📡 URL: ${url}`);
  
  const data = await fetchWithAuth(url);
  console.log(`✅ Données reçues:`, data);
  return data;
};

/**
 * Récupère les alertes
 * @param {boolean} isResolved - Filtrer par statut résolu
 * @param {string} severite - 'critical', 'high', 'medium', 'low' ou null
 * @param {number} limit - Nombre maximum d'alertes à récupérer
 */
export const getAlerts = async (isResolved = false, severite = null, limit = null) => {
  let url = `${API_BASE_URL}/alerts?is_resolved=${isResolved}`;
  if (severite) url += `&severite=${severite}`;
  if (limit) url += `&limit=${limit}`;
  
  const response = await fetch(url);
  if (!response.ok) throw new Error('Erreur lors de la récupération des alertes');
  return response.json();
};

/**
 * Récupère les statistiques des alertes
 */
export const getAlertStats = async () => {
  const response = await fetch(`${API_BASE_URL}/alerts/stats`);
  if (!response.ok) throw new Error('Erreur lors de la récupération des stats d\'alertes');
  return response.json();
};

/**
 * Marque une alerte comme résolue
 * @param {number} alertId - ID de l'alerte à résoudre
 */
export const resolveAlert = async (alertId) => {
  const response = await fetch(`${API_BASE_URL}/alerts/${alertId}/resolve`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json'
    }
  });
  if (!response.ok) throw new Error('Erreur lors de la résolution de l\'alerte');
  return response.json();
};

/**
 * Génère de nouvelles alertes pour tous les médias
 */
export const generateAlerts = async () => {
  const response = await fetch(`${API_BASE_URL}/alerts/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  });
  if (!response.ok) throw new Error('Erreur lors de la génération des alertes');
  return response.json();
};

/**
 * Récupère le classement des médias
 * @param {string} timeRange - '1h', '6h', '24h', '7d', '30d'
 */
export const getRanking = async (timeRange = '24h') => {
  const response = await fetch(`${API_BASE_URL}/ranking?time_range=${timeRange}`);
  if (!response.ok) throw new Error('Erreur lors de la récupération du classement');
  return response.json();
};

/**
 * Récupère les catégories avec leurs statistiques
 */
export const getCategories = async () => {
  const response = await fetch(`${API_BASE_URL}/categories`);
  if (!response.ok) throw new Error('Erreur lors de la récupération des catégories');
  return response.json();
};

/**
 * Récupère le graphique d'activité global ou d'un média
 * @param {string} timeRange - '1h', '6h', '24h', '7d', '30d'
 * @param {number} mediaId - ID du média (optionnel, si null = global)
 */
export const getActivityChart = async (timeRange = '7d', mediaId = null) => {
  let url = `${API_BASE_URL}/activity-chart?time_range=${timeRange}`;
  if (mediaId) url += `&media_id=${mediaId}`;
  
  const response = await fetch(url);
  if (!response.ok) throw new Error('Erreur lors de la récupération du graphique d\'activité');
  return response.json();
};



/**
 * Récupère la distribution thématique
 * @param {number} mediaId - ID du média (optionnel)
 * @param {string} timeRange - '1h', '6h', '24h', '7d', '30d'
 */
export const getThematicDistribution = async (mediaId = null, timeRange = '24h') => {
  let url = `${API_BASE_URL}/thematic-distribution?time_range=${timeRange}`;
  if (mediaId) url += `&media_id=${mediaId}`;
  
  const response = await fetch(url);
  if (!response.ok) throw new Error('Erreur lors de la récupération de la distribution thématique');
  return response.json();
};

/**
 * Récupère le top 5 des médias (alias pour getMediaList avec limit)
 */
export const getTopMedia = async (timeRange = '24h') => {
  const medias = await getMediaList(timeRange);
  // Trier par score d'influence (qui regroupe engagement, articles, followers, ancienneté, régularité)
  return medias
    .sort((a, b) => {
      const scoreA = a.score_influence || 0;
      const scoreB = b.score_influence || 0;
      return scoreB - scoreA;
    })
    .slice(0, 5);
};

/**
 * Récupère les alertes regroupées par média (utilise getAlerts et regroupe côté client)
 */
export const getAlertsByMedia = async () => {
  const alerts = await getAlerts(false);
  
  // Regrouper par média
  const byMedia = {};
  alerts.forEach(alert => {
    const mediaName = alert.medias?.name || 'Inconnu';
    if (!byMedia[mediaName]) {
      byMedia[mediaName] = {
        name: mediaName,
        couleur: alert.medias?.couleur || '#6B7280',
        alerts: []
      };
    }
    byMedia[mediaName].alerts.push(alert);
  });
  
  return Object.values(byMedia);
};

/**
 * Récupère les articles récents
 * @param {number} limit - Nombre d'articles à récupérer (défaut: 10)
 * @param {number} mediaId - ID du média pour filtrer (optionnel)
 * @param {string} timeRange - '1h', '6h', '24h', '7d', '30d', 'all'
 */
export const getRecentArticles = async (limit = 10, mediaId = null, timeRange = '24h') => {
  let url = `${API_BASE_URL}/recent-articles?limit=${limit}&time_range=${timeRange}`;
  if (mediaId) url += `&media_id=${mediaId}`;
  
  const response = await fetch(url);
  if (!response.ok) throw new Error('Erreur lors de la récupération des articles récents');
  return response.json();
};

/**
 * Récupère l'analyse des sentiments pour les posts sociaux
 * @param {number} mediaId - ID du média pour filtrer (optionnel)
 * @param {string} timeRange - Période de temps (optionnel)
 * @param {number} limit - Nombre d'articles à analyser (optionnel)
 * @param {number} offset - Décalage pour la pagination (optionnel)
 */
export const getSentiments = async (mediaId = null, timeRange = 'all', limit = 10, offset = 0) => {
  let url = `${API_BASE_URL}/sentiments?limit=${limit}&offset=${offset}`;
  if (mediaId) url += `&media_id=${mediaId}`;
  if (timeRange) url += `&time_range=${timeRange}`;
  
  return await fetchWithAuth(url);
};

export default {
  getStats,
  getMediaList,
  getMediaDetails,
  getAlerts,
  getAlertStats,
  resolveAlert,
  generateAlerts,
  getRanking,
  getCategories,
  getActivityChart,
  getThematicDistribution,
  getTopMedia,
  getAlertsByMedia,
  getRecentArticles,
  getSentiments
};

