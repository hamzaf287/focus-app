import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useEffect, useState } from 'react';
import Toast from './Toast';

const ProtectedRoute = ({ children, allowedRoles = [] }) => {
  const { user, loading } = useAuth();
  const location = useLocation();
  const [showAccessDenied, setShowAccessDenied] = useState(false);
  const [redirectTo, setRedirectTo] = useState(null);

  useEffect(() => {
    // Check if user is trying to access wrong role's page
    if (!loading && user && allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
      setShowAccessDenied(true);

      // Determine redirect destination
      let destination = '/login';
      if (user.role === 'student') destination = '/student';
      else if (user.role === 'teacher') destination = '/teacher';
      else if (user.role === 'admin') destination = '/admin';

      // Delay redirect to show toast
      setTimeout(() => {
        setRedirectTo(destination);
      }, 1500);
    }
  }, [loading, user, allowedRoles]);

  if (loading) {
    return (
      <div className="loading-screen">
        <i className="ri-loader-4-line ri-spin"></i>
        <p>Loading...</p>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Show access denied toast before redirecting
  if (showAccessDenied) {
    if (redirectTo) {
      return <Navigate to={redirectTo} replace />;
    }

    return (
      <div className="loading-screen">
        <Toast
          message="You don't have access to that page. Redirecting to your dashboard..."
          type="warning"
          onClose={() => {}}
        />
        <i className="ri-loader-4-line ri-spin"></i>
        <p>Redirecting...</p>
      </div>
    );
  }

  if (allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
    // This triggers the useEffect above
    return null;
  }

  return children;
};

export default ProtectedRoute;
