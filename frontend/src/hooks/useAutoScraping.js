import { useState, useEffect, useCallback } from 'react';
import { toast } from 'react-hot-toast';

/**
 * Hook pour gérer le scraping automatique
 * - Lance le scraping toutes les X minutes
 * - Surveille l'état du scraping
 * - Affiche un pop-up automatique quand le scraping se termine
 */
const useAutoScraping = (intervalMinutes = 15) => {
  const [isScrapingRunning, setIsScrapingRunning] = useState(false);
  const [lastScrapingResult, setLastScrapingResult] = useState(null);
  const [showReportModal, setShowReportModal] = useState(false);
  
  // Initialiser le timer depuis localStorage ou créer un nouveau
  const initializeTimer = () => {
    const savedNextScraping = localStorage.getItem('nextScrapingTime');
    if (savedNextScraping) {
      const nextTime = parseInt(savedNextScraping);
      const now = Date.now();
      const remainingSeconds = Math.max(0, Math.floor((nextTime - now) / 1000));
      return remainingSeconds;
    }
    // Nouveau timer
    const nextTime = Date.now() + (intervalMinutes * 60 * 1000);
    localStorage.setItem('nextScrapingTime', nextTime.toString());
    return intervalMinutes * 60;
  };
  
  const [nextScrapingIn, setNextScrapingIn] = useState(initializeTimer());

  // Lancer un scraping
  const startScraping = useCallback(async (maxArticles = 20) => {
    try {
      console.log('🚀 Démarrage du scraping...');
      
      // Afficher pop-up de démarrage
      toast.loading('Scraping démarré...', {
        id: 'scraping-start',
        duration: 3000,
        icon: '🚀',
        style: {
          background: '#3B82F6',
          color: '#fff',
          fontWeight: 'bold'
        }
      });
      
      const response = await fetch('http://localhost:5000/api/pipeline/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ max_articles: maxArticles })
      });

      const data = await response.json();
      
      if (data.success) {
        console.log('✅ Scraping démarré:', data.message);
        setIsScrapingRunning(true);
        return true;
      } else {
        console.warn('⚠️ Impossible de démarrer:', data.message);
        toast.dismiss('scraping-start');
        toast.error(data.message, {
          duration: 4000,
          icon: '⚠️'
        });
        return false;
      }
    } catch (error) {
      console.error('❌ Erreur démarrage scraping:', error);
      toast.dismiss('scraping-start');
      toast.error('Erreur de connexion au serveur', {
        duration: 4000,
        icon: '❌'
      });
      return false;
    }
  }, []);

  // Vérifier l'état du scraping
  const checkScrapingStatus = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:5000/api/pipeline/status');
      const data = await response.json();

      const wasRunning = isScrapingRunning;
      setIsScrapingRunning(data.is_running);

      // Si le scraping vient de se terminer
      if (wasRunning && !data.is_running && data.last_result) {
        toast.dismiss('scraping-start');
        
        if (data.last_result.success) {
          // Pop-up de succès
          const stats = data.last_result.stats;
          toast.success(
            `Scraping terminé !\n${stats.total_inserted} nouveaux articles insérés`,
            {
              duration: 5000,
              icon: '✅',
              style: {
                background: '#10B981',
                color: '#fff',
                fontWeight: 'bold'
              }
            }
          );
        } else {
          // Pop-up d'erreur
          toast.error('Scraping échoué', {
            duration: 5000,
            icon: '❌',
            style: {
              background: '#EF4444',
              color: '#fff'
            }
          });
        }
      }

      // Si le scraping vient de se terminer et qu'on a un résultat
      if (!data.is_running && data.last_result && 
          data.last_result.timestamp !== lastScrapingResult?.timestamp) {
        
        setLastScrapingResult(data.last_result);
        
        // Afficher automatiquement le rapport si succès
        if (data.last_result.success) {
          setShowReportModal(true);
        }
      }

      return data;
    } catch (error) {
      console.error('❌ Erreur vérification status:', error);
      return null;
    }
  }, [lastScrapingResult, isScrapingRunning]);

  // Polling de l'état toutes les 5 secondes
  useEffect(() => {
    const interval = setInterval(checkScrapingStatus, 5000);
    return () => clearInterval(interval);
  }, [checkScrapingStatus]);

  // Timer pour le prochain scraping automatique
  useEffect(() => {
    const countdown = setInterval(() => {
      setNextScrapingIn((prev) => {
        if (prev <= 1 && !isScrapingRunning) {
          // Temps écoulé, lancer le scraping
          startScraping(20);
          
          // Définir le prochain scraping
          const nextTime = Date.now() + (intervalMinutes * 60 * 1000);
          localStorage.setItem('nextScrapingTime', nextTime.toString());
          return intervalMinutes * 60; // Réinitialiser
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(countdown);
  }, [intervalMinutes, isScrapingRunning, startScraping]);

  // Formater le temps restant
  const formatTimeRemaining = () => {
    const minutes = Math.floor(nextScrapingIn / 60);
    const seconds = nextScrapingIn % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  return {
    isScrapingRunning,
    lastScrapingResult,
    showReportModal,
    setShowReportModal,
    nextScrapingIn,
    formatTimeRemaining,
    startScraping,
    checkScrapingStatus
  };
};

export default useAutoScraping;
