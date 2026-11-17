import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { SELF_REGISTER_ROLE_OPTIONS } from '../utils/options';
import { PASSWORD_RULES, validatePasswordStrength, validatePhoneNumber } from '../utils/validators';

const initialState = {
  surname: '',
  name: '',
  patronymic: '',
  position: '',
  phonenum: '',
  email: '',
  login: '',
  password: '',
  confirmPassword: '',
  role: 'user',
  two_factor_enabled: true,
};

const Register = () => {
  const navigate = useNavigate();
  const { register, loading, error, clearError } = useAuth();
  const [form, setForm] = useState(initialState);
  const [validationErrors, setValidationErrors] = useState({});

  const passwordChecks = PASSWORD_RULES.map((rule) => ({
    ...rule,
    passed: rule.test(form.password),
  }));

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm((prev) => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
    setValidationErrors((prev) => ({ ...prev, [name]: '' }));
  };

  const validate = () => {
    const errors = {};
    if (!form.surname.trim()) errors.surname = 'Фамилия обязательна';
    if (!form.name.trim()) errors.name = 'Имя обязательно';
    if (!form.position.trim()) errors.position = 'Должность обязательна';
    const phoneError = validatePhoneNumber(form.phonenum);
    if (phoneError) errors.phonenum = phoneError;
    if (!/^\S+@\S+\.\S+$/.test(form.email)) errors.email = 'Введите корректный email';
    if (form.login.trim().length < 3) errors.login = 'Логин должен содержать минимум 3 символа';
    const passwordError = validatePasswordStrength(form.password);
    if (passwordError) errors.password = passwordError;
    if (form.password !== form.confirmPassword) errors.confirmPassword = 'Пароли не совпадают';
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    clearError();
    if (!validate()) return;
    try {
      const result = await register({
        surname: form.surname.trim(),
        name: form.name.trim(),
        patronymic: form.patronymic.trim() || null,
        position: form.position.trim(),
        phonenum: form.phonenum.trim(),
        email: form.email.trim(),
        login: form.login.trim(),
        password: form.password,
        role: form.role,
        two_factor_enabled: form.two_factor_enabled,
      });
      if (result.requiresOtp) {
        navigate('/verify-otp');
      } else {
        navigate('/incidents');
      }
    } catch (err) {
      // ошибка уже сохранена в контексте
    }
  };

  return (
    <div className="form-container">
      <h2>Регистрация сотрудника</h2>
      <p className="page-description">
        Создайте учётную запись сотрудника, чтобы получить доступ к системе
        учёта инцидентов безопасности образовательного учреждения. При входе
        с включённой двухфакторной аутентификацией на почту будет приходить
        одноразовый код подтверждения.
      </p>

      {error && <div className="error-banner">{error}</div>}

      <form onSubmit={handleSubmit} className="incident-form" noValidate>
        <div className={`form-group ${validationErrors.surname ? 'has-error' : ''}`}>
          <label>Фамилия <span className="required">*</span></label>
          <input name="surname" value={form.surname} onChange={handleChange} className={validationErrors.surname ? 'input-error' : ''} />
          {validationErrors.surname && <span className="validation-error">{validationErrors.surname}</span>}
        </div>

        <div className={`form-group ${validationErrors.name ? 'has-error' : ''}`}>
          <label>Имя <span className="required">*</span></label>
          <input name="name" value={form.name} onChange={handleChange} className={validationErrors.name ? 'input-error' : ''} />
          {validationErrors.name && <span className="validation-error">{validationErrors.name}</span>}
        </div>

        <div className="form-group">
          <label>Отчество</label>
          <input name="patronymic" value={form.patronymic} onChange={handleChange} />
        </div>

        <div className={`form-group ${validationErrors.position ? 'has-error' : ''}`}>
          <label>Должность <span className="required">*</span></label>
          <input name="position" value={form.position} onChange={handleChange} placeholder="Например: Охранник, Завуч по безопасности" className={validationErrors.position ? 'input-error' : ''} />
          {validationErrors.position && <span className="validation-error">{validationErrors.position}</span>}
        </div>

        <div className={`form-group ${validationErrors.phonenum ? 'has-error' : ''}`}>
          <label>Телефон <span className="required">*</span></label>
          <input name="phonenum" value={form.phonenum} onChange={handleChange} placeholder="+7 900 000-00-00" className={validationErrors.phonenum ? 'input-error' : ''} />
          {validationErrors.phonenum && <span className="validation-error">{validationErrors.phonenum}</span>}
        </div>

        <div className={`form-group ${validationErrors.email ? 'has-error' : ''}`}>
          <label>Email <span className="required">*</span></label>
          <input type="email" name="email" value={form.email} onChange={handleChange} className={validationErrors.email ? 'input-error' : ''} />
          {validationErrors.email && <span className="validation-error">{validationErrors.email}</span>}
        </div>

        <div className="form-group">
          <label>Роль</label>
          <select name="role" value={form.role} onChange={handleChange}>
            {SELF_REGISTER_ROLE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
          <span className="field-help">
            Роль «Администратор» через саморегистрацию недоступна — её выдаёт только текущий администратор.
          </span>
        </div>

        <div className={`form-group ${validationErrors.login ? 'has-error' : ''}`}>
          <label>Логин <span className="required">*</span></label>
          <input name="login" value={form.login} onChange={handleChange} autoComplete="username" className={validationErrors.login ? 'input-error' : ''} />
          {validationErrors.login && <span className="validation-error">{validationErrors.login}</span>}
        </div>

        <div className={`form-group ${validationErrors.password ? 'has-error' : ''}`}>
          <label>Пароль <span className="required">*</span></label>
          <input type="password" name="password" value={form.password} onChange={handleChange} autoComplete="new-password" className={validationErrors.password ? 'input-error' : ''} />
          <ul className="password-rules">
            {passwordChecks.map((rule) => (
              <li key={rule.id} className={rule.passed ? 'rule-ok' : 'rule-pending'}>
                {rule.label}
              </li>
            ))}
          </ul>
          {validationErrors.password && <span className="validation-error">{validationErrors.password}</span>}
        </div>

        <div className={`form-group ${validationErrors.confirmPassword ? 'has-error' : ''}`}>
          <label>Повторите пароль <span className="required">*</span></label>
          <input type="password" name="confirmPassword" value={form.confirmPassword} onChange={handleChange} autoComplete="new-password" className={validationErrors.confirmPassword ? 'input-error' : ''} />
          {validationErrors.confirmPassword && <span className="validation-error">{validationErrors.confirmPassword}</span>}
        </div>

        <div className="form-group form-group-checkbox">
          <label className="checkbox-label">
            <input
              type="checkbox"
              name="two_factor_enabled"
              checked={form.two_factor_enabled}
              onChange={handleChange}
            />
            Включить двухфакторную аутентификацию (код на почту при входе)
          </label>
        </div>

        <div className="form-actions">
          <button type="submit" className="btn btn-save" disabled={loading}>
            {loading ? 'Регистрация...' : 'Зарегистрироваться'}
          </button>
        </div>
      </form>

      <p className="auth-switch">
        Уже есть аккаунт? <Link to="/login">Войти</Link>
      </p>
    </div>
  );
};

export default Register;
