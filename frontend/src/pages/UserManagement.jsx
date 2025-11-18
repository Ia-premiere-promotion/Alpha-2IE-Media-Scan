import React, { useState, useEffect } from 'react';
import { 
  Users, 
  UserPlus, 
  Mail, 
  Phone, 
  Shield, 
  X,
  Eye,
  EyeOff,
  CheckCircle,
  XCircle,
  Search,
  Lock,
  Unlock,
  Trash2,
  FileSpreadsheet,
  Download
} from 'lucide-react';
import { usersAPI } from '../services/api';
import './UserManagement.css';

function UserManagement() {
  const [users, setUsers] = useState([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showSuccessMessage, setShowSuccessMessage] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [userToDelete, setUserToDelete] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [newUser, setNewUser] = useState({
    email: '',
    nom: '',
    prenom: '',
    role: 'user',
    telephone: '',
    password: '12345678'
  });

  // Charger les utilisateurs au montage du composant
  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const response = await usersAPI.getAll();
      setUsers(response.users);
    } catch (err) {
      setError(err.message || 'Erreur lors du chargement des utilisateurs');
      console.error('Erreur:', err);
    } finally {
      setLoading(false);
    }
  };

  const showSuccess = (message) => {
    setSuccessMessage(message);
    setShowSuccessMessage(true);
    setTimeout(() => {
      setShowSuccessMessage(false);
    }, 2000);
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    
    try {
      setLoading(true);
      setError('');
      
      const response = await usersAPI.create(newUser);
      
      // Recharger la liste des utilisateurs
      await loadUsers();
      
      setShowCreateModal(false);
      showSuccess('Utilisateur créé avec succès');
      
      // Réinitialiser le formulaire
      setNewUser({
        email: '',
        nom: '',
        prenom: '',
        role: 'user',
        telephone: '',
        password: '12345678'
      });
    } catch (err) {
      setError(err.message || 'Erreur lors de la création de l\'utilisateur');
      console.error('Erreur:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleUserStatus = async (userId) => {
    try {
      const user = users.find(u => u.id === userId);
      await usersAPI.toggleStatus(userId, !user.actif);
      
      // Mettre à jour localement
      setUsers(users.map(u => 
        u.id === userId ? { ...u, actif: !u.actif } : u
      ));
      
      showSuccess(user.actif ? 'Utilisateur bloqué' : 'Utilisateur débloqué');
    } catch (err) {
      setError(err.message || 'Erreur lors de la modification du statut');
      console.error('Erreur:', err);
    }
  };

  const handleDeleteUser = (userId) => {
    const user = users.find(u => u.id === userId);
    setUserToDelete(user);
    setShowDeleteModal(true);
  };

  const confirmDelete = async () => {
    if (userToDelete) {
      try {
        setLoading(true);
        await usersAPI.delete(userToDelete.id);
        
        // Mettre à jour localement
        setUsers(users.filter(user => user.id !== userToDelete.id));
        
        setShowDeleteModal(false);
        setUserToDelete(null);
        showSuccess('Utilisateur supprimé avec succès');
      } catch (err) {
        setError(err.message || 'Erreur lors de la suppression');
        console.error('Erreur:', err);
        setShowDeleteModal(false);
      } finally {
        setLoading(false);
      }
    }
  };

  const cancelDelete = () => {
    setShowDeleteModal(false);
    setUserToDelete(null);
  };

  // Export Excel de toute la base de données
  const exportDatabaseToExcel = async () => {
    try {
      setLoading(true);
      const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';
      const token = localStorage.getItem('access_token');
      
      const response = await fetch(`${API_URL}/api/export/database`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Erreur lors de l\'export');
      }

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

      setSuccessMessage('Base de données exportée avec succès !');
      setShowSuccessMessage(true);
      setTimeout(() => setShowSuccessMessage(false), 3000);
      
    } catch (err) {
      setError(err.message || 'Erreur lors de l\'export');
      console.error('Erreur export:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredUsers = users.filter(user => 
    user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.nom.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.prenom.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const stats = {
    total: users.length,
    admins: users.filter(u => u.role === 'admin').length,
    users: users.filter(u => u.role === 'user').length,
    active: users.filter(u => u.actif).length,
    inactive: users.filter(u => !u.actif).length
  };

  return (
    <div className="user-management">
      <div className="user-management-header">
        <div>
          <h1>Gestion des Utilisateurs</h1>
          <p>Gérer les comptes et les accès au système</p>
        </div>
        <button className="btn-create-user" onClick={() => setShowCreateModal(true)}>
          <UserPlus size={20} />
          Nouvel Utilisateur
        </button>
      </div>

      {/* Statistiques */}
      <div className="user-stats-grid">
        <div className="user-stat-card">
          <Users size={24} className="stat-icon" />
          <div className="stat-content">
            <div className="stat-value">{stats.total}</div>
            <div className="stat-label">Total Utilisateurs</div>
          </div>
        </div>
        <div className="user-stat-card">
          <Shield size={24} className="stat-icon admin" />
          <div className="stat-content">
            <div className="stat-value">{stats.admins}</div>
            <div className="stat-label">Administrateurs</div>
          </div>
        </div>
        <div className="user-stat-card">
          <Users size={24} className="stat-icon user" />
          <div className="stat-content">
            <div className="stat-value">{stats.users}</div>
            <div className="stat-label">Utilisateurs</div>
          </div>
        </div>
        <div className="user-stat-card">
          <CheckCircle size={24} className="stat-icon active" />
          <div className="stat-content">
            <div className="stat-value">{stats.active}</div>
            <div className="stat-label">Actifs</div>
          </div>
        </div>
        <div className="user-stat-card">
          <XCircle size={24} className="stat-icon inactive" />
          <div className="stat-content">
            <div className="stat-value">{stats.inactive}</div>
            <div className="stat-label">Inactifs</div>
          </div>
        </div>
      </div>

      {/* Barre de recherche */}
      <div className="user-search-bar">
        <Search size={20} />
        <input
          type="text"
          placeholder="Rechercher un utilisateur..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      {/* Liste des utilisateurs */}
      <div className="users-table">
        <table>
          <thead>
            <tr>
              <th>Utilisateur</th>
              <th>Email</th>
              <th>Téléphone</th>
              <th>Rôle</th>
              <th>Statut</th>
              <th>Date création</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredUsers.map(user => (
              <tr key={user.id}>
                <td>
                  <div className="user-info-cell">
                    <div className="user-avatar">
                      {user.prenom[0]}{user.nom[0]}
                    </div>
                    <div>
                      <div className="user-name">{user.prenom} {user.nom}</div>
                    </div>
                  </div>
                </td>
                <td>{user.email}</td>
                <td>{user.telephone}</td>
                <td>
                  <span className={`role-badge ${user.role}`}>
                    {user.role === 'admin' ? 'Administrateur' : 'Utilisateur'}
                  </span>
                </td>
                <td>
                  <span className={`status-badge ${user.actif ? 'active' : 'inactive'}`}>
                    {user.actif ? 'Actif' : 'Inactif'}
                  </span>
                </td>
                <td>{new Date(user.created_at).toLocaleDateString('fr-FR')}</td>
                <td>
                  <div className="action-buttons">
                    <button 
                      className={`action-btn ${user.actif ? 'block' : 'unblock'}`}
                      onClick={() => handleToggleUserStatus(user.id)}
                      title={user.actif ? 'Bloquer le compte' : 'Débloquer le compte'}
                    >
                      {user.actif ? <Lock size={18} /> : <Unlock size={18} />}
                    </button>
                    <button 
                      className="action-btn delete"
                      onClick={() => handleDeleteUser(user.id)}
                      title="Supprimer l'utilisateur"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Modal de création d'utilisateur */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Créer un Nouvel Utilisateur</h2>
              <button className="modal-close" onClick={() => setShowCreateModal(false)}>
                <X size={24} />
              </button>
            </div>

            <form onSubmit={handleCreateUser} className="user-form">
              <div className="form-row">
                <div className="form-group">
                  <label>Prénom</label>
                  <input
                    type="text"
                    required
                    value={newUser.prenom}
                    onChange={(e) => setNewUser({...newUser, prenom: e.target.value})}
                    placeholder="Prénom"
                  />
                </div>
                <div className="form-group">
                  <label>Nom</label>
                  <input
                    type="text"
                    required
                    value={newUser.nom}
                    onChange={(e) => setNewUser({...newUser, nom: e.target.value})}
                    placeholder="Nom"
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Email</label>
                <div className="input-with-icon">
                  <Mail size={20} />
                  <input
                    type="email"
                    required
                    value={newUser.email}
                    onChange={(e) => setNewUser({...newUser, email: e.target.value})}
                    placeholder="exemple@csc.bf"
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Téléphone</label>
                <div className="input-with-icon">
                  <Phone size={20} />
                  <input
                    type="tel"
                    value={newUser.telephone}
                    onChange={(e) => setNewUser({...newUser, telephone: e.target.value})}
                    placeholder="+226 70 00 00 00"
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Rôle</label>
                <select
                  value={newUser.role}
                  onChange={(e) => setNewUser({...newUser, role: e.target.value})}
                >
                  <option value="user">Utilisateur</option>
                  <option value="admin">Administrateur</option>
                </select>
              </div>

              <div className="form-group">
                <label>Mot de passe par défaut</label>
                <div className="password-info">
                  <input
                    type="text"
                    value={newUser.password}
                    readOnly
                    className="password-display"
                  />
                  <span className="password-note">
                    L'utilisateur devra changer ce mot de passe à la première connexion
                  </span>
                </div>
              </div>

              <div className="modal-actions">
                <button type="button" className="btn-cancel" onClick={() => setShowCreateModal(false)}>
                  Annuler
                </button>
                <button type="submit" className="btn-submit">
                  <UserPlus size={20} />
                  Créer l'Utilisateur
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal de confirmation de suppression */}
      {showDeleteModal && userToDelete && (
        <div className="modal-overlay" onClick={cancelDelete}>
          <div className="modal-content simple-delete-modal" onClick={(e) => e.stopPropagation()}>
            <div className="simple-modal-body">
              <p className="simple-delete-question">Êtes-vous sûr ?</p>
            </div>

            <div className="simple-modal-actions">
              <button type="button" className="btn-simple-no" onClick={cancelDelete}>
                Non
              </button>
              <button type="button" className="btn-simple-yes" onClick={confirmDelete}>
                Oui
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Message de succès */}
      {showSuccessMessage && (
        <div className="success-toast">
          <CheckCircle size={24} />
          <span>{successMessage}</span>
        </div>
      )}

      {/* Message d'erreur */}
      {error && (
        <div className="error-toast" onClick={() => setError('')}>
          <XCircle size={24} />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}

export default UserManagement;
