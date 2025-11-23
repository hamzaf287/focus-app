import '../styles/ConfirmDialog.css';

const ConfirmDialog = ({
  isOpen,
  title = 'Confirm Action',
  message,
  description,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  type = 'warning', // warning, danger, info
  onConfirm,
  onCancel,
  loading = false,
}) => {
  if (!isOpen) return null;

  const icons = {
    warning: 'ri-alert-line',
    danger: 'ri-delete-bin-line',
    info: 'ri-information-line',
  };

  return (
    <div className="confirm-overlay" onClick={onCancel}>
      <div className="confirm-dialog" onClick={(e) => e.stopPropagation()}>
        <div className={`confirm-header ${type}`}>
          <div className="confirm-icon">
            <i className={icons[type]}></i>
          </div>
          <h3 className="confirm-title">{title}</h3>
        </div>

        <div className="confirm-body">
          <p className="confirm-message">{message}</p>
          {description && <p className="confirm-description">{description}</p>}
        </div>

        <div className="confirm-footer">
          <button
            className="confirm-btn cancel"
            onClick={onCancel}
            disabled={loading}
          >
            {cancelText}
          </button>
          <button
            className={`confirm-btn confirm ${type}`}
            onClick={onConfirm}
            disabled={loading}
          >
            {loading ? (
              <>
                <i className="ri-loader-4-line ri-spin"></i>
                Processing...
              </>
            ) : (
              confirmText
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmDialog;
