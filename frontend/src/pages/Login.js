import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Login = () => {
  const navigate = useNavigate();
  const { login, loading, error, clearError } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [formError, setFormError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    clearError();
    if (!username.trim() || !password) {
      setFormError('Заполните логин и пароль');
      return;
    }
    setFormError('');
    try {
      const result = await login(username.trim(), password);
      if (result.requiresOtp) {
        navigate('/verify-otp');
      } else {
        navigate('/incidents');
      }
    } catch (err) {
      // ошибка уже сохранена в контексте и отображена ниже
    }
  };

  return (
    <div className="form-container">
      <h2>Вход в систему</h2>
      <p className="page-description">
        Доступ к учёту инцидентов только для зарегистрированных сотрудников.
        После пароля потребуется одноразовый код, отправленный на почту.
      </p>

      {(error || formError) && <div className="error-banner">{error || formError}</div>}

      <form onSubmit={handleSubmit} className="incident-form" noValidate>
        <div className="form-group">
          <label>Логин <span className="required">*</span></label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Например: ivanov"
            autoComplete="username"
          />
        </div>

        <div className="form-group">
          <label>Пароль <span className="required">*</span></label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />
        </div>

        <div className="form-actions">
          <button type="submit" className="btn btn-save" disabled={loading}>
            {loading ? 'Вход...' : 'Войти'}
          </button>
        </div>
      </form>

      <p className="auth-switch">
        Нет аккаунта? <Link to="/register">Зарегистрироваться</Link>
      </p>
    </div>
  );
};

export default Login;
