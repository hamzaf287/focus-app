import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import '../styles/Auth.css';

const PendingApproval = () => {
  const { user, logout, checkAuth } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    // If user is approved, redirect to teacher dashboard
    if (user?.status === 'active' || user?.status === 'approved') {
      navigate('/teacher');
    }
  }, [user, navigate]);

  const handleCheckStatus = async () => {
    await checkAuth();
    // useEffect will handle redirect if approved
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="auth-page">
      <div className="auth-container pending-container">
        <div className="pending-icon">
          <i className="ri-time-line"></i>
        </div>

        <div className="auth-header">
          <h1>Account Pending Approval</h1>
          <p>
            Welcome, <strong>{user?.name}</strong>! Your teacher account is currently awaiting admin approval.
          </p>
        </div>

        <div className="pending-info">
          <div className="info-item">
            <i className="ri-checkbox-circle-line"></i>
            <span>Your registration was successful</span>
          </div>
          <div className="info-item">
            <i className="ri-admin-line"></i>
            <span>An administrator will review your account</span>
          </div>
          <div className="info-item">
            <i className="ri-mail-line"></i>
            <span>You'll be able to access full features once approved</span>
          </div>
        </div>

        <div className="pending-status">
          <div className="status-label">Current Status</div>
          <div className="status-value pending">
            <i className="ri-loader-4-line"></i>
            Pending Approval
          </div>
        </div>

        <div className="pending-actions">
          <button className="auth-btn secondary" onClick={handleCheckStatus}>
            <i className="ri-refresh-line"></i> Check Status
          </button>
          <button className="auth-btn outline" onClick={handleLogout}>
            <i className="ri-logout-box-line"></i> Logout
          </button>
        </div>

        <div className="auth-footer">
          <p>
            <i className="ri-question-line"></i> Need help? Contact your institution's administrator.
          </p>
        </div>
      </div>
    </div>
  );
};

export default PendingApproval;
