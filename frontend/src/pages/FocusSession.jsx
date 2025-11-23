import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { sessionAPI } from '../services/api';
import { formatTimer } from '../utils/dateFormat';
import '../styles/FocusSession.css';

const FocusSession = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [isRunning, setIsRunning] = useState(false);
  const [stats, setStats] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [sessionStatus, setSessionStatus] = useState('not_started'); // not_started, running, ended

  const videoRef = useRef(null);
  const timerRef = useRef(null);
  const isRunningRef = useRef(isRunning);

  // Keep ref in sync with state for beforeunload handler
  useEffect(() => {
    isRunningRef.current = isRunning;
  }, [isRunning]);

  // Track tab switches
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden && isRunning) {
        sessionAPI.recordTabSwitch(sessionId, {
          timestamp: new Date().toISOString(),
          reason: 'visibilitychange',
        });
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [isRunning, sessionId]);

  // Beforeunload warning - prevent accidental navigation during active session
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (isRunningRef.current) {
        e.preventDefault();
        e.returnValue = 'You have an active focus session. Are you sure you want to leave? Your session will be stopped.';
        return e.returnValue;
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, []);

  // Timer effect
  useEffect(() => {
    if (isRunning) {
      timerRef.current = setInterval(() => {
        setElapsedTime((prev) => prev + 1);
      }, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [isRunning]);

  const startSession = async () => {
    setLoading(true);
    setError('');

    try {
      await sessionAPI.start(sessionId);
      setIsRunning(true);
      setSessionStatus('running');
      setElapsedTime(0);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to start session. Make sure camera is available.');
    } finally {
      setLoading(false);
    }
  };

  // Set video source after isRunning changes and img element is rendered
  useEffect(() => {
    if (isRunning && videoRef.current) {
      videoRef.current.src = sessionAPI.getVideoFeedUrl(sessionId);
    }
  }, [isRunning, sessionId]);

  const stopSession = async () => {
    setLoading(true);

    try {
      const response = await sessionAPI.stop(sessionId);
      setIsRunning(false);
      setSessionStatus('ended');
      setStats(response.data.statistics);

      // Clear video
      if (videoRef.current) {
        videoRef.current.src = '';
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to stop session');
    } finally {
      setLoading(false);
    }
  };

  const goBack = () => {
    navigate(-1);
  };

  const getFocusClass = (percentage) => {
    if (percentage >= 70) return 'good';
    if (percentage >= 50) return 'medium';
    return 'low';
  };

  const getStatusConfig = () => {
    switch (sessionStatus) {
      case 'running':
        return { label: 'Running', className: 'status-running', icon: 'ri-broadcast-line' };
      case 'ended':
        return { label: 'Ended', className: 'status-ended', icon: 'ri-check-line' };
      default:
        return { label: 'Not Started', className: 'status-not-started', icon: 'ri-time-line' };
    }
  };

  const statusConfig = getStatusConfig();

  return (
    <div className="focus-session-page">
      <div className="session-header">
        <button className="back-btn" onClick={goBack}>
          <i className="ri-arrow-left-line"></i> Back
        </button>
        <div className="header-center">
          <h1><i className="ri-focus-3-line"></i> Focus Detection Session</h1>
          <div className="session-meta">
            <span className={`status-pill ${statusConfig.className}`}>
              <i className={statusConfig.icon}></i>
              {statusConfig.label}
            </span>
            {(isRunning || sessionStatus === 'ended') && (
              <span className="timer-display">
                <i className="ri-timer-line"></i>
                {formatTimer(elapsedTime)}
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="session-container">
        <div className="video-section">
          <div className="video-wrapper">
            {isRunning ? (
              <img
                ref={videoRef}
                alt="Focus Detection Feed"
                className="video-feed"
              />
            ) : (
              <div className="video-placeholder">
                <i className="ri-camera-line"></i>
                <p>Camera feed will appear here</p>
                <p className="hint">Click "Start Session" to begin focus detection</p>
              </div>
            )}
          </div>

          {/* Live timer during session */}
          {isRunning && (
            <div className="live-timer-bar">
              <div className="timer-info">
                <i className="ri-timer-line"></i>
                <span className="timer-value">{formatTimer(elapsedTime)}</span>
              </div>
              <div className="timer-info">
                <i className="ri-broadcast-line"></i>
                <span>Recording in progress...</span>
              </div>
            </div>
          )}

          <div className="controls">
            {!isRunning && sessionStatus !== 'ended' ? (
              <button
                className="btn btn-success btn-large"
                onClick={startSession}
                disabled={loading}
              >
                {loading ? (
                  <>
                    <i className="ri-loader-4-line ri-spin"></i> Starting...
                  </>
                ) : (
                  <>
                    <i className="ri-play-line"></i> Start Session
                  </>
                )}
              </button>
            ) : isRunning ? (
              <button
                className="btn btn-danger btn-large"
                onClick={stopSession}
                disabled={loading}
              >
                {loading ? (
                  <>
                    <i className="ri-loader-4-line ri-spin"></i> Stopping...
                  </>
                ) : (
                  <>
                    <i className="ri-stop-line"></i> Stop Session
                  </>
                )}
              </button>
            ) : null}
          </div>

          {error && (
            <div className="error-message">
              <i className="ri-error-warning-line"></i> {error}
            </div>
          )}
        </div>

        <div className="stats-section">
          <h2><i className="ri-bar-chart-line"></i> Session Statistics</h2>

          {stats ? (
            <div className="stats-results">
              <div className="stat-item main-stat">
                <div className="stat-label">Focus Score</div>
                <div className={`stat-value large ${getFocusClass(stats.focus_percentage)}`}>
                  {stats.focus_percentage}%
                </div>
              </div>

              <div className="stat-grid">
                <div className="stat-item">
                  <div className="stat-label">Duration</div>
                  <div className="stat-value">
                    {Math.floor(stats.duration / 60)}m {stats.duration % 60}s
                  </div>
                </div>

                <div className="stat-item">
                  <div className="stat-label">Total Frames</div>
                  <div className="stat-value">{stats.total_frames}</div>
                </div>

                <div className="stat-item">
                  <div className="stat-label">Focused Frames</div>
                  <div className="stat-value good">{stats.focused_frames}</div>
                </div>

                <div className="stat-item">
                  <div className="stat-label">Distracted Frames</div>
                  <div className="stat-value low">{stats.distracted_frames}</div>
                </div>

                <div className="stat-item">
                  <div className="stat-label">Tab Switches</div>
                  <div className="stat-value">{stats.tab_switches_count}</div>
                </div>
              </div>

              <div className="result-message">
                {stats.focus_percentage >= 70 ? (
                  <p className="good"><i className="ri-checkbox-circle-line"></i> Great job! You maintained excellent focus.</p>
                ) : stats.focus_percentage >= 50 ? (
                  <p className="medium"><i className="ri-alert-line"></i> Good effort! Try to minimize distractions next time.</p>
                ) : (
                  <p className="low"><i className="ri-close-circle-line"></i> You seemed distracted. Try to improve your focus.</p>
                )}
              </div>

              {/* Post-session navigation */}
              <div className="post-session-actions">
                <button
                  className="btn btn-primary"
                  onClick={() => navigate(`/session/${sessionId}/report`)}
                >
                  <i className="ri-file-chart-line"></i> View Full Report
                </button>
                <button
                  className="btn btn-secondary"
                  onClick={() => navigate(user?.role === 'teacher' ? '/teacher' : '/student')}
                >
                  <i className="ri-dashboard-line"></i> Back to Dashboard
                </button>
              </div>
            </div>
          ) : (
            <div className="stats-placeholder">
              <i className="ri-line-chart-line"></i>
              <p>Statistics will appear after the session ends</p>
            </div>
          )}
        </div>
      </div>

      {isRunning && (
        <div className="warning-banner">
          <i className="ri-eye-line"></i>
          <span>Focus detection is active. Stay focused and avoid switching tabs!</span>
        </div>
      )}
    </div>
  );
};

export default FocusSession;
