import { Navigate } from 'react-router-dom';
import { authAPI } from '../services/api';

function ProtectedRoute({ children, requireAdmin = false }) {
  const isAuthenticated = authAPI.isAuthenticated();
  const isAdmin = authAPI.isAdmin();

  if (!isAuthenticated) {
    // Rediriger vers login si pas authentifié
    return <Navigate to="/login" replace />;
  }

  if (requireAdmin && !isAdmin) {
    // Rediriger vers dashboard si pas admin
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}

export default ProtectedRoute;
