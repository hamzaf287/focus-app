import { useState, useEffect, useRef, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import '../styles/Auth.css';

const Register = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [passwordFocused, setPasswordFocused] = useState(false);
  const [showPasswordTips, setShowPasswordTips] = useState(false);
  const [role, setRole] = useState('student'); // Default to student
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [touched, setTouched] = useState({
    name: false,
    email: false,
    password: false,
    confirmPassword: false,
  });

  const nameInputRef = useRef(null);
  const { register, login } = useAuth();
  const navigate = useNavigate();

  // Auto-focus name field on mount
  useEffect(() => {
    nameInputRef.current?.focus();
  }, []);

  // Clear error when user starts typing
  const handleFieldChange = (setter, field) => (e) => {
    setter(e.target.value);
    if (error) setError('');
  };

  // Mark field as touched on blur
  const handleBlur = (field) => () => {
    setTouched((prev) => ({ ...prev, [field]: true }));
  };

  // Validation helpers
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  const validationErrors = useMemo(() => {
    const errors = {};

    if (touched.name && name.trim().length < 3) {
      errors.name = 'Name must be at least 3 characters';
    }

    if (touched.email && !emailRegex.test(email)) {
      errors.email = 'Please enter a valid email address';
    }

    if (touched.password && password.length < 8) {
      errors.password = 'Password must be at least 8 characters';
    }

    if (touched.confirmPassword && confirmPassword !== password) {
      errors.confirmPassword = 'Passwords do not match';
    }

    return errors;
  }, [name, email, password, confirmPassword, touched]);

  // Password strength calculation
  const passwordStrength = useMemo(() => {
    if (!password) return { level: 0, label: '', color: '' };

    let strength = 0;
    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^A-Za-z0-9]/.test(password)) strength++;

    if (strength <= 2) return { level: strength, label: 'Weak', color: 'var(--error)' };
    if (strength <= 3) return { level: strength, label: 'Medium', color: 'var(--warning)' };
    return { level: strength, label: 'Strong', color: 'var(--success)' };
  }, [password]);

  // Check if form is valid for submission
  const isFormValid = useMemo(() => {
    return (
      name.trim().length >= 3 &&
      emailRegex.test(email) &&
      password.length >= 8 &&
      confirmPassword === password &&
      role
    );
  }, [name, email, password, confirmPassword, role]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Mark all fields as touched to show any validation errors
    setTouched({
      name: true,
      email: true,
      password: true,
      confirmPassword: true,
    });

    // Client-side validation
    if (name.trim().length < 3) {
      setError('Name must be at least 3 characters');
      return;
    }

    if (!emailRegex.test(email)) {
      setError('Please enter a valid email address');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    if (confirmPassword !== password) {
      setError('Passwords do not match');
      return;
    }

    setError('');
    setSuccess('');
    setLoading(true);

    try {
      await register(name.trim(), email.toLowerCase().trim(), password, role);

      // For students: auto-login and redirect to dashboard
      if (role === 'student') {
        setSuccess('Account created! Logging you in...');

        try {
          await login(email.toLowerCase().trim(), password);
          navigate('/student');
        } catch (loginErr) {
          // If auto-login fails, redirect to login page
          setSuccess('Account created! Redirecting to login...');
          setTimeout(() => navigate('/login'), 1500);
        }
      }
      // For teachers: redirect to pending approval page
      else if (role === 'teacher') {
        setSuccess('Account created! Redirecting to approval status...');

        try {
          await login(email.toLowerCase().trim(), password);
          navigate('/pending-approval');
        } catch (loginErr) {
          // If auto-login fails, redirect to login page
          setTimeout(() => navigate('/login'), 2000);
        }
      }
    } catch (err) {
      const status = err.response?.status;
      const serverMessage = err.response?.data?.error;

      // Specific error messages based on status code
      if (status === 409 || serverMessage?.toLowerCase().includes('exists')) {
        setError('An account with this email already exists. Try logging in instead.');
      } else if (status === 400) {
        setError(serverMessage || 'Please check your information and try again.');
      } else if (status >= 500 || !err.response) {
        setError('Something went wrong on our side. Please try again.');
      } else {
        setError(serverMessage || 'Registration failed. Please try again.');
      }
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
        <div className="auth-form-container register">
          <div className="auth-form-header">
            <h2>Get started with FocusCheck</h2>
            <p>Create your account as a student or teacher.</p>
          </div>

          {error && (
            <div className="auth-error">
              <i className="ri-error-warning-line"></i>
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="auth-success">
              <i className="ri-checkbox-circle-line"></i>
              <span>{success}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="auth-form">
            {/* Role Selector - Segmented Control */}
            <div className="form-group">
              <label>Choose your role</label>
              <div className="role-selector">
                <button
                  type="button"
                  className={`role-option ${role === 'student' ? 'active' : ''}`}
                  onClick={() => setRole('student')}
                  disabled={loading}
                >
                  <i className="ri-graduation-cap-line"></i>
                  <span>Student</span>
                </button>
                <button
                  type="button"
                  className={`role-option ${role === 'teacher' ? 'active' : ''}`}
                  onClick={() => setRole('teacher')}
                  disabled={loading}
                >
                  <i className="ri-presentation-line"></i>
                  <span>Teacher</span>
                </button>
              </div>

              {/* Role Info Box - Only show for teachers */}
              {role === 'teacher' && (
                <div className="role-info-box teacher">
                  <i className="ri-time-line"></i>
                  <span>Teacher accounts require admin approval before creating courses.</span>
                </div>
              )}
            </div>

            {/* Account Details Group */}
            <div className="form-section">
              <span className="form-section-label">Account details</span>
            </div>

            <div className="form-group compact">
              <label htmlFor="name">Full name</label>
              <input
                ref={nameInputRef}
                type="text"
                id="name"
                value={name}
                onChange={handleFieldChange(setName, 'name')}
                onBlur={handleBlur('name')}
                required
                placeholder="John Doe"
                disabled={loading}
                className={validationErrors.name ? 'input-error' : ''}
              />
              {validationErrors.name && (
                <p className="field-error">
                  <i className="ri-error-warning-line"></i>
                  {validationErrors.name}
                </p>
              )}
            </div>

            <div className="form-group compact">
              <label htmlFor="email">Email address</label>
              <input
                type="email"
                id="email"
                value={email}
                onChange={handleFieldChange(setEmail, 'email')}
                onBlur={handleBlur('email')}
                required
                placeholder="you@example.com"
                disabled={loading}
                className={validationErrors.email ? 'input-error' : ''}
              />
              {validationErrors.email && (
                <p className="field-error">
                  <i className="ri-error-warning-line"></i>
                  {validationErrors.email}
                </p>
              )}
            </div>

            {/* Security Group */}
            <div className="form-section">
              <span className="form-section-label">Security</span>
            </div>

            <div className="form-group compact">
              <label htmlFor="password">Password</label>
              <div className="password-input-wrapper">
                <input
                  type={showPassword ? 'text' : 'password'}
                  id="password"
                  value={password}
                  onChange={handleFieldChange(setPassword, 'password')}
                  onFocus={() => setPasswordFocused(true)}
                  onBlur={() => {
                    handleBlur('password')();
                    setPasswordFocused(false);
                  }}
                  required
                  placeholder="Min. 8 characters"
                  disabled={loading}
                  className={validationErrors.password ? 'input-error' : ''}
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

              {/* Password strength indicator - show when typing */}
              {password.length >= 1 && (
                <div className="password-strength">
                  <div className="strength-bar">
                    <div
                      className="strength-fill"
                      style={{
                        width: `${(passwordStrength.level / 5) * 100}%`,
                        backgroundColor: passwordStrength.color,
                      }}
                    />
                  </div>
                  <span className="strength-label" style={{ color: passwordStrength.color }}>
                    {passwordStrength.label}
                  </span>
                </div>
              )}

              {/* Password tips toggle - show when weak/medium */}
              {password.length >= 1 && passwordStrength.level < 4 && (
                <button
                  type="button"
                  className="password-tips-toggle"
                  onClick={() => setShowPasswordTips(!showPasswordTips)}
                >
                  <i className={showPasswordTips ? 'ri-arrow-up-s-line' : 'ri-question-line'}></i>
                  {showPasswordTips ? 'Hide tips' : 'How to make it stronger?'}
                </button>
              )}

              {/* Password requirements - expandable */}
              {showPasswordTips && password.length >= 1 && (
                <div className="password-requirements">
                  <p className={password.length >= 8 ? 'met' : ''}>
                    <i className={password.length >= 8 ? 'ri-checkbox-circle-fill' : 'ri-checkbox-blank-circle-line'}></i>
                    8+ characters
                  </p>
                  <p className={/[A-Z]/.test(password) ? 'met' : ''}>
                    <i className={/[A-Z]/.test(password) ? 'ri-checkbox-circle-fill' : 'ri-checkbox-blank-circle-line'}></i>
                    Uppercase letter
                  </p>
                  <p className={/[0-9]/.test(password) ? 'met' : ''}>
                    <i className={/[0-9]/.test(password) ? 'ri-checkbox-circle-fill' : 'ri-checkbox-blank-circle-line'}></i>
                    Number
                  </p>
                  <p className={/[^A-Za-z0-9]/.test(password) ? 'met' : ''}>
                    <i className={/[^A-Za-z0-9]/.test(password) ? 'ri-checkbox-circle-fill' : 'ri-checkbox-blank-circle-line'}></i>
                    Special character
                  </p>
                </div>
              )}
            </div>

            <div className="form-group compact">
              <label htmlFor="confirmPassword">Confirm password</label>
              <div className="password-input-wrapper">
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  id="confirmPassword"
                  value={confirmPassword}
                  onChange={handleFieldChange(setConfirmPassword, 'confirmPassword')}
                  onBlur={handleBlur('confirmPassword')}
                  required
                  placeholder="Re-enter your password"
                  disabled={loading}
                  className={validationErrors.confirmPassword ? 'input-error' : ''}
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  tabIndex={-1}
                  aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
                >
                  <i className={showConfirmPassword ? 'ri-eye-off-line' : 'ri-eye-line'}></i>
                </button>
              </div>

              {/* Live password match feedback */}
              {confirmPassword && (
                <p className={`password-match ${confirmPassword === password ? 'match' : 'no-match'}`}>
                  <i className={confirmPassword === password ? 'ri-checkbox-circle-fill' : 'ri-close-circle-fill'}></i>
                  {confirmPassword === password ? 'Passwords match' : 'Passwords do not match'}
                </p>
              )}
            </div>

            <button
              type="submit"
              className="auth-submit-btn"
              disabled={loading || !isFormValid}
            >
              {loading ? (
                <>
                  <i className="ri-loader-4-line ri-spin"></i>
                  <span>Creating account...</span>
                </>
              ) : (
                <>
                  <span>Create my account</span>
                  <i className="ri-arrow-right-line"></i>
                </>
              )}
            </button>
          </form>

          <div className="auth-form-footer">
            <span>Already have an account?</span>
            <Link to="/login">Log in <i className="ri-arrow-right-s-line"></i></Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Register;
