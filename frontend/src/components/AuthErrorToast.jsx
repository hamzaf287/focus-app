import { useAuth } from '../context/AuthContext';
import Toast from './Toast';

const AuthErrorToast = () => {
  const { authError, clearAuthError } = useAuth();

  if (!authError) return null;

  return (
    <Toast
      message={authError}
      type="error"
      onClose={clearAuthError}
    />
  );
};

export default AuthErrorToast;
