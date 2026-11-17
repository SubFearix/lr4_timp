import React, { useState, useEffect, useRef, useCallback } from 'react';
import './Toast.css';

let idCounter = 0;

const Toast = () => {
  const [toasts, setToasts] = useState([]);
  const timers = useRef({});

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
    clearTimeout(timers.current[id]);
    delete timers.current[id];
  }, []);

  useEffect(() => {
    const handler = (event) => {
      const { message, status } = event.detail || {};
      const id = ++idCounter;
      setToasts((prev) => [...prev, { id, message: message || 'Произошла ошибка', status }]);
      timers.current[id] = setTimeout(() => removeToast(id), 6000);
    };
    window.addEventListener('app_error', handler);
    return () => window.removeEventListener('app_error', handler);
  }, [removeToast]);

  if (toasts.length === 0) return null;

  return (
    <div className="toast-stack" role="status" aria-live="polite">
      {toasts.map((toast) => (
        <div key={toast.id} className="toast-item">
          <span className="toast-status">{toast.status || 'Ошибка'}</span>
          <span className="toast-message">{toast.message}</span>
          <button
            type="button"
            className="toast-close"
            onClick={() => removeToast(toast.id)}
            aria-label="Закрыть уведомление"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
};

export default Toast;
