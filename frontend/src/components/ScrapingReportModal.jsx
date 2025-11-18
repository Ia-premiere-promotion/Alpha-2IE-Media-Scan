import React from 'react';
import { X, CheckCircle, AlertCircle, Newspaper, Database, Clock, TrendingUp } from 'lucide-react';
import './ScrapingReportModal.css';

const ScrapingReportModal = ({ isOpen, onClose, stats }) => {
  if (!isOpen || !stats) return null;

  const successRate = stats.total_scraped > 0 
    ? ((stats.total_inserted / stats.total_scraped) * 100).toFixed(1)
    : 0;

  const formatDuration = (seconds) => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}m ${secs}s`;
  };

  return (
    <div className="scraping-modal-overlay" onClick={onClose}>
      <div className="scraping-modal" onClick={(e) => e.stopPropagation()}>
        <div className="scraping-modal-header">
          <div className="header-content">
            <CheckCircle size={32} color="#10b981" />
            <div>
              <h2>Scraping terminé avec succès</h2>
              <p>Rapport détaillé de l'exécution</p>
            </div>
          </div>
          <button className="close-modal-btn" onClick={onClose}>
            <X size={24} />
          </button>
        </div>

        <div className="scraping-modal-body">
          {/* Stats principales */}
          <div className="stats-grid-modal">
            <div className="stat-card-modal">
              <div className="stat-icon-modal" style={{ backgroundColor: '#eff6ff' }}>
                <Newspaper size={24} color="#3b82f6" />
              </div>
              <div className="stat-content-modal">
                <p className="stat-label-modal">Articles scrapés</p>
                <h3 className="stat-value-modal">{stats.total_scraped || 0}</h3>
              </div>
            </div>

            <div className="stat-card-modal">
              <div className="stat-icon-modal" style={{ backgroundColor: '#f0fdf4' }}>
                <Database size={24} color="#10b981" />
              </div>
              <div className="stat-content-modal">
                <p className="stat-label-modal">Insérés dans la BD</p>
                <h3 className="stat-value-modal success-text">{stats.total_inserted || 0}</h3>
              </div>
            </div>

            <div className="stat-card-modal">
              <div className="stat-icon-modal" style={{ backgroundColor: '#fef3c7' }}>
                <AlertCircle size={24} color="#f59e0b" />
              </div>
              <div className="stat-content-modal">
                <p className="stat-label-modal">Doublons ignorés</p>
                <h3 className="stat-value-modal">{stats.total_skipped || 0}</h3>
              </div>
            </div>

            <div className="stat-card-modal">
              <div className="stat-icon-modal" style={{ backgroundColor: '#fef2f2' }}>
                <AlertCircle size={24} color="#ef4444" />
              </div>
              <div className="stat-content-modal">
                <p className="stat-label-modal">Erreurs</p>
                <h3 className="stat-value-modal error-text">{stats.total_errors || 0}</h3>
              </div>
            </div>
          </div>

          {/* Indicateurs de performance */}
          <div className="performance-section">
            <h3>Performance</h3>
            <div className="performance-items">
              <div className="performance-item">
                <Clock size={20} color="#64748b" />
                <div>
                  <p className="performance-label">Durée totale</p>
                  <p className="performance-value">{formatDuration(stats.duration || 0)}</p>
                </div>
              </div>

              <div className="performance-item">
                <TrendingUp size={20} color="#10b981" />
                <div>
                  <p className="performance-label">Taux de réussite</p>
                  <p className="performance-value success-text">{successRate}%</p>
                </div>
              </div>
            </div>
          </div>

          {/* Détails par étape */}
          {stats.total_cleaned !== undefined && (
            <div className="details-section">
              <h3>Détails du pipeline</h3>
              <div className="pipeline-steps">
                <div className="pipeline-step">
                  <div className="step-dot completed"></div>
                  <div className="step-content">
                    <p className="step-title">Scraping</p>
                    <p className="step-desc">{stats.total_scraped} articles collectés</p>
                  </div>
                </div>

                <div className="pipeline-step">
                  <div className="step-dot completed"></div>
                  <div className="step-content">
                    <p className="step-title">Nettoyage</p>
                    <p className="step-desc">{stats.total_cleaned} articles nettoyés</p>
                  </div>
                </div>

                <div className="pipeline-step">
                  <div className="step-dot completed"></div>
                  <div className="step-content">
                    <p className="step-title">Insertion BD</p>
                    <p className="step-desc">{stats.total_inserted} articles insérés</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="scraping-modal-footer">
          <button className="modal-btn primary" onClick={onClose}>
            Fermer
          </button>
        </div>
      </div>
    </div>
  );
};

export default ScrapingReportModal;
