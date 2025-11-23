import '../styles/ReportBadge.css';

const ReportBadge = ({ percentage }) => {
  const getBadgeConfig = () => {
    if (percentage >= 80) {
      return {
        label: 'Excellent',
        icon: 'ri-star-fill',
        className: 'excellent',
      };
    } else if (percentage >= 60) {
      return {
        label: 'Good',
        icon: 'ri-thumb-up-fill',
        className: 'good',
      };
    } else {
      return {
        label: 'Needs Improvement',
        icon: 'ri-arrow-up-circle-fill',
        className: 'needs-improvement',
      };
    }
  };

  const config = getBadgeConfig();

  return (
    <span className={`report-badge ${config.className}`}>
      <i className={config.icon}></i>
      {config.label}
    </span>
  );
};

export default ReportBadge;
