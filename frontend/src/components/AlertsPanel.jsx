import React, { useState, useEffect } from 'react';
import { 
  AlertTriangle, 
  AlertCircle, 
  Info, 
  CheckCircle, 
  X,
  Filter,
  TrendingUp,
  TrendingDown,
  Activity,
  Clock,
  Bell,
  Eye
} from 'lucide-react';
import './AlertsPanel.css';

const AlertsPanel = ({ onClose }) => {
  const [alerts, setAlerts] = useState([]);
  const [alertStats, setAlertStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState('all');
  const [expandedAlert, setExpandedAlert] = useState(null);

  useEffect(() => {
    loadAlerts();
    loadAlertStats();
    
    // Rafraîchir toutes les 30 secondes
    const interval = setInterval(() => {
      loadAlerts();
      loadAlertStats();
    }, 30000);
    
    return () => clearInterval(interval);
  }, [severityFilter]);

  const loadAlerts = async () => {
    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';
      const params = new URLSearchParams({
        is_resolved: 'false',
        limit: '50'
      });
      
      if (severityFilter !== 'all') {
        params.append('severite', severityFilter);
      }
      
      const response = await fetch(`${API_URL}/api/dashboard/alerts?${params}`);
      const data = await response.json();
      setAlerts(data || []);
    } catch (error) {
      console.error('Erreur chargement alertes:', error);
      setAlerts([]);
    } finally {
      setLoading(false);
    }
  };

  const loadAlertStats = async () => {
    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';
      const response = await fetch(`${API_URL}/api/dashboard/alerts/stats`);
      const data = await response.json();
      setAlertStats(data);
    } catch (error) {
      console.error('Erreur chargement stats alertes:', error);
    }
  };

  const resolveAlert = async (alertId) => {
    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';
      const response = await fetch(`${API_URL}/api/dashboard/alerts/${alertId}/resolve`, {
        method: 'PUT'
      });
      
      if (response.ok) {
        // Retirer l'alerte de la liste
        setAlerts(alerts.filter(a => a.id !== alertId));
        // Recharger les stats
        loadAlertStats();
      }
    } catch (error) {
      console.error('Erreur résolution alerte:', error);
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'critical':
        return <AlertTriangle className="severity-icon critical" />;
      case 'high':
        return <AlertCircle className="severity-icon high" />;
      case 'medium':
        return <Info className="severity-icon medium" />;
      case 'low':
        return <CheckCircle className="severity-icon low" />;
      default:
        return <Info className="severity-icon" />;
    }
  };

  const getSeverityLabel = (severity) => {
    const labels = {
      critical: 'CRITIQUE',
      high: 'IMPORTANT',
      medium: 'MOYEN',
      low: 'INFO'
    };
    return labels[severity] || severity;
  };

  const getAlertTypeIcon = (type) => {
    const icons = {
      pic_engagement: <TrendingUp size={16} />,
      chute_engagement: <TrendingDown size={16} />,
      inactivite: <Clock size={16} />,
      explosion_publications: <Activity size={16} />,
      baisse_influence: <TrendingDown size={16} />,
      regularite_faible: <Clock size={16} />,
      ratio_engagement_faible: <Eye size={16} />,
      ratio_engagement_eleve: <Bell size={16} />,
      nouveau_media_actif: <Activity size={16} />,
      thematique_dominante: <Filter size={16} />,
      record_engagement: <TrendingUp size={16} />,
      commentaires_eleves: <Activity size={16} />
    };
    return icons[type] || <Info size={16} />;
  };

  const formatDate = (dateString) => {
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

  const groupedAlerts = alerts.reduce((acc, alert) => {
    const severity = alert.severite;
    if (!acc[severity]) {
      acc[severity] = [];
    }
    acc[severity].push(alert);
    return acc;
  }, {});

  const severityOrder = ['critical', 'high', 'medium', 'low'];

  return (
    <div className="alerts-panel-overlay" onClick={onClose}>
      <div className="alerts-panel" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="alerts-header">
          <div className="alerts-title">
            <Bell size={24} />
            <h2>Alertes Système</h2>
            {alertStats && (
              <span className="alerts-count">
                {alertStats.total_active}
              </span>
            )}
          </div>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {/* Stats Summary */}
        {alertStats && (
          <div className="alerts-stats">
            <div className="stat-card critical">
              <AlertTriangle size={20} />
              <div className="stat-info">
                <span className="stat-value">{alertStats.by_severity.critical}</span>
                <span className="stat-label">Critiques</span>
              </div>
            </div>
            <div className="stat-card high">
              <AlertCircle size={20} />
              <div className="stat-info">
                <span className="stat-value">{alertStats.by_severity.high}</span>
                <span className="stat-label">Importants</span>
              </div>
            </div>
            <div className="stat-card medium">
              <Info size={20} />
              <div className="stat-info">
                <span className="stat-value">{alertStats.by_severity.medium}</span>
                <span className="stat-label">Moyens</span>
              </div>
            </div>
            <div className="stat-card low">
              <CheckCircle size={20} />
              <div className="stat-info">
                <span className="stat-value">{alertStats.by_severity.low}</span>
                <span className="stat-label">Infos</span>
              </div>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="alerts-filters">
          <button 
            className={`filter-btn ${severityFilter === 'all' ? 'active' : ''}`}
            onClick={() => setSeverityFilter('all')}
          >
            Toutes
          </button>
          <button 
            className={`filter-btn ${severityFilter === 'critical' ? 'active' : ''}`}
            onClick={() => setSeverityFilter('critical')}
          >
            🔴 Critiques
          </button>
          <button 
            className={`filter-btn ${severityFilter === 'high' ? 'active' : ''}`}
            onClick={() => setSeverityFilter('high')}
          >
            🟠 Importants
          </button>
          <button 
            className={`filter-btn ${severityFilter === 'medium' ? 'active' : ''}`}
            onClick={() => setSeverityFilter('medium')}
          >
            🟡 Moyens
          </button>
          <button 
            className={`filter-btn ${severityFilter === 'low' ? 'active' : ''}`}
            onClick={() => setSeverityFilter('low')}
          >
            🔵 Infos
          </button>
        </div>

        {/* Alerts List */}
        <div className="alerts-list">
          {loading ? (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>Chargement des alertes...</p>
            </div>
          ) : alerts.length === 0 ? (
            <div className="empty-state">
              <CheckCircle size={48} />
              <p>Aucune alerte active</p>
              <span>Tout va bien ! 🎉</span>
            </div>
          ) : (
            severityOrder.map(severity => 
              groupedAlerts[severity] && groupedAlerts[severity].length > 0 && (
                <div key={severity} className="alerts-group">
                  <div className="group-header">
                    {getSeverityIcon(severity)}
                    <span>{getSeverityLabel(severity)}</span>
                    <span className="group-count">({groupedAlerts[severity].length})</span>
                  </div>
                  {groupedAlerts[severity].map(alert => (
                    <div 
                      key={alert.id} 
                      className={`alert-item ${alert.severite} ${expandedAlert === alert.id ? 'expanded' : ''}`}
                    >
                      <div className="alert-content">
                        <div className="alert-icon-type">
                          {getAlertTypeIcon(alert.type)}
                        </div>
                        <div className="alert-body">
                          <div className="alert-header-line">
                            <h4 className="alert-title">{alert.titre}</h4>
                            <span className="alert-time">{formatDate(alert.date)}</span>
                          </div>
                          {alert.media && (
                            <div className="alert-media">
                              <span 
                                className="media-badge" 
                                style={{ 
                                  backgroundColor: alert.media.couleur + '20',
                                  color: alert.media.couleur,
                                  borderColor: alert.media.couleur
                                }}
                              >
                                {alert.media.name}
                              </span>
                            </div>
                          )}
                          <p className="alert-message">{alert.message}</p>
                        </div>
                      </div>
                      <div className="alert-actions">
                        <button 
                          className="resolve-btn"
                          onClick={() => resolveAlert(alert.id)}
                          title="Marquer comme résolu"
                        >
                          <CheckCircle size={16} />
                          Résoudre
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )
            )
          )}
        </div>
      </div>
    </div>
  );
};

export default AlertsPanel;
