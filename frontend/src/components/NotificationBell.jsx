import React, { useState, useEffect } from 'react';
import { Bell, X, CheckCircle, AlertCircle, Info, Clock, Trash2 } from 'lucide-react';
import './NotificationBell.css';

const NotificationBell = ({ onShowReport }) => {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  // Charger les notifications depuis l'API
  const loadNotifications = async () => {
    try {
      const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';
      const response = await fetch(`${API_URL}/api/pipeline/notifications`);
      const data = await response.json();
      setNotifications(data.notifications || []);
      setUnreadCount(data.unread_count || 0);
    } catch (error) {
      console.error('Erreur chargement notifications:', error);
    }
  };

  // Polling toutes les 5 secondes pour récupérer les nouvelles notifications
  useEffect(() => {
    loadNotifications();
    const interval = setInterval(loadNotifications, 5000);
    return () => clearInterval(interval);
  }, []);

  // Marquer toutes comme lues
  const markAllAsRead = async () => {
    try {
      const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';
      await fetch(`${API_URL}/api/pipeline/notifications/mark-read`, {
        method: 'POST'
      });
      setUnreadCount(0);
      setNotifications(notifications.map(n => ({ ...n, read: true })));
    } catch (error) {
      console.error('Erreur marquage:', error);
    }
  };

  // Effacer toutes les notifications
  const clearAll = async () => {
    try {
      const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';
      await fetch(`${API_URL}/api/pipeline/notifications/clear`, {
        method: 'POST'
      });
      setNotifications([]);
      setUnreadCount(0);
    } catch (error) {
      console.error('Erreur effacement:', error);
    }
  };

  // Icône selon le type
  const getIcon = (type) => {
    switch (type) {
      case 'success':
        return <CheckCircle size={20} color="#10b981" />;
      case 'error':
        return <AlertCircle size={20} color="#ef4444" />;
      case 'info':
      default:
        return <Info size={20} color="#3b82f6" />;
    }
  };

  // Formater le temps
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000); // secondes

    if (diff < 60) return 'À l\'instant';
    if (diff < 3600) return `Il y a ${Math.floor(diff / 60)} min`;
    if (diff < 86400) return `Il y a ${Math.floor(diff / 3600)} h`;
    return date.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
  };

  // Ouvrir le rapport si c'est une notification de succès
  const handleNotificationClick = (notification) => {
    if (notification.type === 'success' && notification.stats && onShowReport) {
      onShowReport(notification.stats);
    }
  };

  return (
    <div className="notification-bell-container">
      <button 
        className="notification-bell-button"
        onClick={() => {
          setIsOpen(!isOpen);
          if (!isOpen && unreadCount > 0) {
            markAllAsRead();
          }
        }}
      >
        <Bell size={20} />
        {unreadCount > 0 && (
          <span className="notification-badge">{unreadCount > 9 ? '9+' : unreadCount}</span>
        )}
      </button>

      {isOpen && (
        <div className="notification-dropdown">
          <div className="notification-header">
            <h3>Notifications</h3>
            <div className="notification-actions">
              {notifications.length > 0 && (
                <button 
                  className="clear-all-btn"
                  onClick={clearAll}
                  title="Effacer tout"
                >
                  <Trash2 size={16} />
                </button>
              )}
              <button 
                className="close-btn"
                onClick={() => setIsOpen(false)}
              >
                <X size={18} />
              </button>
            </div>
          </div>

          <div className="notification-list">
            {notifications.length === 0 ? (
              <div className="no-notifications">
                <Bell size={40} color="#cbd5e1" />
                <p>Aucune notification</p>
              </div>
            ) : (
              notifications.map((notif, index) => (
                <div 
                  key={index} 
                  className={`notification-item ${!notif.read ? 'unread' : ''} ${notif.type === 'success' ? 'clickable' : ''}`}
                  onClick={() => handleNotificationClick(notif)}
                >
                  <div className="notification-icon">
                    {getIcon(notif.type)}
                  </div>
                  <div className="notification-content">
                    <h4>{notif.title.replace(/[🚀✅❌📢🎉👥📰]/g, '').trim()}</h4>
                    <p>{notif.message.replace(/[🚀✅❌📢🎉👥📰]/g, '').trim()}</p>
                    
                    {/* Afficher les stats détaillées si disponibles */}
                    {notif.stats && (
                      <div className="notification-stats-simple">
                        <span className="stats-info">
                          Total: <strong>{notif.stats.total_scraped || 0}</strong> scrapés, 
                          <strong className="inserted"> {notif.stats.total_inserted || 0}</strong> insérés
                          {notif.stats.total_skipped > 0 && (
                            <>, <strong className="skipped">{notif.stats.total_skipped}</strong> ignorés</>
                          )}
                        </span>
                      </div>
                    )}
                    
                    <div className="notification-time">
                      <Clock size={12} />
                      <span>{formatTime(notif.timestamp)}</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationBell;
