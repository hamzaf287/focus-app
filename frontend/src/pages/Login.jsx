import { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import '../styles/Auth.css';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const emailInputRef = useRef(null);
  const { login } = useAuth();
  const navigate = useNavigate();

  // Auto-focus email field on mount
  useEffect(() => {
    emailInputRef.current?.focus();
  }, []);

  // Clear error when user starts typing
  const handleEmailChange = (e) => {
    setEmail(e.target.value);
    if (error) setError('');
  };

  const handlePasswordChange = (e) => {
    setPassword(e.target.value);
    if (error) setError('');
  };

  // Email validation regex
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Client-side validation
    if (!email.trim()) {
      setError('Please enter your email address');
      return;
    }

    if (!emailRegex.test(email.trim())) {
      setError('Please enter a valid email address');
      return;
    }

    if (!password) {
      setError('Please enter your password');
      return;
    }

    setError('');
    setLoading(true);

    try {
      const data = await login(email.toLowerCase().trim(), password);

      // Redirect based on role and status
      const user = data.user;
      if (user?.role === 'student') {
        navigate('/student');
      } else if (user?.role === 'teacher') {
        // Check if teacher is pending approval
        if (user?.status === 'pending') {
          navigate('/pending-approval');
        } else {
          navigate('/teacher');
        }
      } else if (user?.role === 'admin') {
        navigate('/admin');
      } else {
        navigate('/');
      }
    } catch (err) {
      const status = err.response?.status;
      const serverMessage = err.response?.data?.error;

      // More specific error messages
      if (status === 401) {
        setError('Invalid email or password. Please try again.');
      } else if (status === 403) {
        setError(serverMessage || 'Your account is not active. Please contact support.');
      } else if (status >= 500 || !err.response) {
        setError('Unable to connect. Please check your internet connection and try again.');
      } else {
        setError(serverMessage || 'Login failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-split-layout">
      {/* Hero Panel - Left Side */}
      <div className="auth-hero">
        <div className="hero-content">
          {/* Logo */}
          <div className="hero-logo">
            <div className="hero-logo-icon">
              <i className="ri-focus-3-line"></i>
            </div>
            <span className="hero-logo-text">FocusCheck</span>
          </div>

          {/* Main Headline */}
          <div className="hero-headline">
            <h1>Brew better focus.</h1>
            <p>AI-powered attention tracking for classrooms and beyond.</p>
          </div>

          {/* Feature List */}
          <div className="hero-features">
            <div className="hero-feature">
              <div className="feature-icon">
                <i className="ri-brain-line"></i>
              </div>
              <div className="feature-text">
                <strong>AI focus detection</strong>
              </div>
            </div>
            <div className="hero-feature">
              <div className="feature-icon">
                <i className="ri-bar-chart-box-line"></i>
              </div>
              <div className="feature-text">
                <strong>Session analytics</strong>
              </div>
            </div>
            <div className="hero-feature">
              <div className="feature-icon">
                <i className="ri-team-line"></i>
              </div>
              <div className="feature-text">
                <strong>Multi-role platform</strong>
              </div>
            </div>
          </div>
        </div>

        {/* Background decoration */}
        <div className="hero-decoration">
          <div className="decoration-circle circle-1"></div>
          <div className="decoration-circle circle-2"></div>
        </div>
      </div>

      {/* Form Panel - Right Side */}
      <div className="auth-form-panel">
        <div className="auth-form-container">
          <div className="auth-form-header">
            <h2>Sign in to FocusCheck</h2>
            <p>Track your focus and sessions</p>
          </div>

          {error && (
            <div className="auth-error">
              <i className="ri-error-warning-line"></i>
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="auth-form">
            <div className="form-group">
              <label htmlFor="email">Email address</label>
              <input
                ref={emailInputRef}
                type="email"
                id="email"
                value={email}
                onChange={handleEmailChange}
                placeholder="you@example.com"
                disabled={loading}
                autoComplete="email"
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <div className="password-input-wrapper">
                <input
                  type={showPassword ? 'text' : 'password'}
                  id="password"
                  value={password}
                  onChange={handlePasswordChange}
                  placeholder="Enter your password"
                  disabled={loading}
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                  tabIndex={-1}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  <i className={showPassword ? 'ri-eye-off-line' : 'ri-eye-line'}></i>
                </button>
              </div>
            </div>

            <div className="forgot-password-row">
              <Link to="#" className="forgot-password-link">Forgot password?</Link>
            </div>

            <button type="submit" className="auth-submit-btn" disabled={loading}>
              {loading ? (
                <>
                  <i className="ri-loader-4-line ri-spin"></i>
                  <span>Signing in...</span>
                </>
              ) : (
                <>
                  <span>Log in to FocusCheck</span>
                  <i className="ri-arrow-right-line"></i>
                </>
              )}
            </button>
          </form>

          <div className="auth-form-footer">
            <span>New here?</span>
            <Link to="/register">Create an account <i className="ri-arrow-right-s-line"></i></Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
