import { createContext, useState, useContext, useEffect, useCallback } from 'react';
import { authAPI, setupInterceptors } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState(null);

  // Handle 401 - session expired
  const handleUnauthorized = useCallback(() => {
    setUser(null);
    setAuthError('Your session has expired. Please log in again.');
  }, []);

  // Handle 403 - forbidden
  const handleForbidden = useCallback((message) => {
    setAuthError(message);
    // Clear error after 5 seconds
    setTimeout(() => setAuthError(null), 5000);
  }, []);

  // Setup interceptors on mount
  useEffect(() => {
    setupInterceptors({
      onUnauthorized: handleUnauthorized,
      onForbidden: handleForbidden,
    });
  }, [handleUnauthorized, handleForbidden]);

  // Check if user is logged in on app load
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const response = await authAPI.getMe();
      setUser(response.data.user);
    } catch (error) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    const response = await authAPI.login(email, password);
    if (response.data.user) {
      setUser(response.data.user);
    }
    return response.data;
  };

  const register = async (name, email, password, role) => {
    const response = await authAPI.register(name, email, password, role);
    return response.data;
  };

  const logout = async () => {
    try {
      await authAPI.logout();
    } finally {
      setUser(null);
    }
  };

  const clearAuthError = useCallback(() => {
    setAuthError(null);
  }, []);

  const value = {
    user,
    loading,
    authError,
    login,
    register,
    logout,
    checkAuth,
    clearAuthError,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
