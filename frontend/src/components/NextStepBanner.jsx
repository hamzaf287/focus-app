import { useNavigate } from 'react-router-dom';
import '../styles/NextStepBanner.css';

const NextStepBanner = ({ type, data, onAction }) => {
  const navigate = useNavigate();

  const bannerConfig = {
    no_courses: {
      icon: 'ri-book-open-line',
      title: 'Get Started!',
      message: "You haven't enrolled in any courses yet.",
      action: 'Browse Available Courses',
      color: 'info',
    },
    no_active_session: {
      icon: 'ri-time-line',
      title: 'No Active Sessions',
      message: 'Wait for your teacher to start a focus session.',
      action: null,
      color: 'neutral',
    },
    active_session: {
      icon: 'ri-play-circle-line',
      title: 'Session Active!',
      message: `${data?.courseName || 'A session'} is running now.`,
      action: 'Join Session Now',
      color: 'success',
    },
    pending_requests: {
      icon: 'ri-user-add-line',
      title: `${data?.count || 0} Pending Requests`,
      message: 'Students are waiting for enrollment approval.',
      action: 'Review Requests',
      color: 'warning',
    },
    active_sessions_teacher: {
      icon: 'ri-broadcast-line',
      title: `${data?.count || 0} Active Sessions`,
      message: 'You have sessions currently running.',
      action: 'View Sessions',
      color: 'success',
    },
  };

  const config = bannerConfig[type];
  if (!config) return null;

  const handleAction = () => {
    if (type === 'active_session' && data?.sessionId) {
      navigate(`/session/${data.sessionId}`);
    } else if (onAction) {
      onAction();
    }
  };

  return (
    <div className={`next-step-banner ${config.color}`}>
      <div className="banner-icon">
        <i className={config.icon}></i>
      </div>
      <div className="banner-content">
        <h3 className="banner-title">{config.title}</h3>
        <p className="banner-message">{config.message}</p>
      </div>
      {config.action && (
        <button className="banner-action" onClick={handleAction}>
          {config.action}
          <i className="ri-arrow-right-line"></i>
        </button>
      )}
    </div>
  );
};

export default NextStepBanner;
