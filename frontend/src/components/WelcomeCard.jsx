import '../styles/WelcomeCard.css';

const WelcomeCard = ({ user, stats }) => {
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  return (
    <div className="welcome-card">
      <div className="welcome-content">
        <h1 className="welcome-greeting">
          {getGreeting()}, <span className="welcome-name">{user?.name?.split(' ')[0] || 'User'}</span>!
        </h1>
        <p className="welcome-subtitle">
          {user?.role === 'student' && "Ready to stay focused today?"}
          {user?.role === 'teacher' && "Manage your courses and sessions"}
          {user?.role === 'admin' && "System overview and management"}
        </p>
      </div>

      <div className="welcome-stats">
        {stats?.map((stat, index) => (
          <div key={index} className="welcome-stat">
            <span className="stat-value">{stat.value}</span>
            <span className="stat-label">{stat.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default WelcomeCard;
