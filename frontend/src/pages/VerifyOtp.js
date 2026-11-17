import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const CODE_LENGTH = 6;

const VerifyOtp = () => {
  const navigate = useNavigate();
  const { pendingAuth, verifyOtp, resendOtp, cancelOtp, loading, error, clearError } = useAuth();
  const [code, setCode] = useState('');
  const [formError, setFormError] = useState('');
  const [secondsLeft, setSecondsLeft] = useState(0);
  const [resendCooldown, setResendCooldown] = useState(0);
  const timerRef = useRef(null);
  const cooldownRef = useRef(null);

  useEffect(() => {
    if (!pendingAuth) return undefined;
    const tick = () => {
      const elapsed = Math.floor((Date.now() - pendingAuth.issuedAt) / 1000);
      setSecondsLeft(Math.max(0, pendingAuth.expiresIn - elapsed));
    };
    tick();
    timerRef.current = setInterval(tick, 1000);
    return () => clearInterval(timerRef.current);
  }, [pendingAuth]);

  useEffect(() => {
    if (resendCooldown <= 0) return undefined;
    cooldownRef.current = setInterval(() => {
      setResendCooldown((prev) => (prev <= 1 ? 0 : prev - 1));
    }, 1000);
    return () => clearInterval(cooldownRef.current);
  }, [resendCooldown]);

  if (!pendingAuth) {
    return <Navigate to="/login" replace />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormError('');
    clearError();
    if (code.trim().length !== CODE_LENGTH) {
      setFormError(`Введите ${CODE_LENGTH}-значный код из письма`);
      return;
    }
    try {
      await verifyOtp(code.trim());
      navigate('/incidents');
    } catch (err) {
      setFormError(err.message);
    }
  };

  const handleResend = async () => {
    setFormError('');
    clearError();
    try {
      await resendOtp();
      setCode('');
      setResendCooldown(30);
    } catch (err) {
      setFormError(err.message);
    }
  };

  const handleCancel = () => {
    cancelOtp();
    navigate('/login');
  };

  return (
    <div className="form-container">
      <h2>Подтверждение входа</h2>
      <p className="page-description">
        Мы отправили одноразовый код на почту <strong>{pendingAuth.maskedEmail}</strong>.
        Проверьте входящие (и папку «Спам»), введите код ниже — он
        действителен {Math.max(pendingAuth.expiresIn / 60, 1)} минут.
      </p>

      {(formError || error) && <div className="error-banner">{formError || error}</div>}

      <form onSubmit={handleSubmit} className="incident-form" noValidate>
        <div className="form-group">
          <label>Код из письма <span className="required">*</span></label>
          <input
            type="text"
            inputMode="numeric"
            maxLength={CODE_LENGTH}
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
            placeholder="000000"
            className="otp-code-input"
            autoFocus
          />
          <span className="field-help">
            {secondsLeft > 0 ? `Код действителен ещё ${secondsLeft} сек.` : 'Срок действия кода истёк, запросите новый'}
          </span>
        </div>

        <div className="form-actions">
          <button type="submit" className="btn btn-save" disabled={loading}>
            {loading ? 'Проверка...' : 'Подтвердить'}
          </button>
          <button
            type="button"
            className="btn btn-cancel"
            onClick={handleResend}
            disabled={resendCooldown > 0}
          >
            {resendCooldown > 0 ? `Повторно через ${resendCooldown} сек.` : 'Отправить код повторно'}
          </button>
        </div>
      </form>

      <p className="auth-switch">
        <button type="button" className="link-button" onClick={handleCancel}>
          Отменить и вернуться к входу
        </button>
      </p>
    </div>
  );
};

export default VerifyOtp;
