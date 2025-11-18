import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Toaster, toast } from 'react-hot-toast';
import UserManagement from './UserManagement';
import NotificationBell from '../components/NotificationBell';
import AlertsPanel from '../components/AlertsPanel';
import ScrapingReportModal from '../components/ScrapingReportModal';
import useAutoScraping from '../hooks/useAutoScraping';
import { 
  BarChart3, 
  Newspaper, 
  Trophy, 
  Users, 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle, 
  Eye, 
  Clock,
  Bell,
  User,
  ThumbsUp,
  Share2,
  MapPin,
  Activity,
  Globe,
  BookOpen,
  Calendar,
  ArrowLeft,
  Settings,
  LogOut,
  Search,
  X,
  Smile,
  Frown,
  Angry,
  Heart,
  Meh,
  ExternalLink,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ArrowUp,
  Filter,
  MessageCircle,
  Repeat2,
  FileSpreadsheet,
  Download
} from 'lucide-react';
import { authAPI } from '../services/api';
import * as dashboardAPI from '../services/dashboardApi';
import './Dashboard.css';

function Dashboard() {
  const navigate = useNavigate();
  
  // Hook pour le scraping automatique
  const {
    isScrapingRunning,
    lastScrapingResult,
    showReportModal,
    setShowReportModal,
    nextScrapingIn,
    formatTimeRemaining,
    startScraping
  } = useAutoScraping(3); // 3 minutes
  
  const [activeTab, setActiveTab] = useState('general');
  const [timeRange, setTimeRange] = useState('all');
  const [mediaAnalysisTimeRange, setMediaAnalysisTimeRange] = useState('all'); // Période indépendante pour l'analyse par média
  const [selectedMedia, setSelectedMedia] = useState(null);
  const [selectedMediaId, setSelectedMediaId] = useState(null); // ID séparé pour éviter les boucles
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [sentimentFilter, setSentimentFilter] = useState('all');
  const [selectedPublication, setSelectedPublication] = useState(null);
  const [showSentimentDetails, setShowSentimentDetails] = useState(false);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState([]);
  const [statsData, setStatsData] = useState(null);
  const [topMedia, setTopMedia] = useState([]);
  const [mediaList, setMediaList] = useState([]);
  const [activityData, setActivityData] = useState([]);
  const [recentAlerts, setRecentAlerts] = useState([]);
  const [recentArticles, setRecentArticles] = useState([]); // Tous les articles bruts
  const [analyzedArticles, setAnalyzedArticles] = useState([]); // Articles avec leur analyse LLM
  const [articlesLoading, setArticlesLoading] = useState(false); // Chargement et analyse en cours
  const [sentimentsData, setSentimentsData] = useState(null); // Données globales des sentiments
  const [displayedPublications, setDisplayedPublications] = useState(5); // Nombre de publications affichées
  const [showScrollTop, setShowScrollTop] = useState(false); // Afficher bouton retour en haut
  const [showAlertsPanel, setShowAlertsPanel] = useState(false); // Afficher le panel d'alertes
  const [alertsCount, setAlertsCount] = useState(0); // Nombre d'alertes actives
  
  // États pour le système d'alertes (onglet dédié)
  const [alertsData, setAlertsData] = useState([]);
  const [alertsStats, setAlertsStats] = useState(null);
  const [alertsLoading, setAlertsLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState('all');
  
  const user = authAPI.getUser();

  // Export Excel de toute la base de données
  const exportDatabaseToExcel = async () => {
    try {
      const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';
      const token = localStorage.getItem('access_token');
      
      // Afficher un loader avec message de patience
      toast.loading('📊 Export en cours... Veuillez patienter, cela peut prendre quelques secondes', { 
        id: 'export-db',
        duration: Infinity,
        style: {
          minWidth: '350px',
          fontSize: '15px',
          fontWeight: '600'
        }
      });
      
      const response = await fetch(`${API_URL}/api/export/database`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Erreur lors de l\'export');
      }

      // Mettre à jour le message
      toast.loading('💾 Génération du fichier Excel...', { id: 'export-db' });

      // Récupérer le blob
      const blob = await response.blob();
      
      // Créer un lien de téléchargement
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `MEDIA_SCAN_Database_${new Date().toISOString().slice(0,10)}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast.success('✅ Base de données exportée avec succès !', { 
        id: 'export-db',
        duration: 4000,
        style: {
          fontSize: '15px',
          fontWeight: '600'
        }
      });
      
    } catch (err) {
      console.error('Erreur export:', err);
      toast.error('❌ Erreur lors de l\'export de la base de données', { 
        id: 'export-db',
        duration: 4000
      });
    }
  };

  // Charger les données au montage et quand timeRange change
  useEffect(() => {
    // Petit délai pour éviter les appels multiples
    const timer = setTimeout(() => {
      loadDashboardData();
    }, 100);
    
    return () => clearTimeout(timer);
  }, [timeRange]);

  // Charger le nombre d'alertes actives au montage et toutes les 30 secondes
  useEffect(() => {
    loadAlertsCount();
    
    const interval = setInterval(() => {
      loadAlertsCount();
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  // Charger les données du système d'alertes quand l'onglet est actif
  useEffect(() => {
    if (activeTab === 'alerts') {
      loadAlertsData();
    }
  }, [activeTab, severityFilter]);

  const loadAlertsCount = async () => {
    try {
      const stats = await dashboardAPI.getAlertStats();
      setAlertsCount(stats.total_active || 0);
    } catch (error) {
      console.error('Erreur chargement stats alertes:', error);
    }
  };

  const loadAlertsData = async () => {
    try {
      setAlertsLoading(true);
      
      // Charger les alertes et les stats en parallèle
      const [alerts, stats] = await Promise.all([
        dashboardAPI.getAlerts(false, severityFilter === 'all' ? null : severityFilter),
        dashboardAPI.getAlertStats()
      ]);
      
      // Grouper les alertes par média
      const alertsByMedia = {};
      alerts.forEach(alert => {
        const mediaId = alert.media_id;
        const mediaName = alert.media?.name || 'Média inconnu';
        const mediaColor = alert.media?.couleur || '#6B7280';
        
        if (!alertsByMedia[mediaId]) {
          alertsByMedia[mediaId] = {
            id: mediaId,
            name: mediaName,
            color: mediaColor,
            alerts: []
          };
        }
        
        alertsByMedia[mediaId].alerts.push(alert);
      });
      
      setAlertsData(Object.values(alertsByMedia));
      setAlertsStats(stats);
    } catch (error) {
      console.error('Erreur chargement alertes:', error);
      setAlertsData([]);
    } finally {
      setAlertsLoading(false);
    }
  };

  const resolveAlertInPage = async (alertId) => {
    try {
      await dashboardAPI.resolveAlert(alertId);
      // Recharger les données
      loadAlertsData();
      loadAlertsCount(); // Mettre à jour le compteur du header
    } catch (error) {
      console.error('Erreur résolution alerte:', error);
    }
  };

  const loadDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      // Réinitialiser les données pour forcer le re-render
      setActivityData([]);
      
      console.log('🔄 Chargement des données pour:', timeRange);
      
      // Charger les stats
      const statsData = await dashboardAPI.getStats(timeRange);
      console.log('📊 Stats data:', statsData);
      setStatsData(statsData); // Sauvegarder pour les quick stats
      
      setStats([
        { 
          icon: Newspaper, 
          label: 'Articles analysés', 
          value: statsData.total_articles?.toLocaleString() || '0', 
          color: '#3b82f6'
        },
        { 
          icon: Globe, 
          label: 'Médias surveillés', 
          value: statsData.total_medias?.toString() || '0', 
          color: '#8b5cf6'
        },
        { 
          icon: AlertTriangle, 
          label: 'Alertes actives', 
          value: statsData.total_alerts?.toString() || '0', 
          color: '#f59e0b'
        },
        { 
          icon: Users, 
          label: 'Engagement total', 
          value: formatNumber(statsData.total_engagement) || '0', 
          color: '#10b981'
        }
      ]);

      // Charger le top médias et transformer les données pour l'UI
      const topMediaData = await dashboardAPI.getTopMedia(timeRange);
      console.log('🏆 Top media data:', topMediaData);
      const transformedTopMedia = topMediaData.map((media, index) => {
        // Utiliser le score d'influence calculé par le backend
        const influenceScore = media.score_influence || 0;
        const totalEngagement = media.engagement?.total || 0;
        const totalArticles = media.total_articles || 0;
        
        return {
          name: media.name,
          articles: totalArticles,
          engagement: formatNumber(totalEngagement),
          engagementRaw: totalEngagement,
          trend: index < Math.ceil(topMediaData.length / 2) ? 'up' : 'down',
          score: Math.round(influenceScore) // Utiliser directement le score d'influence (0-100)
        };
      });
      console.log('✅ Transformed top media:', transformedTopMedia);
      setTopMedia(transformedTopMedia);

      // Charger la liste des médias SANS filtre de temps (toujours 'all' pour avoir tous les articles)
      const mediaListData = await dashboardAPI.getMediaList('all');
      console.log('📰 Media list:', mediaListData);
      
      // Définir un jeu de couleurs pour les médias (chaque média aura une couleur différente)
      const mediaColors = ['#3b82f6', '#ef4444', '#10b981', '#f97316', '#8b5cf6'];
      
      // Assigner une couleur à chaque média de manière cohérente
      const mediaWithColors = mediaListData.map((media, index) => ({
        ...media,
        couleur: mediaColors[index % mediaColors.length], // Force l'attribution de couleur même si elle existe déjà
        articles: media.total_articles || media.articles || 0 // Normaliser la propriété articles
      }));
      
      console.log('🎨 Médias avec couleurs:', mediaWithColors);
      setMediaList(mediaWithColors);

      // Charger les alertes récentes et transformer pour l'UI
      const alertsData = await dashboardAPI.getAlerts(false, null);
      console.log('🚨 Alerts data:', alertsData);
      const transformedAlerts = alertsData.slice(0, 3).map(alert => ({
        type: alert.type || alert.severite || 'info',
        media: alert.medias?.name || 'Inconnu',
        content: alert.titre || alert.message || '',
        time: formatTimeAgo(alert.date)
      }));
      console.log('✅ Transformed alerts:', transformedAlerts);
      setRecentAlerts(transformedAlerts);

      // Charger les vraies données d'activité depuis l'API
      const activityChartData = await dashboardAPI.getActivityChart(timeRange);
      console.log('📈 Activity data from API:', activityChartData);
      
      // Transformer pour l'UI {hour, value}
      const transformedActivityData = activityChartData.map(item => ({
        hour: item.label,
        value: item.count
      }));
      console.log('✅ Transformed activity data:', transformedActivityData);
      setActivityData(transformedActivityData);

      setLoading(false);
    } catch (error) {
      console.error('❌ Erreur lors du chargement des données:', error);
      setLoading(false);
    }
  }, [timeRange]);  // Dépendance sur timeRange

  // Effet pour recharger les détails du média quand mediaAnalysisTimeRange change
  useEffect(() => {
    if (selectedMediaId) {
      console.log(`🔄 Rechargement des détails du média ${selectedMediaId} pour la période: ${mediaAnalysisTimeRange}`);
      const reloadMediaDetails = async () => {
        try {
          const mediaDetails = await dashboardAPI.getMediaDetails(selectedMediaId, mediaAnalysisTimeRange);
          console.log('✅ Détails du média reçus:', mediaDetails);
          console.log('🎨 Couleur actuelle du média sélectionné:', selectedMedia?.couleur);
          
          const enrichedMedia = {
            ...mediaDetails.media,  // D'abord les détails de l'API
            id: selectedMediaId,
            name: selectedMedia?.name,
            couleur: selectedMedia?.couleur, // PUIS on force la couleur du cadrant original
            stats: mediaDetails.stats,
            articles_list: mediaDetails.articles,
            categories_distribution: mediaDetails.categories_distribution,
            activity_chart: mediaDetails.activity_chart
          };
          
          console.log('✅ Couleur après enrichissement:', enrichedMedia.couleur);
          setSelectedMedia(enrichedMedia);
        } catch (error) {
          console.error('❌ Erreur lors du rechargement des détails du média:', error);
        }
      };
      reloadMediaDetails();
    }
  }, [mediaAnalysisTimeRange, selectedMediaId]);  // Recharger quand la période OU l'ID change

  // Effet pour charger les articles ET leur analyse en même temps
  useEffect(() => {
    if (selectedMediaId) {
      const loadArticlesWithAnalysis = async () => {
        setArticlesLoading(true);
        setAnalyzedArticles([]); // Réinitialiser les articles analysés
        setDisplayedPublications(5); // Réinitialiser le nombre affiché
        
        // Créer une clé unique pour le cache basée sur média + période
        const cacheKey = `analyzed_articles_${selectedMediaId}_${mediaAnalysisTimeRange}`;
        
        // Vérifier le cache localStorage
        const cachedData = localStorage.getItem(cacheKey);
        if (cachedData) {
          try {
            const { articles, recentArticles: cached_recent, sentiments, timestamp } = JSON.parse(cachedData);
            const now = Date.now();
            const CACHE_DURATION = 30 * 60 * 1000; // 30 minutes
            
            // Si le cache est encore valide (moins de 30 min)
            if (now - timestamp < CACHE_DURATION) {
              console.log('✅ Utilisation du cache pour les articles analysés');
              setRecentArticles(cached_recent);
              setAnalyzedArticles(articles);
              setSentimentsData(sentiments);
              setArticlesLoading(false);
              return;
            } else {
              console.log('⏰ Cache expiré, rechargement...');
              localStorage.removeItem(cacheKey);
            }
          } catch (e) {
            console.error('❌ Erreur lecture cache:', e);
            localStorage.removeItem(cacheKey);
          }
        }
        
        try {
          // 1. Charger tous les articles bruts
          const articles = await dashboardAPI.getRecentArticles(50, selectedMediaId, mediaAnalysisTimeRange);
          console.log('📰 Articles récents chargés:', articles.length);
          setRecentArticles(articles);
          
          // 2. Analyser les 5 premiers articles avec le LLM
          console.log('🤖 Analyse LLM des 5 premiers articles...');
          const sentiments = await dashboardAPI.getSentiments(selectedMediaId, mediaAnalysisTimeRange, 5);
          console.log('✅ Analyse terminée:', sentiments);
          console.log('📊 Détails des articles analysés:', sentiments.articles);
          setSentimentsData(sentiments);
          
          // 3. Créer les articles analysés en fusionnant les données
          const analyzed = articles.slice(0, 5).map((article, index) => {
            // Utiliser l'index car l'API retourne les analyses dans le même ordre
            const analysisData = sentiments.articles?.[index];
            
            console.log(`Article ${index + 1}:`, {
              titre: article.titre?.substring(0, 50),
              score_recu: analysisData?.score,
              interpretation: analysisData?.interpretation?.substring(0, 50)
            });
            
            return {
              ...article,
              score: analysisData?.score !== undefined && analysisData?.score >= 0 ? analysisData.score : 5,
              interpretation: analysisData?.interpretation || "En attente d'analyse"
            };
          });
          
          setAnalyzedArticles(analyzed);
          
          // 4. Sauvegarder dans le cache localStorage
          const cacheData = {
            articles: analyzed,
            recentArticles: articles,
            sentiments: sentiments,
            timestamp: Date.now()
          };
          localStorage.setItem(cacheKey, JSON.stringify(cacheData));
          console.log('💾 Résultats mis en cache');
          
        } catch (error) {
          console.error('❌ Erreur lors du chargement:', error);
          setRecentArticles([]);
          setAnalyzedArticles([]);
        } finally {
          setArticlesLoading(false);
          // Ne retirer mediaDetailsLoading que quand tout est prêt
          
        }
      };
      
      loadArticlesWithAnalysis();
    } else {
      setRecentArticles([]);
      setAnalyzedArticles([]);
      setArticlesLoading(false);
      
    }
  }, [selectedMediaId, mediaAnalysisTimeRange]); // Rechargement quand le média ou la période change

  // Gérer le scroll infini et le bouton retour en haut
  useEffect(() => {
    const handleScroll = () => {
      // Afficher/masquer le bouton "retour en haut"
      if (window.scrollY > 500) {
        setShowScrollTop(true);
      } else {
        setShowScrollTop(false);
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Fonction pour charger plus de publications (analyse les 5 suivants)
  const loadMorePublications = useCallback(async () => {
    if (!selectedMediaId || analyzedArticles.length >= recentArticles.length) {
      return; // Tous les articles sont déjà chargés
    }
    
    setArticlesLoading(true);
    
    try {
      const currentCount = analyzedArticles.length;
      const nextBatch = recentArticles.slice(currentCount, currentCount + 5);
      
      // Créer une clé unique pour le cache de ce batch
      const cacheKey = `analyzed_batch_${selectedMediaId}_${mediaAnalysisTimeRange}_${currentCount}`;
      
      // Vérifier le cache localStorage pour ce batch
      const cachedBatch = localStorage.getItem(cacheKey);
      let newAnalyzed;
      
      if (cachedBatch) {
        try {
          const { articles, timestamp } = JSON.parse(cachedBatch);
          const now = Date.now();
          const CACHE_DURATION = 30 * 60 * 1000; // 30 minutes
          
          if (now - timestamp < CACHE_DURATION) {
            console.log(`✅ Utilisation du cache pour le batch ${currentCount}-${currentCount + 5}`);
            newAnalyzed = articles;
          }
        } catch (e) {
          console.error('❌ Erreur lecture cache batch:', e);
          localStorage.removeItem(cacheKey);
        }
      }
      
      // Si pas de cache valide, analyser avec le LLM
      if (!newAnalyzed) {
        console.log(`🤖 Analyse LLM des articles ${currentCount + 1} à ${currentCount + nextBatch.length}...`);
        
        // Analyser le prochain batch de 5 articles
        const sentiments = await dashboardAPI.getSentiments(selectedMediaId, mediaAnalysisTimeRange, 5, currentCount);
        console.log('✅ Analyse du batch suivant terminée:', sentiments);
        
        // Créer les nouveaux articles analysés
        newAnalyzed = nextBatch.map((article, index) => {
          const analysisData = sentiments.articles?.[index];
          
          return {
            ...article,
            score: analysisData?.score || 5,
            interpretation: analysisData?.interpretation || "En attente d'analyse"
          };
        });
        
        // Sauvegarder dans le cache
        const cacheData = {
          articles: newAnalyzed,
          timestamp: Date.now()
        };
        localStorage.setItem(cacheKey, JSON.stringify(cacheData));
        console.log('💾 Batch mis en cache');
      }
      
      // Ajouter les nouveaux articles analysés aux existants
      setAnalyzedArticles(prev => [...prev, ...newAnalyzed]);
      setDisplayedPublications(prev => prev + 5);
      
    } catch (error) {
      console.error('❌ Erreur lors du chargement du batch suivant:', error);
    } finally {
      setArticlesLoading(false);
    }
  }, [selectedMediaId, mediaAnalysisTimeRange, analyzedArticles, recentArticles]);

  // Fonction pour revenir en haut
  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  };

  // Fonction pour exporter les visuels en PNG format A4
  const exportDashboardToPNG = async () => {
    try {
      // Importer html2canvas dynamiquement
      const html2canvas = (await import('html2canvas')).default;
      
      // Période pour le nom du fichier
      const periodLabel = timeRange === 'all' ? 'Tous_les_temps' : 
                         timeRange === '1h' ? '1_heure' : 
                         timeRange === '6h' ? '6_heures' : 
                         timeRange === '24h' ? '24_heures' : 
                         timeRange === '7d' ? '7_jours' : '30_jours';

      // Toast de progression
      const loadingToast = toast.loading('Préparation de l\'export format A4...');

      // Créer un conteneur format A4 (210mm x 297mm à 96 DPI = 794px x 1123px)
      const exportContainer = document.createElement('div');
      exportContainer.style.cssText = `
        position: fixed;
        left: -9999px;
        top: 0;
        width: 794px;
        background: white;
        padding: 40px;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      `;
      document.body.appendChild(exportContainer);

      // Titre
      const title = document.createElement('div');
      title.style.cssText = `
        font-size: 24px;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 8px;
        text-align: center;
      `;
      title.textContent = `Dashboard Media Scan - ${periodLabel}`;
      exportContainer.appendChild(title);

      // Date
      const dateDiv = document.createElement('div');
      dateDiv.style.cssText = `
        font-size: 14px;
        color: #64748b;
        margin-bottom: 30px;
        text-align: center;
      `;
      dateDiv.textContent = new Date().toLocaleDateString('fr-FR', { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
      });
      exportContainer.appendChild(dateDiv);

      // Liste des sections à inclure
      const sectionsToExport = [
        { selector: '.stats-grid', name: 'Statistiques', marginBottom: '30px' },
        { selector: '.charts-section', name: 'Graphiques', marginBottom: '30px' },
        { selector: '.info-section', name: 'Informations', marginBottom: '20px' }
      ];

      // Cloner et ajouter chaque section
      for (let i = 0; i < sectionsToExport.length; i++) {
        const section = sectionsToExport[i];
        const element = document.querySelector(section.selector);
        
        if (element) {
          toast.loading(`Ajout ${i + 1}/${sectionsToExport.length}: ${section.name}...`, { id: loadingToast });
          
          const clone = element.cloneNode(true);
          clone.style.cssText = `
            width: 100%;
            background: transparent;
            margin-bottom: ${section.marginBottom};
          `;
          exportContainer.appendChild(clone);
        }
      }

      // Attendre le rendu
      toast.loading('Génération de l\'image...', { id: loadingToast });
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Capturer en PNG
      const canvas = await html2canvas(exportContainer, {
        backgroundColor: '#ffffff',
        scale: 2,
        logging: false,
        useCORS: true,
        width: 794,
        windowWidth: 794
      });

      // Télécharger
      const link = document.createElement('a');
      link.download = `Dashboard_Complet_${periodLabel}_${new Date().toISOString().split('T')[0]}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();

      // Nettoyer
      document.body.removeChild(exportContainer);
      toast.success('Dashboard exporté en format A4!', { id: loadingToast });
      
    } catch (error) {
      console.error('Erreur export:', error);
      toast.error('Erreur lors de l\'export du dashboard');
    }
  };

  const formatNumber = (num) => {
    if (!num) return '0';
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  };

  const formatTimeAgo = (dateString) => {
    if (!dateString) return 'Il y a un moment';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) return `Il y a ${diffMins} min`;
    if (diffHours < 24) return `Il y a ${diffHours}h`;
    return `Il y a ${diffDays}j`;
  };

  const handleLogout = async () => {
    await authAPI.logout();
    navigate('/login');
  };

  const timeRanges = [
    { value: 'all', label: 'Tous les temps' },
    { value: '1h', label: '1 heure' },
    { value: '6h', label: '6 heures' },
    { value: '24h', label: '24 heures' },
    { value: '7d', label: '7 jours' },
    { value: '30d', label: '30 jours' }
  ];

  const navigationItems = [
    { id: 'general', icon: BarChart3, label: 'Tableau de bord général' },
    { id: 'media', icon: Newspaper, label: 'Analyse par média' },
    { id: 'ranking', icon: Trophy, label: 'Classement des médias' },
    { id: 'alerts', icon: Bell, label: 'Système d\'alerte' }
  ];

  // Ajouter "Gestion des utilisateurs" si admin
  const adminNavigationItems = user?.role === 'admin' 
    ? [...navigationItems, { id: 'users', icon: Users, label: 'Gestion des utilisateurs' }]
    : navigationItems;

  const handleMediaSelect = async (media) => {
    console.log('🎯 Sélection du média:', media.name, 'Couleur:', media.couleur);
    setSelectedMedia(media);
    setSelectedMediaId(media.id); // Définir l'ID séparément pour déclencher le useEffect
     // Activer le loader
    
    try {
      // Charger les détails complets du média depuis l'API avec sa propre période
      const mediaDetails = await dashboardAPI.getMediaDetails(media.id, mediaAnalysisTimeRange);
      console.log(' Détails du média reçus:', mediaDetails);
      
      // Enrichir l'objet média avec les détails de l'API EN CONSERVANT LA COULEUR ORIGINALE
      const enrichedMedia = {
        ...mediaDetails.media,  // D'abord les détails de l'API
        id: media.id,
        name: media.name,
        couleur: media.couleur, // PUIS on écrase avec la couleur du cadrant (PRIORITAIRE)
        stats: mediaDetails.stats,
        articles_list: mediaDetails.articles,
        categories_distribution: mediaDetails.categories_distribution,
        activity_chart: mediaDetails.activity_chart
      };
      
      console.log('✅ Média enrichi avec couleur:', enrichedMedia.couleur);
      setSelectedMedia(enrichedMedia);
    } catch (error) {
      console.error('❌ Erreur lors du chargement des détails du média:', error);
      // Garder le média de base en cas d'erreur
      
    }
    // NE PAS mettre mediaDetailsLoading à false ici
    // Il sera mis à false après le chargement des articles dans le useEffect
  };

  const handleBackToList = () => {
    setSelectedMedia(null);
    setSelectedMediaId(null);
  };

  const renderContent = () => {
    // Si un média est sélectionné ET qu'on est dans l'onglet 'media'
    if (selectedMedia && activeTab === 'media') {
      // Afficher les détails directement (chaque section aura son propre loader)
      return renderMediaDetails();
    }

    // Pour tous les autres cas, utiliser le switch normal
    switch(activeTab) {
      case 'general':
        return renderGeneralDashboard();
      case 'media':
        return renderMediaList();
      case 'ranking':
        return renderRanking();
      case 'alerts':
        return renderAlertsSystem();
      case 'users':
        return <UserManagement />;
      default:
        return renderGeneralDashboard();
    }
  };

  const renderGeneralDashboard = () => (
    <>
      {/* Bouton d'export */}
      <div className="export-actions-bar">
        <button className="export-dashboard-btn" onClick={exportDashboardToPNG}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          <span>Exporter les visuels</span>
          <span className="export-period-badge">{timeRange === 'all' ? 'Tous les temps' : timeRange === '1h' ? '1h' : timeRange === '6h' ? '6h' : timeRange === '24h' ? '24h' : timeRange === '7d' ? '7j' : '30j'}</span>
        </button>
      </div>

      <div className="stats-grid">
        {stats.map((stat, index) => (
          <div key={index} className="stat-card">
            <div className="stat-icon" style={{ backgroundColor: `${stat.color}15` }}>
              <stat.icon size={24} style={{ color: stat.color }} />
            </div>
            <div className="stat-content">
              <p className="stat-label">{stat.label}</p>
              <h3 className="stat-value">{stat.value}</h3>
            </div>
          </div>
        ))}
      </div>

      <div className="charts-section">
        <div className="chart-card large">
          <div className="chart-header">
            <div>
              <h3>Activité des médias ({timeRange === 'all' ? 'Tous les temps' : timeRange === '1h' ? '1h' : timeRange === '6h' ? '6h' : timeRange === '24h' ? '24h' : timeRange === '7d' ? '7 jours' : '30 jours'})</h3>
              <p>Articles publiés par {timeRange === '1h' || timeRange === '6h' || timeRange === '24h' ? 'heure' : 'jour'}</p>
            </div>
            {loading && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#3b82f6' }}>
                <div style={{ 
                  width: '16px', 
                  height: '16px', 
                  border: '2px solid #3b82f6', 
                  borderTopColor: 'transparent',
                  borderRadius: '50%',
                  animation: 'spin 0.8s linear infinite'
                }}></div>
                <span style={{ fontSize: '0.875rem' }}>Actualisation...</span>
              </div>
            )}
          </div>
          <div className="activity-chart-line" key={`activity-${timeRange}-${activityData.length}`} style={{ opacity: loading ? 0.5 : 1, transition: 'opacity 0.3s' }}>
            <svg width="100%" height="250" viewBox="0 0 800 250" preserveAspectRatio="none">
              <defs>
                <linearGradient id="lineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" style={{ stopColor: '#3b82f6', stopOpacity: 1 }} />
                  <stop offset="50%" style={{ stopColor: '#8b5cf6', stopOpacity: 1 }} />
                  <stop offset="100%" style={{ stopColor: '#ec4899', stopOpacity: 1 }} />
                </linearGradient>
                <linearGradient id="areaGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" style={{ stopColor: '#3b82f6', stopOpacity: 0.3 }} />
                  <stop offset="100%" style={{ stopColor: '#3b82f6', stopOpacity: 0 }} />
                </linearGradient>
              </defs>
              
              {activityData && activityData.length > 0 ? (
                <>
                  {/* Aire sous la courbe */}
                  <path
                    d={(() => {
                      const maxValue = Math.max(...activityData.map(d => d.value), 1);
                      const width = 800;
                      const height = 200;
                      const padding = 20;
                      const step = (width - padding * 2) / (activityData.length - 1 || 1);
                      
                      let path = `M ${padding} ${height + padding}`;
                      activityData.forEach((data, i) => {
                        const x = padding + i * step;
                        const y = padding + (height - (data.value / maxValue) * height);
                        if (i === 0) path += ` L ${x} ${y}`;
                        else path += ` L ${x} ${y}`;
                      });
                      path += ` L ${padding + (activityData.length - 1) * step} ${height + padding}`;
                      return path;
                    })()}
                    fill="url(#areaGradient)"
                    opacity="0.5"
                  />
                  
                  {/* Ligne principale */}
                  <path
                    d={(() => {
                      const maxValue = Math.max(...activityData.map(d => d.value), 1);
                      const width = 800;
                      const height = 200;
                      const padding = 20;
                      const step = (width - padding * 2) / (activityData.length - 1 || 1);
                      
                      let path = '';
                      activityData.forEach((data, i) => {
                        const x = padding + i * step;
                        const y = padding + (height - (data.value / maxValue) * height);
                        if (i === 0) path = `M ${x} ${y}`;
                        else path += ` L ${x} ${y}`;
                      });
                      return path;
                    })()}
                    stroke="url(#lineGradient)"
                    strokeWidth="3"
                    fill="none"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  
                  {/* Points sur la courbe */}
                  {activityData.map((data, i) => {
                    const maxValue = Math.max(...activityData.map(d => d.value), 1);
                    const width = 800;
                    const height = 200;
                    const padding = 20;
                    const step = (width - padding * 2) / (activityData.length - 1 || 1);
                    const x = padding + i * step;
                    const y = padding + (height - (data.value / maxValue) * height);
                    
                    return (
                      <g key={i}>
                        <circle cx={x} cy={y} r="5" fill="#fff" stroke="#3b82f6" strokeWidth="2" />
                        <text x={x} y={y - 15} textAnchor="middle" fill="#3b82f6" fontSize="12" fontWeight="600">
                          {data.value}
                        </text>
                      </g>
                    );
                  })}
                </>
              ) : (
                <text x="400" y="125" textAnchor="middle" fill="#94a3b8" fontSize="16">
                  Chargement des données...
                </text>
              )}
            </svg>
            
            {/* Labels des heures/jours */}
            <div className="chart-labels">
              {activityData.map((data, i) => (
                <span key={i} className="chart-label">{data.hour}</span>
              ))}
            </div>
          </div>
        </div>

        <div className="chart-card">
          <div className="chart-header">
            <h3>Top 5 Médias</h3>
            <p>Classement par score d'influence</p>
          </div>
          <div className="top-media-list">
            {topMedia.map((media, index) => (
              <div key={index} className="media-item">
                <div className="media-rank">
                  <span className={`rank-badge rank-${index + 1}`}>{index + 1}</span>
                </div>
                <div className="media-info">
                  <h4>{media.name}</h4>
                  <p>{media.articles} article{media.articles > 1 ? 's' : ''}</p>
                </div>
                <div className="media-stats">
                  <div className="media-engagement" title="Engagement total (likes + commentaires + partages)">
                    <Eye size={14} />
                    <span style={{ color: media.engagementRaw === 0 ? '#94a3b8' : 'inherit' }}>
                      {media.engagement}
                      {media.engagementRaw === 0 && <span style={{ fontSize: '10px', marginLeft: '4px' }}>(Aucune donnée)</span>}
                    </span>
                  </div>
                  <div className={`media-trend ${media.trend}`} title={media.trend === 'up' ? 'En progression' : 'Stable/baisse'}>
                    {media.trend === 'up' ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                  </div>
                </div>
                <div className="media-score" title={`Score d'influence: ${media.score}/100 (engagement 40%, followers 25%, articles 15%, ancienneté 10%, régularité 10%)`}>
                  <div className="score-circle" style={{ 
                    background: `conic-gradient(${media.score > 50 ? '#10b981' : media.score > 25 ? '#f59e0b' : '#ef4444'} ${media.score}%, #e5e7eb ${media.score}%)`
                  }}>
                    <span>{media.score}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="info-section">
        <div className="info-card">
          <div className="info-header">
            <h3>Alertes récentes</h3>
          </div>
          <div className="alerts-list">
            {recentAlerts.map((alert, index) => (
              <div key={index} className={`alert-item alert-${alert.type}`}>
                <div className="alert-indicator"></div>
                <div className="alert-content">
                  <div className="alert-header-info">
                    <AlertTriangle size={16} />
                    <span className="alert-media">{alert.media}</span>
                  </div>
                  <p className="alert-text">{alert.content}</p>
                  <div className="alert-time">
                    <Clock size={12} />
                    <span>{alert.time}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="info-card">
          <div className="info-header">
            <h3>Statistiques rapides</h3>
          </div>
          <div className="quick-stats">
            <div className="quick-stat-item">
              <div className="quick-stat-icon" style={{ background: '#3b82f615' }}>
                <ThumbsUp size={20} style={{ color: '#3b82f6' }} />
              </div>
              <div className="quick-stat-info">
                <p className="quick-stat-label">Engagement moyen/article</p>
                <h4>
                  {statsData && statsData.total_articles > 0 
                    ? formatNumber(Math.round(statsData.total_engagement / statsData.total_articles))
                    : '0'}
                </h4>
              </div>
            </div>

            <div className="quick-stat-item">
              <div className="quick-stat-icon" style={{ background: '#8b5cf615' }}>
                <Share2 size={20} style={{ color: '#8b5cf6' }} />
              </div>
              <div className="quick-stat-info">
                <p className="quick-stat-label">Partages sociaux</p>
                <h4>
                  {statsData?.engagement_details?.partages 
                    ? formatNumber(statsData.engagement_details.partages)
                    : '0'}
                </h4>
              </div>
            </div>

            <div className="quick-stat-item">
              <div className="quick-stat-icon" style={{ background: '#10b98115' }}>
                <MessageCircle size={20} style={{ color: '#10b981' }} />
              </div>
              <div className="quick-stat-info">
                <p className="quick-stat-label">Commentaires</p>
                <h4>
                  {statsData?.engagement_details?.commentaires 
                    ? formatNumber(statsData.engagement_details.commentaires)
                    : '0'}
                </h4>
              </div>
            </div>

            <div className="quick-stat-item">
              <div className="quick-stat-icon" style={{ background: '#f59e0b15' }}>
                <Heart size={20} style={{ color: '#f59e0b' }} />
              </div>
              <div className="quick-stat-info">
                <p className="quick-stat-label">Likes totaux</p>
                <h4>
                  {statsData?.engagement_details?.likes 
                    ? formatNumber(statsData.engagement_details.likes)
                    : '0'}
                </h4>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );

  const renderMediaList = () => {
    // Afficher un loader pendant le chargement initial
    if (loading && mediaList.length === 0) {
      return (
        <div className="loading-container" style={{ 
          display: 'flex', 
          flexDirection: 'column',
          alignItems: 'center', 
          justifyContent: 'center',
          minHeight: '400px',
          gap: '1rem'
        }}>
          <div className="spinner" style={{ borderTopColor: '#3b82f6' }}></div>
          <p style={{ color: '#64748b', fontSize: '1rem' }}>Chargement des médias...</p>
        </div>
      );
    }
    
    // Filtrer les médias selon la recherche
    const filteredMedia = mediaList.filter(media =>
      media.name.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
      <div className="media-grid-container">
        {/* Toaster pour les notifications pop-up */}
        <Toaster 
          position="top-right"
          reverseOrder={false}
          toastOptions={{
            duration: 4000,
            style: {
              borderRadius: '10px',
              fontSize: '14px',
              padding: '12px 16px'
            }
          }}
        />
        
        {/* Barre de recherche moderne */}
        <div className="media-search-bar">
          <div className="search-input-wrapper">
            <Search className="search-icon" size={20} />
            <input
              type="text"
              placeholder="Rechercher un média..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
            {searchQuery && (
              <button 
                className="search-clear"
                onClick={() => setSearchQuery('')}
              >
                <X size={18} />
              </button>
            )}
          </div>
          <div className="search-results-count">
            {filteredMedia.length} média{filteredMedia.length > 1 ? 's' : ''} trouvé{filteredMedia.length > 1 ? 's' : ''}
          </div>
        </div>

        {/* Grille de médias */}
        <div className="media-grid">
          {filteredMedia.length > 0 ? (
            filteredMedia.map((media) => (
              <div 
                key={media.id} 
                className="media-card-simple"
                onClick={() => handleMediaSelect(media)}
                style={{ border: `2px solid ${media.couleur || '#e5e7eb'}` }}
              >
                <div className="media-card-icon" style={{ backgroundColor: `${media.couleur || '#3b82f6'}15` }}>
                  <Newspaper size={24} style={{ color: media.couleur || '#3b82f6' }} />
                </div>
                <h3>{media.name}</h3>
                <div className="media-card-articles" style={{ color: media.couleur || '#3b82f6' }}>
                  {media.total_articles || media.articles || 0} articles
                </div>
                {media.score_influence !== undefined && (
                  <div style={{ 
                    marginTop: '8px', 
                    fontSize: '13px', 
                    fontWeight: '600',
                    color: '#f59e0b',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '4px'
                  }}>
                    <TrendingUp size={16} />
                    {media.score_influence.toFixed(1)}/10
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="no-results">
              <Search size={48} />
              <p>Aucun média trouvé pour "{searchQuery}"</p>
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderRanking = () => (
    <div className="ranking-container">
      <div className="section-header">
        <h2>Classement des médias</h2>
        <p>Performance globale des médias surveillés</p>
      </div>
      <div className="ranking-list">
        {topMedia.map((media, index) => (
          <div key={index} className="ranking-card">
            <div className="ranking-position">
              <span className={`rank-badge rank-${index + 1}`}>{index + 1}</span>
            </div>
            <div className="ranking-content">
              <h3>{media.name}</h3>
              <div className="ranking-metrics">
                <div className="metric">
                  <Newspaper size={16} />
                  <span>{media.articles} articles</span>
                </div>
                <div className="metric">
                  <Eye size={16} />
                  <span>{media.engagement}</span>
                </div>
                <div className={`metric trend-${media.trend}`}>
                  {media.trend === 'up' ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                  <span>{media.trend === 'up' ? 'En hausse' : 'En baisse'}</span>
                </div>
              </div>
            </div>
            <div className="ranking-score">
              <div className="score-circle-large" style={{ 
                background: `conic-gradient(#10b981 ${media.score}%, #e5e7eb ${media.score}%)`
              }}>
                <span>{media.score}</span>
              </div>
              <p>Score</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderMediaDetails = () => {
    // Utiliser les vraies données de l'API ou des données par défaut
    const thematics = (selectedMedia.categories_distribution || []).map(cat => ({
      name: cat.categorie || cat.name,
      value: cat.percentage || cat.value || 0,
      color: cat.couleur || cat.color || '#6B7280'
    }));
    
    // Si pas de données, utiliser des données par défaut
    const thematicsToDisplay = thematics.length > 0 ? thematics : [
      { name: 'Politique', value: 45, color: '#3b82f6' },
      { name: 'Économie', value: 28, color: '#10b981' },
      { name: 'Social', value: 18, color: '#8b5cf6' },
      { name: 'Culture', value: 9, color: '#f59e0b' }
    ];

    // Données d'activité pour le graphique (vraies données de l'API)
    const mediaActivityData = selectedMedia.activity_chart || activityData;

    // Publications avec analyse de sentiments - Utiliser les vrais articles récents
    const generatePublications = () => {
      if (!recentArticles || recentArticles.length === 0) {
        return [];
      }

      // Utiliser les vrais pourcentages de l'API ou des valeurs par défaut
      const { joy = 2, sadness = 25, anger = 65, love = 1, neutral = 7, total_posts = 0 } = sentimentsData || {};

      // Convertir les articles récents en publications avec sentiments
      return recentArticles.map((article, index) => {
        // Extraire les 5 premières lignes du contenu (environ 250 caractères)
        const contentPreview = article.description 
          ? article.description.substring(0, 250) + '...'
          : 'Aucun contenu disponible';

        return {
          id: article.id,
          title: article.titre,
          date: article.temps_ecoule,
          summary: contentPreview,
          link: article.url || '#',
          sentiments: { joy, sadness, anger, love, neutral },
          likes: article.likes || 0,
          commentaires: article.commentaires || 0,
          partages: article.partages || 0,
          engagementTotal: article.engagement_total || 0,
          totalReactions: article.engagement_total || 0,
          comments: [] // Pas de commentaires pour l'instant
        };
      });
    };

    const publications = generatePublications();

    const sentimentIcons = {
      joy: { icon: Smile, color: '#10b981', label: 'Joie' },
      sadness: { icon: Frown, color: '#3b82f6', label: 'Tristesse' },
      anger: { icon: Angry, color: '#ef4444', label: 'Colère' },
      love: { icon: Heart, color: '#ec4899', label: 'Amour' },
      neutral: { icon: Meh, color: '#64748b', label: 'Neutre' }
    };

    // Filtrer les publications par sentiment
    const filterPublications = () => {
      if (!publications || publications.length === 0) return [];
      if (sentimentFilter === 'all') return publications;
      
      return [...publications].sort((a, b) => {
        return b.sentiments[sentimentFilter] - a.sentiments[sentimentFilter];
      });
    };

    const filteredPublications = filterPublications();
    // Utiliser displayedPublications au lieu de pagination
    const currentPublications = filteredPublications.slice(0, displayedPublications);
    const hasMorePublications = displayedPublications < filteredPublications.length;

    const handleSentimentClick = (publication, sentimentType) => {
      setSelectedPublication(publication);
      setShowSentimentDetails(sentimentType);
    };

    const closeSentimentModal = () => {
      setSelectedPublication(null);
      setShowSentimentDetails(false);
    };

    const getContentByTab = () => {
      switch(activeTab) {
        case 'media':
          return 'Analyse par média';
        case 'thematic':
          return 'Analyse thématique';
        case 'sensitive':
          return 'Contenus sensibles';
        case 'activity':
          return 'Activité & conformité';
        default:
          return 'Analyse détaillée';
      }
    };

    const totalThematic = Math.round(thematicsToDisplay.reduce((acc, t) => acc + t.value, 0));

    // Fonction pour exporter l'analyse du média en PNG format A4
    const exportMediaAnalysisToPNG = async () => {
      try {
        const html2canvas = (await import('html2canvas')).default;
        
        const periodLabel = mediaAnalysisTimeRange === 'all' ? 'Tous_les_temps' : 
                           mediaAnalysisTimeRange === '1h' ? '1_heure' : 
                           mediaAnalysisTimeRange === '6h' ? '6_heures' : 
                           mediaAnalysisTimeRange === '24h' ? '24_heures' : 
                           mediaAnalysisTimeRange === '7d' ? '7_jours' : '30_jours';

        const loadingToast = toast.loading('Préparation de l\'export format A4...');

        // Créer un conteneur format A4
        const exportContainer = document.createElement('div');
        exportContainer.style.cssText = `
          position: fixed;
          left: -9999px;
          top: 0;
          width: 794px;
          background: white;
          padding: 40px;
          font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        `;
        document.body.appendChild(exportContainer);

        // Titre
        const title = document.createElement('div');
        title.style.cssText = `
          font-size: 24px;
          font-weight: 700;
          color: #1e293b;
          margin-bottom: 8px;
          text-align: center;
        `;
        title.textContent = `Analyse Média: ${selectedMedia.name} - ${periodLabel}`;
        exportContainer.appendChild(title);

        // Date
        const dateDiv = document.createElement('div');
        dateDiv.style.cssText = `
          font-size: 14px;
          color: #64748b;
          margin-bottom: 30px;
          text-align: center;
        `;
        dateDiv.textContent = new Date().toLocaleDateString('fr-FR', { 
          weekday: 'long', 
          year: 'numeric', 
          month: 'long', 
          day: 'numeric' 
        });
        exportContainer.appendChild(dateDiv);

        // Sections à exporter
        const sectionsToExport = [
          { selector: '.media-profile-header', name: 'Profil', marginBottom: '20px' },
          { selector: '.details-stats-grid', name: 'Statistiques', marginBottom: '30px' },
          { selector: '.details-charts-section', name: 'Graphiques', marginBottom: '20px' }
        ];

        // Cloner et ajouter chaque section
        for (let i = 0; i < sectionsToExport.length; i++) {
          const section = sectionsToExport[i];
          const element = document.querySelector(section.selector);
          
          if (element) {
            toast.loading(`Ajout ${i + 1}/${sectionsToExport.length}: ${section.name}...`, { id: loadingToast });
            
            const clone = element.cloneNode(true);
            clone.style.cssText = `
              width: 100%;
              background: transparent;
              margin-bottom: ${section.marginBottom};
            `;
            exportContainer.appendChild(clone);
          }
        }

        // Attendre le rendu
        toast.loading('Génération de l\'image...', { id: loadingToast });
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Capturer en PNG
        const canvas = await html2canvas(exportContainer, {
          backgroundColor: '#ffffff',
          scale: 2,
          logging: false,
          useCORS: true,
          width: 794,
          windowWidth: 794
        });

        // Télécharger
        const link = document.createElement('a');
        link.download = `Analyse_${selectedMedia.name.replace(/\s+/g, '_')}_${periodLabel}_${new Date().toISOString().split('T')[0]}.png`;
        link.href = canvas.toDataURL('image/png');
        link.click();

        // Nettoyer
        document.body.removeChild(exportContainer);
        toast.success('Analyse média exportée en format A4!', { id: loadingToast });
        
      } catch (error) {
        console.error('Erreur export:', error);
        toast.error('Erreur lors de l\'export de l\'analyse');
      }
    };

    return (
      <div className="media-details-container">
        {/* En-tête avec retour et sélecteur de temps */}
        <div className="media-details-top">
          <button className="back-btn" onClick={handleBackToList}>
            <ArrowLeft size={20} />
            Retour à la liste
          </button>
          
          <div className="details-time-selector">
            <Clock size={18} style={{ color: selectedMedia.couleur }} />
            <span style={{ color: selectedMedia.couleur }}>Période :</span>
            <div 
              className="time-range-buttons-compact"
              style={{
                '--media-color': selectedMedia.couleur,
                '--media-color-light': `${selectedMedia.couleur}20`,
                '--media-color-medium': `${selectedMedia.couleur}40`
              }}
            >
              {timeRanges.map((range) => (
                <button
                  key={range.value}
                  className={`time-btn ${mediaAnalysisTimeRange === range.value ? 'active' : ''}`}
                  onClick={() => setMediaAnalysisTimeRange(range.value)}
                  style={mediaAnalysisTimeRange === range.value ? {
                    background: selectedMedia.couleur,
                    borderColor: selectedMedia.couleur,
                    color: 'white'
                  } : {}}
                >
                  {range.label}
                </button>
              ))}
            </div>
          </div>

          {/* Bouton export */}
          <button 
            className="export-media-analysis-btn"
            onClick={exportMediaAnalysisToPNG}
            title="Exporter l'analyse en PNG"
            style={{
              background: selectedMedia.couleur || selectedMedia.color,
              boxShadow: `0 4px 12px ${selectedMedia.couleur || selectedMedia.color}50`
            }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7 10 12 15 17 10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            <span>Exporter</span>
            <span className="export-period-badge">{mediaAnalysisTimeRange === 'all' ? 'Tous' : mediaAnalysisTimeRange === '1h' ? '1h' : mediaAnalysisTimeRange === '6h' ? '6h' : mediaAnalysisTimeRange === '24h' ? '24h' : mediaAnalysisTimeRange === '7d' ? '7j' : '30j'}</span>
          </button>
        </div>

        {/* Profil du média */}
        <div className="media-profile-header" style={{ borderLeftColor: selectedMedia.couleur || selectedMedia.color }}>
          <div className="media-profile-icon" style={{ backgroundColor: `${selectedMedia.couleur || selectedMedia.color}15` }}>
            <Newspaper size={32} style={{ color: selectedMedia.couleur || selectedMedia.color }} />
          </div>
          <div className="media-profile-info">
            <h2>{selectedMedia.name}</h2>
            <p className="media-profile-subtitle">{getContentByTab()}</p>
          </div>
          <div className="media-influence-score">
            <div className="score-circle-xlarge" style={{ 
              background: `conic-gradient(${selectedMedia.couleur || selectedMedia.color} ${selectedMedia.scoreInfluence || 0}%, #e5e7eb ${selectedMedia.scoreInfluence || 0}%)`
            }}>
              <div className="score-inner">
                <span className="score-number">{selectedMedia.scoreInfluence !== undefined ? Math.round(selectedMedia.scoreInfluence) : '0'}</span>
                <span className="score-label">SCORE</span>
              </div>
            </div>
            <p>Score d'influence</p>
          </div>
        </div>

        {/* Statistiques principales */}
        <div className="details-stats-grid">
          <div className="detail-stat-card">
            <div className="detail-stat-icon" style={{ backgroundColor: `${selectedMedia.couleur || selectedMedia.color}15` }}>
              <Newspaper size={24} style={{ color: selectedMedia.couleur || selectedMedia.color }} />
            </div>
            <div className="detail-stat-content">
              <p className="detail-stat-label">Articles publiés</p>
              <h3 className="detail-stat-value" style={{ color: selectedMedia.couleur || '#0f172a' }}>{selectedMedia.stats?.total_articles || selectedMedia.articles || 0}</h3>
            </div>
          </div>

          <div className="detail-stat-card">
            <div className="detail-stat-icon" style={{ backgroundColor: `${selectedMedia.couleur || '#10b981'}15` }}>
              <Eye size={24} style={{ color: selectedMedia.couleur || '#10b981' }} />
            </div>
            <div className="detail-stat-content">
              <p className="detail-stat-label">Engagement total</p>
              <h3 className="detail-stat-value" style={{ color: selectedMedia.couleur || '#0f172a' }}>{formatNumber(selectedMedia.stats?.total_engagement || 0)}</h3>
            </div>
          </div>

          <div className="detail-stat-card">
            <div className="detail-stat-icon" style={{ backgroundColor: `${selectedMedia.couleur || '#8b5cf6'}15` }}>
              <Share2 size={24} style={{ color: selectedMedia.couleur || '#8b5cf6' }} />
            </div>
            <div className="detail-stat-content">
              <p className="detail-stat-label">Partages</p>
              <h3 className="detail-stat-value" style={{ color: selectedMedia.couleur || '#0f172a' }}>{formatNumber(selectedMedia.stats?.partages || 0)}</h3>
            </div>
          </div>

          <div className="detail-stat-card">
            <div className="detail-stat-icon" style={{ backgroundColor: `${selectedMedia.couleur || '#10b981'}15` }}>
              <Activity size={24} style={{ color: selectedMedia.couleur || '#10b981' }} />
            </div>
            <div className="detail-stat-content">
              <p className="detail-stat-label"> Taux de régularité (90j)</p>
              <h3 className="detail-stat-value" style={{ color: selectedMedia.couleur || '#0f172a' }}>
                {selectedMedia.regularityRate !== undefined ? `${selectedMedia.regularityRate}%` : 'N/A'}
              </h3>
              <p style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>
                Constance des publications
              </p>
            </div>
          </div>
        </div>

        {/* Graphiques et analyses */}
        <div className="details-charts-section" style={{ position: 'relative' }}>
          {/* Graphique d'activité courbe */}
          <div className="detail-chart-card large">
            <div className="chart-card-header">
              <div>
                <h3>Activité de publication</h3>
                <p>Évolution du nombre d'articles sur {mediaAnalysisTimeRange === 'all' ? 'tous les temps' : mediaAnalysisTimeRange === '1h' ? '1 heure' : mediaAnalysisTimeRange === '6h' ? '6 heures' : mediaAnalysisTimeRange === '24h' ? '24 heures' : mediaAnalysisTimeRange === '7d' ? '7 jours' : '30 jours'}</p>
              </div>
            </div>
            <div className="activity-chart-curved" style={{ position: 'relative', height: '300px', padding: '20px 10px' }}>
              {mediaActivityData && mediaActivityData.length > 0 ? (
                <svg viewBox="0 0 1000 300" preserveAspectRatio="xMidYMid meet" style={{ width: '100%', height: '100%' }}>
                  <defs>
                  <linearGradient id={`barGradient-${selectedMedia.id}`} x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style={{ stopColor: selectedMedia.couleur || '#3b82f6', stopOpacity: 0.8 }} />
                    <stop offset="100%" style={{ stopColor: selectedMedia.couleur || '#3b82f6', stopOpacity: 0.4 }} />
                  </linearGradient>
                  <linearGradient id={`lineGradient-${selectedMedia.id}`} x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style={{ stopColor: selectedMedia.couleur || '#3b82f6', stopOpacity: 1 }} />
                    <stop offset="100%" style={{ stopColor: selectedMedia.couleur || '#3b82f6', stopOpacity: 0.6 }} />
                  </linearGradient>
                  <filter id={`glow-${selectedMedia.id}`}>
                    <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                    <feMerge>
                      <feMergeNode in="coloredBlur"/>
                      <feMergeNode in="SourceGraphic"/>
                    </feMerge>
                  </filter>
                </defs>
                
                {/* Grille horizontale */}
                {[0, 25, 50, 75, 100].map((percent) => (
                  <g key={percent}>
                    <line
                      x1="40"
                      y1={`${20 + (100 - percent) * 2.4}px`}
                      x2="95%"
                      y2={`${20 + (100 - percent) * 2.4}px`}
                      stroke="#e5e7eb"
                      strokeWidth="1"
                      strokeDasharray="4,4"
                      opacity="0.5"
                    />
                    <text
                      x="5"
                      y={`${24 + (100 - percent) * 2.4}px`}
                      fill="#6b7280"
                      fontSize="11"
                      fontWeight="500"
                    >
                      {Math.round((300 * percent) / 100)}
                    </text>
                  </g>
                ))}
                
                {/* Barres */}
                {mediaActivityData.map((data, index) => {
                  const maxValue = Math.max(...mediaActivityData.map(d => d.value), 1);
                  const barHeight = (data.value / maxValue) * 220;
                  const barWidth = Math.min(40, (920 / mediaActivityData.length) - 10);
                  const spacing = 920 / mediaActivityData.length;
                  const xPos = 60 + (index * spacing) + (spacing - barWidth) / 2;
                  return (
                    <g key={index}>
                      <rect
                        x={xPos}
                        y={240 - barHeight}
                        width={barWidth}
                        height={barHeight}
                        fill={`url(#barGradient-${selectedMedia.id})`}
                        rx="4"
                        ry="4"
                        style={{
                          filter: `drop-shadow(0 4px 8px ${selectedMedia.couleur || '#3b82f6'}40)`
                        }}
                      />
                      <text
                        x={xPos + barWidth / 2}
                        y={235 - barHeight}
                        fill={selectedMedia.couleur || '#3b82f6'}
                        fontSize="12"
                        fontWeight="700"
                        textAnchor="middle"
                      >
                        {data.value}
                      </text>
                      <text
                        x={xPos + barWidth / 2}
                        y="270"
                        fill="#6b7280"
                        fontSize="11"
                        textAnchor="middle"
                        fontWeight="500"
                      >
                        {data.hour}
                      </text>
                    </g>
                  );
                })}
                
                {/* Courbe lisse par-dessus */}
                {mediaActivityData.length > 1 && (
                  <>
                    {/* Zone sous la courbe (gradient) */}
                    <path
                      d={(() => {
                        const maxValue = Math.max(...mediaActivityData.map(d => d.value), 1);
                        const barWidth = Math.min(40, (920 / mediaActivityData.length) - 10);
                        const spacing = 920 / mediaActivityData.length;
                        
                        let pathData = `M ${60 + (spacing - barWidth) / 2 + barWidth / 2} 240 `;
                        
                        mediaActivityData.forEach((data, index) => {
                          const barHeight = (data.value / maxValue) * 220;
                          const xPos = 60 + (index * spacing) + (spacing - barWidth) / 2 + barWidth / 2;
                          const yPos = 240 - barHeight;
                          
                          if (index === 0) {
                            pathData += `L ${xPos} ${yPos} `;
                          } else {
                            const prevData = mediaActivityData[index - 1];
                            const prevHeight = (prevData.value / maxValue) * 220;
                            const prevX = 60 + ((index - 1) * spacing) + (spacing - barWidth) / 2 + barWidth / 2;
                            const prevY = 240 - prevHeight;
                            
                            const cpX1 = prevX + (xPos - prevX) / 3;
                            const cpY1 = prevY;
                            const cpX2 = prevX + (2 * (xPos - prevX)) / 3;
                            const cpY2 = yPos;
                            
                            pathData += `C ${cpX1} ${cpY1}, ${cpX2} ${cpY2}, ${xPos} ${yPos} `;
                          }
                        });
                        
                        const lastIndex = mediaActivityData.length - 1;
                        const lastXPos = 60 + (lastIndex * spacing) + (spacing - barWidth) / 2 + barWidth / 2;
                        pathData += `L ${lastXPos} 240 Z`;
                        
                        return pathData;
                      })()}
                      fill={`url(#lineGradient-${selectedMedia.id})`}
                      opacity="0.15"
                    />
                    
                    {/* Ligne de courbe */}
                    <path
                      d={(() => {
                        const maxValue = Math.max(...mediaActivityData.map(d => d.value), 1);
                        const barWidth = Math.min(40, (920 / mediaActivityData.length) - 10);
                        const spacing = 920 / mediaActivityData.length;
                        
                        let pathData = '';
                        
                        mediaActivityData.forEach((data, index) => {
                          const barHeight = (data.value / maxValue) * 220;
                          const xPos = 60 + (index * spacing) + (spacing - barWidth) / 2 + barWidth / 2;
                          const yPos = 240 - barHeight;
                          
                          if (index === 0) {
                            pathData += `M ${xPos} ${yPos} `;
                          } else {
                            const prevData = mediaActivityData[index - 1];
                            const prevHeight = (prevData.value / maxValue) * 220;
                            const prevX = 60 + ((index - 1) * spacing) + (spacing - barWidth) / 2 + barWidth / 2;
                            const prevY = 240 - prevHeight;
                            
                            const cpX1 = prevX + (xPos - prevX) / 3;
                            const cpY1 = prevY;
                            const cpX2 = prevX + (2 * (xPos - prevX)) / 3;
                            const cpY2 = yPos;
                            
                            pathData += `C ${cpX1} ${cpY1}, ${cpX2} ${cpY2}, ${xPos} ${yPos} `;
                          }
                        });
                        
                        return pathData;
                      })()}
                      stroke={selectedMedia.couleur || '#3b82f6'}
                      strokeWidth="3"
                      fill="none"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      filter={`url(#glow-${selectedMedia.id})`}
                    />
                    
                    {/* Points sur la courbe */}
                    {mediaActivityData.map((data, index) => {
                      const maxValue = Math.max(...mediaActivityData.map(d => d.value), 1);
                      const barHeight = (data.value / maxValue) * 220;
                      const barWidth = Math.min(40, (920 / mediaActivityData.length) - 10);
                      const spacing = 920 / mediaActivityData.length;
                      const xPos = 60 + (index * spacing) + (spacing - barWidth) / 2 + barWidth / 2;
                      const yPos = 240 - barHeight;
                      
                      return (
                        <g key={`point-${index}`}>
                          <circle
                            cx={xPos}
                            cy={yPos}
                            r="6"
                            fill="white"
                            stroke={selectedMedia.couleur || '#3b82f6'}
                            strokeWidth="3"
                            style={{
                              filter: `drop-shadow(0 2px 4px ${selectedMedia.couleur || '#3b82f6'}60)`
                            }}
                          />
                          <circle
                            cx={xPos}
                            cy={yPos}
                            r="3"
                            fill={selectedMedia.couleur || '#3b82f6'}
                          />
                        </g>
                      );
                    })}
                  </>
                )}
              </svg>
              ) : (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#6b7280' }}>
                  Chargement des données...
                </div>
              )}
            </div>
          </div>

          {/* Diagramme circulaire thématiques */}
          <div className="detail-chart-card">
            <div className="chart-card-header">
              <h3>Thématiques dominantes</h3>
              <p>Répartition des sujets traités</p>
            </div>
            <div className="pie-chart-container">
              <svg viewBox="0 0 200 200" className="pie-chart">
                {thematicsToDisplay.map((thematic, index) => {
                  const prevTotal = thematicsToDisplay.slice(0, index).reduce((acc, t) => acc + t.value, 0);
                  const startAngle = (prevTotal / totalThematic) * 360;
                  const angle = (thematic.value / totalThematic) * 360;
                  const endAngle = startAngle + angle;
                  
                  const startRad = (startAngle - 90) * Math.PI / 180;
                  const endRad = (endAngle - 90) * Math.PI / 180;
                  
                  const x1 = 100 + 80 * Math.cos(startRad);
                  const y1 = 100 + 80 * Math.sin(startRad);
                  const x2 = 100 + 80 * Math.cos(endRad);
                  const y2 = 100 + 80 * Math.sin(endRad);
                  
                  const largeArc = angle > 180 ? 1 : 0;
                  
                  return (
                    <path
                      key={index}
                      d={`M 100 100 L ${x1} ${y1} A 80 80 0 ${largeArc} 1 ${x2} ${y2} Z`}
                      fill={thematic.color}
                      stroke="white"
                      strokeWidth="2"
                    />
                  );
                })}
                <circle cx="100" cy="100" r="50" fill="white" />
                <text x="100" y="95" textAnchor="middle" fontSize="20" fontWeight="bold" fill="#1e293b">
                  {totalThematic}%
                </text>
                <text x="100" y="110" textAnchor="middle" fontSize="10" fill="#64748b">
                  Couverture
                </text>
              </svg>
              
              <div className="pie-chart-legend">
                {thematicsToDisplay.map((thematic, index) => (
                  <div key={index} className="legend-item">
                    <div className="legend-color" style={{ backgroundColor: thematic.color }}></div>
                    <span className="legend-label">{thematic.name}</span>
                    <span className="legend-value">{thematic.value}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Articles récents */}
        <div 
          className="recent-articles-section"
          style={{
            '--media-color': selectedMedia.couleur || '#3b82f6',
            '--media-color-light': `${selectedMedia.couleur || '#3b82f6'}15`,
            '--media-color-medium': `${selectedMedia.couleur || '#3b82f6'}40`
          }}
        >
          <div className="section-title-bar">
            <h3 style={{ color: selectedMedia.couleur || '#0f172a' }}>Contenus récents</h3>
            <span 
              className="articles-count"
              style={{
                background: `linear-gradient(135deg, ${selectedMedia.couleur || '#3b82f6'} 0%, ${selectedMedia.couleur || '#8b5cf6'} 100%)`,
                boxShadow: `0 4px 12px ${selectedMedia.couleur || '#3b82f6'}30`
              }}
            >
              {recentArticles.length} articles
            </span>
          </div>
          
          <div className="articles-list-horizontal">
            {articlesLoading && recentArticles.length === 0 ? (
              <div className="loading-overlay">
                <div className="spinner" style={{ borderTopColor: selectedMedia.couleur || '#3b82f6' }}></div>
              </div>
            ) : recentArticles.length > 0 ? recentArticles.map((article) => (
              <a 
                key={article.id} 
                href={article.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="article-card"
                style={{ 
                  textDecoration: 'none', 
                  color: 'inherit',
                  borderColor: `${selectedMedia.couleur || '#3b82f6'}30`
                }}
              >
                <div 
                  className="article-card-accent" 
                  style={{ backgroundColor: selectedMedia.couleur || '#3b82f6' }}
                ></div>
                <div className="article-header">
                  <span 
                    className="article-category" 
                    style={{ 
                      backgroundColor: article.categorie_couleur || '#6B7280',
                      color: 'white',
                      padding: '4px 12px',
                      borderRadius: '12px',
                      fontSize: '12px',
                      fontWeight: '600'
                    }}
                  >
                    {article.categorie || 'Autre'}
                  </span>
                </div>
                <h4 className="article-title">{article.titre}</h4>
                {article.description && (
                  <p className="article-description">{article.description}</p>
                )}
                <div className="article-footer">
                  <div className="article-meta" style={{ backgroundColor: `${selectedMedia.couleur || '#3b82f6'}10` }}>
                    <Clock size={14} style={{ color: selectedMedia.couleur || '#3b82f6' }} />
                    <span>{article.temps_ecoule}</span>
                  </div>
                  <div className="article-engagement" style={{ backgroundColor: `${selectedMedia.couleur || '#3b82f6'}10` }}>
                    <Eye size={14} style={{ color: selectedMedia.couleur || '#3b82f6' }} />
                    <span>{formatNumber(article.vues)} vues</span>
                  </div>
                </div>
              </a>
            )) : (
              <div className="no-articles">
                <Newspaper size={48} />
                <p>Aucun article récent pour cette période</p>
              </div>
            )}
          </div>
        </div>

        {/* Analyse déontologique */}
        <div 
          className="sentiment-analysis-section"
          style={{
            '--media-color': selectedMedia.couleur || '#3b82f6',
            '--media-color-light': `${selectedMedia.couleur || '#3b82f6'}15`,
            '--media-color-medium': `${selectedMedia.couleur || '#3b82f6'}40`
          }}
        >
          <div className="section-title-bar">
            <div>
              <h3 style={{ color: selectedMedia.couleur || '#0f172a' }}>Analyse Déontologique</h3>
              <p className="section-subtitle">Évaluation de la qualité journalistique des publications (scores 0-10)</p>
            </div>
            {sentimentsData && (
              <span 
                className="posts-count-badge"
                style={{
                  background: `linear-gradient(135deg, ${selectedMedia.couleur || '#3b82f6'} 0%, ${selectedMedia.couleur || '#8b5cf6'} 100%)`,
                  boxShadow: `0 4px 12px ${selectedMedia.couleur || '#3b82f6'}30`
                }}
              >
                Score moyen: {sentimentsData.score_moyen}/10
              </span>
            )}
          </div>

          {articlesLoading && analyzedArticles.length === 0 ? (
            <div className="loading-overlay" style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '60px 20px',
              minHeight: '300px'
            }}>
              <div className="spinner" style={{ 
                borderTopColor: selectedMedia.couleur || '#3b82f6',
                width: '50px',
                height: '50px',
                marginBottom: '20px'
              }}></div>
              <p style={{ 
                marginTop: '1rem', 
                color: selectedMedia.couleur || '#3b82f6',
                fontSize: '1.1rem',
                fontWeight: '600'
              }}>
                 Analyse déontologique en cours...
              </p>
              <p style={{ 
                color: '#64748b',
                fontSize: '0.9rem',
                marginTop: '0.5rem'
              }}>
                Le LLM analyse la qualité journalistique des 5 premiers articles
              </p>
            </div>
          ) : !sentimentsData ? (
            <div className="no-data-message">
              <MessageCircle size={48} />
              <p>Aucune analyse disponible</p>
            </div>
          ) : (
            <>
              {/* Liste de tous les articles avec scores déontologiques */}
              {analyzedArticles && analyzedArticles.length > 0 && (
                <div className="deontology-articles-list">
                  <h4 style={{ color: selectedMedia.couleur || '#0f172a', marginBottom: '20px' }}>
                    Posts analysés - Du plus récent au plus ancien ({recentArticles.length} au total)
                  </h4>
                  
                  <div className="articles-deontology-detailed">
                    {analyzedArticles.map((article, index) => {
                      // L'article a déjà son score et son interprétation
                      // Si le score est négatif (erreur), utiliser un score par défaut
                      const score = article.score >= 0 ? article.score : 5;
                      const interpretation = article.score >= 0 
                        ? article.interpretation 
                        : "En attente d'analyse complète";
                      
                      // Déterminer la couleur du score
                      const getScoreColor = (score) => {
                        if (score >= 9) return '#10b981'; // Vert
                        if (score >= 7) return '#3b82f6'; // Bleu
                        if (score >= 5) return '#f59e0b'; // Orange
                        if (score >= 3) return '#ef4444'; // Rouge
                        return '#dc2626'; // Rouge foncé
                      };
                      
                      const scoreColor = getScoreColor(score);
                      
                      // Fonction pour ouvrir l'URL de l'article
                      const handleArticleClick = () => {
                        if (article.url) {
                          window.open(article.url, '_blank', 'noopener,noreferrer');
                        }
                      };
                      
                      return (
                        <div 
                          key={article.id || index} 
                          className="article-deontology-row"
                          onClick={handleArticleClick}
                          style={{ cursor: article.url ? 'pointer' : 'default' }}
                        >
                          {/* Article info */}
                          <div className="article-info-section">
                            <div className="article-title-row">
                              <h5 className="article-deontology-title">
                                {article.titre}
                                {article.url && (
                                  <ExternalLink size={16} style={{ 
                                    color: selectedMedia.couleur || '#3b82f6', 
                                    marginLeft: '8px',
                                    opacity: 0.7
                                  }} />
                                )}
                              </h5>
                              <span className="article-date">{article.temps_ecoule}</span>
                            </div>
                            {article.description && (
                              <p className="article-excerpt">
                                {article.description.substring(0, 120)}...
                              </p>
                            )}
                          </div>
                          
                          {/* Score circulaire */}
                          <div className="deontology-score-section">
                            <div className="score-circle-container">
                              <div 
                                className="score-circle-deontology" 
                                style={{ 
                                  background: `conic-gradient(${scoreColor} ${score * 10}%, #e5e7eb ${score * 10}%)`
                                }}
                              >
                                <div className="score-inner-deontology">
                                  <span className="score-number-deontology" style={{ color: scoreColor }}>
                                    {score}
                                  </span>
                                  <span className="score-label-deontology">/10</span>
                                </div>
                              </div>
                            </div>
                          </div>
                          
                          {/* Interprétation */}
                          <div className="interpretation-section">
                            <p className="article-interpretation">{interpretation}</p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                  
                  {/* Bouton "Voir plus" si il y a plus d'articles */}
                  {analyzedArticles.length < recentArticles.length && (
                    <div className="load-more-container">
                      <button 
                        className="load-more-btn"
                        onClick={loadMorePublications}
                        disabled={articlesLoading}
                        style={{
                          background: `linear-gradient(135deg, ${selectedMedia.couleur || '#3b82f6'} 0%, ${selectedMedia.couleur || '#8b5cf6'} 100%)`,
                          boxShadow: `0 4px 16px ${selectedMedia.couleur || '#3b82f6'}40`,
                          opacity: articlesLoading ? 0.6 : 1,
                          cursor: articlesLoading ? 'wait' : 'pointer'
                        }}
                      >
                        {articlesLoading ? (
                          <>
                            <div className="spinner-small" style={{ borderTopColor: '#fff' }}></div>
                            <span>Analyse en cours...</span>
                          </>
                        ) : (
                          <>
                            <span>Voir plus d'articles</span>
                            <ChevronDown size={20} />
                          </>
                        )}
                      </button>
                    </div>
                  )}
                  
                  {/* Indicateur fin de liste */}
                  {analyzedArticles.length >= recentArticles.length && recentArticles.length > 5 && (
                    <div className="end-of-list">
                      <div className="end-line"></div>
                      <span className="end-text">Tous les articles affichés</span>
                      <div className="end-line"></div>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>

        {/* Bouton retour en haut */}
        {showScrollTop && (
          <button 
            className="scroll-to-top-btn"
            onClick={scrollToTop}
            style={{
              background: selectedMedia.couleur || '#3b82f6',
              boxShadow: `0 4px 16px ${selectedMedia.couleur || '#3b82f6'}40`
            }}
          >
            <ArrowUp size={24} />
          </button>
        )}

        {/* Modal des détails du sentiment */}
        {showSentimentDetails && selectedPublication && (
          <div className="sentiment-modal-overlay" onClick={closeSentimentModal}>
            <div className="sentiment-modal" onClick={(e) => e.stopPropagation()}>
              <div className="sentiment-modal-header">
                <div className="sentiment-modal-title">
                  {React.createElement(sentimentIcons[showSentimentDetails].icon, { 
                    size: 24, 
                    style: { color: sentimentIcons[showSentimentDetails].color } 
                  })}
                  <h3>Réactions : {sentimentIcons[showSentimentDetails].label}</h3>
                </div>
                <button className="sentiment-modal-close" onClick={closeSentimentModal}>
                  <X size={24} />
                </button>
              </div>
              
              <div className="sentiment-modal-body">
                <div className="sentiment-modal-publication">
                  <h4>{selectedPublication.title}</h4>
                  <p>{selectedPublication.summary}</p>
                </div>
                
                <div className="sentiment-modal-stats">
                  <div className="modal-stat">
                    <span className="modal-stat-label">Pourcentage</span>
                    <span className="modal-stat-value" style={{ color: sentimentIcons[showSentimentDetails].color }}>
                      {selectedPublication.sentiments[showSentimentDetails]}%
                    </span>
                  </div>
                  <div className="modal-stat">
                    <span className="modal-stat-label">Nombre de réactions</span>
                    <span className="modal-stat-value">
                      {Math.round((selectedPublication.sentiments[showSentimentDetails] / 100) * selectedPublication.totalReactions)}
                    </span>
                  </div>
                </div>

                <h4 className="comments-title">Commentaires et réactions</h4>
                <div className="sentiment-comments-list">
                  {selectedPublication.comments
                    .filter(comment => comment.sentiment === showSentimentDetails)
                    .map((comment, index) => (
                      <div key={index} className="sentiment-comment">
                        <div className="comment-icon" style={{ backgroundColor: `${sentimentIcons[showSentimentDetails].color}15` }}>
                          {React.createElement(sentimentIcons[showSentimentDetails].icon, { 
                            size: 16, 
                            style: { color: sentimentIcons[showSentimentDetails].color } 
                          })}
                        </div>
                        <p>{comment.text}</p>
                      </div>
                    ))}
                  
                  {selectedPublication.comments.filter(c => c.sentiment === showSentimentDetails).length === 0 && (
                    <p className="no-comments">Aucun commentaire pour ce sentiment</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderAlertsSystem = () => {
    const getAlertIcon = (type) => {
      const icons = {
        pic_engagement: TrendingUp,
        chute_engagement: TrendingDown,
        inactivite: Clock,
        explosion_publications: Activity,
        baisse_influence: TrendingDown,
        regularite_faible: Clock,
        ratio_engagement_faible: Eye,
        ratio_engagement_eleve: Bell,
        nouveau_media_actif: Activity,
        thematique_dominante: Filter,
        record_engagement: TrendingUp,
        commentaires_eleves: MessageCircle
      };
      return icons[type] || AlertTriangle;
    };

    const getAlertColor = (severite) => {
      const colors = {
        critical: '#dc2626',
        high: '#ea580c',
        medium: '#ca8a04',
        low: '#2563eb'
      };
      return colors[severite] || '#6b7280';
    };

    const getSeverityLabel = (severity) => {
      const labels = {
        critical: { label: 'CRITIQUE', color: '#dc2626' },
        high: { label: 'ÉLEVÉE', color: '#ef4444' },
        medium: { label: 'MOYENNE', color: '#f59e0b' },
        low: { label: 'INFO', color: '#10b981' }
      };
      return labels[severity] || { label: 'INCONNU', color: '#6b7280' };
    };

    const formatTimeAgo = (dateString) => {
      const date = new Date(dateString);
      const now = new Date();
      const diffMs = now - date;
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      const diffDays = Math.floor(diffMs / 86400000);

      if (diffMins < 1) return 'À l\'instant';
      if (diffMins < 60) return `Il y a ${diffMins} min`;
      if (diffHours < 24) return `Il y a ${diffHours}h`;
      if (diffDays < 7) return `Il y a ${diffDays}j`;
      
      return date.toLocaleDateString('fr-FR', { 
        day: 'numeric', 
        month: 'short',
        hour: '2-digit',
        minute: '2-digit'
      });
    };

    const totalAlerts = alertsStats?.total_active || 0;
    const criticalAlerts = alertsStats?.by_severity?.critical || 0;
    const highAlerts = alertsStats?.by_severity?.high || 0;

    return (
      <div className="alerts-system-container">
        <div className="alerts-header">
          <div className="alerts-header-content">
            <div className="alerts-header-icon">
              <Bell size={32} />
            </div>
            <div>
              <h2>Système d'alerte</h2>
              <p>Surveillance en temps réel des médias et détection des anomalies</p>
            </div>
          </div>
          
          <div className="alerts-stats-summary">
            <div className="alert-stat-item critical">
              <AlertTriangle size={20} />
              <div>
                <span className="stat-number">{criticalAlerts}</span>
                <span className="stat-label">Critiques</span>
              </div>
            </div>
            <div className="alert-stat-item high">
              <Bell size={20} />
              <div>
                <span className="stat-number">{highAlerts}</span>
                <span className="stat-label">Élevées</span>
              </div>
            </div>
            <div className="alert-stat-item total">
              <Activity size={20} />
              <div>
                <span className="stat-number">{totalAlerts}</span>
                <span className="stat-label">Total</span>
              </div>
            </div>
          </div>
        </div>

        {/* Filtres de sévérité */}
        <div className="alerts-filters-bar">
          <button 
            className={`filter-btn ${severityFilter === 'all' ? 'active' : ''}`}
            onClick={() => setSeverityFilter('all')}
          >
            Toutes
          </button>
          <button 
            className={`filter-btn ${severityFilter === 'critical' ? 'active critical' : ''}`}
            onClick={() => setSeverityFilter('critical')}
          >
            🔴 Critiques
          </button>
          <button 
            className={`filter-btn ${severityFilter === 'high' ? 'active high' : ''}`}
            onClick={() => setSeverityFilter('high')}
          >
            🟠 Élevées
          </button>
          <button 
            className={`filter-btn ${severityFilter === 'medium' ? 'active medium' : ''}`}
            onClick={() => setSeverityFilter('medium')}
          >
            🟡 Moyennes
          </button>
          <button 
            className={`filter-btn ${severityFilter === 'low' ? 'active low' : ''}`}
            onClick={() => setSeverityFilter('low')}
          >
            🔵 Infos
          </button>
        </div>

        {alertsLoading ? (
          <div className="loading-state">
            <div className="spinner"></div>
            <p>Chargement des alertes...</p>
          </div>
        ) : alertsData.length === 0 ? (
          <div className="no-alerts-container">
            <div className="no-alerts-header">
              <Bell size={48} style={{ color: '#10b981' }} />
              <h3>Aucune alerte active</h3>
              <p>Tous les médias fonctionnent normalement.</p>
            </div>
          </div>
        ) : (
          <div className="alerts-list">
            {alertsData.map((media) => (
              <div key={media.id} className="media-alerts-section">
                <div className="media-alerts-header">
                  <div className="media-name-badge">
                    <div className="media-icon-badge" style={{ backgroundColor: `${media.color}15` }}>
                      <Newspaper size={24} style={{ color: media.color }} />
                    </div>
                    <h3>{media.name}</h3>
                    <span className="alerts-count">{media.alerts.length} alerte{media.alerts.length > 1 ? 's' : ''}</span>
                  </div>
                </div>

                <div className="alerts-items-row">
                  {media.alerts.map((alert) => {
                    const severityInfo = getSeverityLabel(alert.severite);
                    const AlertIcon = getAlertIcon(alert.type);
                    const alertColor = getAlertColor(alert.severite);
                    
                    return (
                      <div key={alert.id} className={`alert-card severity-${alert.severite}`}>
                        <div className="alert-card-header">
                          <div className="alert-icon" style={{ backgroundColor: `${alertColor}15` }}>
                            <AlertIcon size={24} style={{ color: alertColor }} />
                          </div>
                          <span 
                            className="alert-severity-badge"
                            style={{ 
                              backgroundColor: `${severityInfo.color}15`,
                              color: severityInfo.color 
                            }}
                          >
                            {severityInfo.label}
                          </span>
                        </div>
                        
                        <h4 className="alert-title">{alert.titre}</h4>
                        <p className="alert-description">{alert.message}</p>
                        
                        <div className="alert-footer">
                          <div className="alert-timestamp">
                            <Clock size={14} />
                            <span>{formatTimeAgo(alert.date)}</span>
                          </div>
                          <button 
                            className="resolve-alert-btn"
                            onClick={() => resolveAlertInPage(alert.id)}
                            title="Marquer comme résolu"
                          >
                            <X size={16} />
                            Résoudre
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="dashboard-container">
      <aside className="dashboard-sidebar">
        <div className="sidebar-header">
          <img 
            src="/imageonline-co-pixelated-removebg-preview.png" 
            alt="CSC Logo" 
            className="sidebar-logo-image"
          />
          <h2>MÉDIA-SCAN</h2>
          <p>CSC Dashboard</p>
        </div>

        <nav className="sidebar-nav">
          {adminNavigationItems.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
              onClick={() => {
                setActiveTab(item.id);
                setSelectedMedia(null);
              }}
            >
              <item.icon size={20} />
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          {user?.role === 'admin' && (
            <button className="sidebar-btn export-db" onClick={exportDatabaseToExcel}>
              <FileSpreadsheet size={20} />
              <span>Exporter BD Excel</span>
              <Download size={14} />
            </button>
          )}
          <button className="sidebar-btn">
            <Settings size={20} />
            <span>Paramètres</span>
          </button>
          <button className="sidebar-btn logout" onClick={handleLogout}>
            <LogOut size={20} />
            <span>Déconnexion</span>
          </button>
        </div>
      </aside>

      <main className="dashboard-main">
        {(activeTab === 'general' || activeTab === 'ranking') && (
          <header className="dashboard-header">
            <div className="header-left">
              <h1>Tableau de bord général</h1>
              <p>Vue d'ensemble de la surveillance médiatique</p>
            </div>
            <div className="header-center">
              <div className="time-range-selector">
                <label>Période :</label>
                <div className="time-range-buttons">
                  {timeRanges.map((range) => (
                    <button
                      key={range.value}
                      className={`time-range-btn ${timeRange === range.value ? 'active' : ''}`}
                      onClick={() => setTimeRange(range.value)}
                    >
                      {range.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
            <div className="header-right">
              {/* Bouton Alertes */}
              <button 
                className="alerts-btn"
                onClick={() => setShowAlertsPanel(true)}
                title="Voir les alertes"
              >
                <AlertTriangle size={20} />
                {alertsCount > 0 && (
                  <span className="alerts-badge">{alertsCount}</span>
                )}
              </button>
              
              {/* Bouton Notifications */}
              <NotificationBell onShowReport={(stats) => {
                setShowReportModal(true);
              }} />
            </div>
          </header>
        )}

        {renderContent()}
        
        {/* Panel des alertes */}
        {showAlertsPanel && (
          <AlertsPanel onClose={() => {
            setShowAlertsPanel(false);
            loadAlertsCount(); // Recharger le compteur après fermeture
          }} />
        )}
        
        {/* Modal de rapport de scraping */}
        <ScrapingReportModal 
          isOpen={showReportModal}
          onClose={() => setShowReportModal(false)}
          stats={lastScrapingResult?.stats}
        />
      </main>
    </div>
  );
}

export default Dashboard;
