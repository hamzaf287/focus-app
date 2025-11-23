import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

// Prevents authenticated users from accessing login/register pages
const PublicRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="loading-screen">
        <i className="ri-loader-4-line ri-spin"></i>
        <p>Loading...</p>
      </div>
    );
  }

  // If already authenticated, redirect to appropriate dashboard
  if (user) {
    if (user.role === 'student') return <Navigate to="/student" replace />;
    if (user.role === 'teacher') return <Navigate to="/teacher" replace />;
    if (user.role === 'admin') return <Navigate to="/admin" replace />;
  }

  return children;
};

export default PublicRoute;
