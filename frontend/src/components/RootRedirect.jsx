import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const RootRedirect = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="loading-screen">
        <i className="ri-loader-4-line ri-spin"></i>
        <p>Loading...</p>
      </div>
    );
  }

  // If authenticated, redirect to appropriate dashboard
  if (user) {
    if (user.role === 'student') return <Navigate to="/student" replace />;
    if (user.role === 'teacher') return <Navigate to="/teacher" replace />;
    if (user.role === 'admin') return <Navigate to="/admin" replace />;
  }

  // If not authenticated, go to login
  return <Navigate to="/login" replace />;
};

export default RootRedirect;
