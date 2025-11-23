import { useNavigate } from 'react-router-dom';
import '../styles/ActiveSessionBanner.css';

const ActiveSessionBanner = ({ courseName, courseCode, sessionName, sessionId, teacherName }) => {
  const navigate = useNavigate();

  const handleJoin = () => {
    navigate(`/session/${sessionId}`);
  };

  return (
    <div className="active-session-banner">
      <div className="asb-pulse-ring"></div>
      <div className="asb-pulse-ring delay"></div>

      <div className="asb-content">
        <div className="asb-live-indicator">
          <span className="asb-live-dot"></span>
          <span className="asb-live-text">LIVE NOW</span>
        </div>

        <div className="asb-main">
          <div className="asb-info">
            <h3 className="asb-title">
              <i className="ri-broadcast-line"></i>
              Session in Progress
            </h3>
            <div className="asb-details">
              <span className="asb-course">
                <i className="ri-book-open-line"></i>
                {courseCode ? `${courseCode} - ${courseName}` : courseName}
              </span>
              {sessionName && (
                <span className="asb-session-name">
                  <i className="ri-calendar-event-line"></i>
                  {sessionName}
                </span>
              )}
              {teacherName && (
                <span className="asb-teacher">
                  <i className="ri-user-line"></i>
                  {teacherName}
                </span>
              )}
            </div>
          </div>

          <button className="asb-join-btn" onClick={handleJoin}>
            <i className="ri-play-circle-fill"></i>
            <span>Join Session</span>
            <i className="ri-arrow-right-line asb-arrow"></i>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ActiveSessionBanner;
