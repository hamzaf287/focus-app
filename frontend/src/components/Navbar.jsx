import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import ConfirmDialog from './ConfirmDialog';
import '../styles/Navbar.css';

const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);

  const handleLogoutClick = () => {
    setMobileMenuOpen(false);
    setShowLogoutConfirm(true);
  };

  const handleLogoutConfirm = async () => {
    setLoggingOut(true);
    try {
      await logout();
      navigate('/login');
    } finally {
      setLoggingOut(false);
      setShowLogoutConfirm(false);
    }
  };

  const handleLogoutCancel = () => {
    setShowLogoutConfirm(false);
  };

  const getRoleConfig = () => {
    const configs = {
      student: {
        label: 'Student',
        className: 'role-student',
        icon: 'ri-graduation-cap-line',
        dashboardPath: '/student'
      },
      teacher: {
        label: 'Teacher',
        className: 'role-teacher',
        icon: 'ri-presentation-line',
        dashboardPath: '/teacher'
      },
      admin: {
        label: 'Admin',
        className: 'role-admin',
        icon: 'ri-shield-star-line',
        dashboardPath: '/admin'
      },
    };
    return configs[user?.role] || { label: 'User', className: '', icon: 'ri-user-line', dashboardPath: '/' };
  };

  const getCurrentSection = () => {
    if (location.pathname.startsWith('/student')) return { name: 'Dashboard', icon: 'ri-dashboard-line' };
    if (location.pathname.startsWith('/teacher')) return { name: 'Dashboard', icon: 'ri-dashboard-line' };
    if (location.pathname.startsWith('/admin')) return { name: 'Admin Panel', icon: 'ri-settings-3-line' };
    if (location.pathname.startsWith('/session')) return { name: 'Focus Session', icon: 'ri-focus-3-line' };
    return { name: 'Home', icon: 'ri-home-line' };
  };

  const roleConfig = getRoleConfig();
  const currentSection = getCurrentSection();
  const isInSession = location.pathname.startsWith('/session');

  // Get user initials for avatar
  const getInitials = () => {
    if (!user?.name) return 'U';
    const names = user.name.split(' ');
    if (names.length >= 2) {
      return `${names[0][0]}${names[1][0]}`.toUpperCase();
    }
    return names[0][0].toUpperCase();
  };

  return (
    <nav className={`navbar ${isInSession ? 'navbar-session' : ''}`}>
      {/* Background decoration */}
      <div className="navbar-bg-pattern"></div>

      <div className="navbar-content">
        {/* Logo and Brand */}
        <div className="navbar-brand">
          <Link to={roleConfig.dashboardPath} className="brand-link">
            <div className="brand-logo">
              <i className="ri-focus-3-line"></i>
            </div>
            <div className="brand-text">
              <span className="brand-name">FocusCheck</span>
              <span className="brand-tagline">Stay Focused</span>
            </div>
          </Link>
        </div>

        {/* Center - Current Section Breadcrumb */}
        <div className="navbar-center">
          <div className="breadcrumb">
            <span className="breadcrumb-role">
              <i className={roleConfig.icon}></i>
              {roleConfig.label}
            </span>
            <i className="ri-arrow-right-s-line breadcrumb-separator"></i>
            <span className="breadcrumb-section">
              <i className={currentSection.icon}></i>
              {currentSection.name}
            </span>
          </div>
        </div>

        {/* Right - User Area */}
        <div className="navbar-user">
          {/* User Profile Card */}
          <div className="user-card">
            <div className="user-avatar-wrapper">
              <div className={`user-avatar ${roleConfig.className}`}>
                {getInitials()}
              </div>
              <span className="avatar-status"></span>
            </div>
            <div className="user-info">
              <span className="user-name">{user?.name || 'User'}</span>
              <span className={`user-role-badge ${roleConfig.className}`}>
                <i className={roleConfig.icon}></i>
                {roleConfig.label}
              </span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="navbar-actions">
            {!isInSession && (
              <Link to={roleConfig.dashboardPath} className="nav-action-btn" title="Go to Dashboard">
                <i className="ri-dashboard-line"></i>
              </Link>
            )}
            <button className="nav-action-btn logout" onClick={handleLogoutClick} title="Logout">
              <i className="ri-logout-box-r-line"></i>
            </button>
          </div>

          {/* Mobile Menu Toggle */}
          <button
            className="mobile-menu-btn"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            <i className={mobileMenuOpen ? 'ri-close-line' : 'ri-menu-line'}></i>
          </button>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      <div className={`mobile-menu ${mobileMenuOpen ? 'open' : ''}`}>
        <div className="mobile-user-info">
          <div className={`mobile-avatar ${roleConfig.className}`}>
            {getInitials()}
          </div>
          <div className="mobile-user-details">
            <span className="mobile-user-name">{user?.name || 'User'}</span>
            <span className={`mobile-user-role ${roleConfig.className}`}>
              <i className={roleConfig.icon}></i> {roleConfig.label}
            </span>
          </div>
        </div>
        <div className="mobile-menu-items">
          <Link
            to={roleConfig.dashboardPath}
            className="mobile-menu-item"
            onClick={() => setMobileMenuOpen(false)}
          >
            <i className="ri-dashboard-line"></i>
            <span>Dashboard</span>
          </Link>
          <button className="mobile-menu-item logout" onClick={handleLogoutClick}>
            <i className="ri-logout-box-r-line"></i>
            <span>Logout</span>
          </button>
        </div>
      </div>

      {/* Logout Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showLogoutConfirm}
        title="Logout"
        message={`Are you sure you want to logout, ${user?.name?.split(' ')[0] || 'User'}?`}
        description="You will need to sign in again to access your account."
        confirmText="Yes, Logout"
        cancelText="Stay Signed In"
        type="warning"
        onConfirm={handleLogoutConfirm}
        onCancel={handleLogoutCancel}
        loading={loggingOut}
      />
    </nav>
  );
};

export default Navbar;
