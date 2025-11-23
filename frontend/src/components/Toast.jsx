import '../styles/Toast.css';

const Toast = ({ message, type = 'info', onClose }) => {
  const icons = {
    success: 'ri-checkbox-circle-fill',
    error: 'ri-error-warning-fill',
    warning: 'ri-alert-fill',
    info: 'ri-information-fill',
  };

  const titles = {
    success: 'Success',
    error: 'Error',
    warning: 'Warning',
    info: 'Info',
  };

  return (
    <div className="toast-container">
      <div className={`toast ${type}`}>
        <div className="toast-icon">
          <i className={icons[type]}></i>
        </div>
        <div className="toast-content">
          <div className="toast-title">{titles[type]}</div>
          <div className="toast-message">{message}</div>
        </div>
        <div className="toast-close" onClick={onClose}>
          <i className="ri-close-line"></i>
        </div>
      </div>
    </div>
  );
};

export default Toast;
