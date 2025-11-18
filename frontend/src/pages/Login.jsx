import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, Lock, Mail, Eye, EyeOff, ArrowLeft, AlertCircle } from 'lucide-react';
import { authAPI } from '../services/api';
import './Login.css';

function Login() {
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Appel à l'API de connexion
      const response = await authAPI.login(formData.email, formData.password);
      
      console.log('Connexion réussie:', response.user);
      
      // Rediriger vers le dashboard après connexion
      navigate('/dashboard');
    } catch (err) {
      setError(err.message || 'Erreur de connexion. Vérifiez vos identifiants.');
      console.error('Erreur de connexion:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-wrapper">
        <div className="login-right">
          <button className="back-button-right" onClick={() => navigate('/')}>
            <ArrowLeft size={20} />
            Retour
          </button>

          <div className="welcome-panel">
            <div className="login-branding">
              <img 
                src="/imageonline-co-pixelated-removebg-preview.png" 
                alt="CSC Logo" 
                className="login-logo-image"
              />
              <h1>MÉDIA-SCAN</h1>
              <p className="login-subtitle">Conseil Supérieur de la Communication</p>
            </div>

            <div className="security-messages">
              <div className="security-item">
                <Lock size={24} />
                <p>Connexion sécurisée SSL/TLS</p>
              </div>
              <div className="security-item">
                <Activity size={24} />
                <p>Données protégées et cryptées</p>
              </div>
              <div className="security-item">
                <Mail size={24} />
                <p>Authentification à deux facteurs</p>
              </div>
            </div>

            <div className="copyright-right">
              © 2025 CSC - Burkina Faso. Tous droits réservés.
            </div>
          </div>
        </div>

        <div className="login-left">
          <div className="login-card-center">
            <div className="login-form-section">
              <h2>Connexion</h2>
              <p className="form-description">Accédez à votre espace de surveillance médiatique</p>

              {error && (
                <div className="error-message">
                  <AlertCircle size={20} />
                  <span>{error}</span>
                </div>
              )}

              <form className="login-form" onSubmit={handleSubmit}>
                <div className="form-group">
                  <label>Adresse email</label>
                  <div className="input-wrapper">
                    <Mail className="input-icon" size={20} />
                    <input
                      type="email"
                      placeholder="votre.email@csc.bf"
                      value={formData.email}
                      onChange={(e) => setFormData({...formData, email: e.target.value})}
                      required
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label>Mot de passe</label>
                  <div className="input-wrapper">
                    <Lock className="input-icon" size={20} />
                    <input
                      type={showPassword ? 'text' : 'password'}
                      placeholder="••••••••"
                      value={formData.password}
                      onChange={(e) => setFormData({...formData, password: e.target.value})}
                      required
                    />
                    <button
                      type="button"
                      className="toggle-password"
                      onClick={() => setShowPassword(!showPassword)}
                    >
                      {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                    </button>
                  </div>
                </div>

                <div className="form-options">
                  <label className="checkbox-label">
                    <input type="checkbox" />
                    <span>Se souvenir de moi</span>
                  </label>
                  <a href="#" className="forgot-link">Mot de passe oublié ?</a>
                </div>

                <button type="submit" className="login-button" disabled={loading}>
                  {loading ? 'Connexion en cours...' : 'Se connecter'}
                </button>

                <div className="login-footer">
                  <p className="footer-text">ou</p>
                  <p className="no-account">Vous n'avez pas de compte ?</p>
                  <a href="#" className="contact-admin">Contactez l'administrateur</a>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Login;
