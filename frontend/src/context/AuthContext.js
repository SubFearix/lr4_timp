import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import api from '../api/axios';
import { getErrorMessage } from '../api/errors';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth должен быть использован внутри AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [initializing, setInitializing] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  // Промежуточное состояние второго шага входа (2FA): заполняется, когда
  // /login отвечает requires_otp=true, и обнуляется после успешной
  // проверки кода или отмены входа.
  const [pendingAuth, setPendingAuth] = useState(null);

  const isAuthenticated = Boolean(currentUser);

  const clearError = () => setError(null);

  const clearSession = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setCurrentUser(null);
  }, []);

  const loadProfile = useCallback(async () => {
    try {
      const response = await api.get('/profile');
      setCurrentUser(response.data);
      return response.data;
    } catch (err) {
      clearSession();
      return null;
    }
  }, [clearSession]);

  useEffect(() => {
    const init = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        await loadProfile();
      }
      setInitializing(false);
    };
    init();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // axios.js бросает это событие, когда access_token истёк и продлить
  // сессию через /refresh не удалось (истёк и refresh_token).
  useEffect(() => {
    const handleLogout = () => clearSession();
    window.addEventListener('auth_logout', handleLogout);
    return () => window.removeEventListener('auth_logout', handleLogout);
  }, [clearSession]);

  const applyTokens = (tokens) => {
    localStorage.setItem('access_token', tokens.access_token);
    localStorage.setItem('refresh_token', tokens.refresh_token);
  };

  // Общий обработчик ответа /login: либо сразу приходят токены (2FA
  // отключена у сотрудника), либо requires_otp=true и нужно перейти на
  // страницу ввода кода.
  const handleLoginResponse = useCallback(async (data) => {
    if (data.requires_otp) {
      setPendingAuth({
        pendingToken: data.pending_token,
        maskedEmail: data.masked_email,
        expiresIn: data.expires_in,
        issuedAt: Date.now(),
      });
      return { requiresOtp: true, maskedEmail: data.masked_email, expiresIn: data.expires_in };
    }
    applyTokens(data);
    const user = await loadProfile();
    return { requiresOtp: false, user };
  }, [loadProfile]);

  const login = useCallback(async (username, password) => {
    setLoading(true);
    setError(null);
    try {
      const form = new URLSearchParams();
      form.set('username', username);
      form.set('password', password);
      const response = await api.post('/login', form);
      return await handleLoginResponse(response.data);
    } catch (err) {
      const message = getErrorMessage(err);
      setError(message);
      throw new Error(message);
    } finally {
      setLoading(false);
    }
  }, [handleLoginResponse]);

  const register = useCallback(async (payload) => {
    setLoading(true);
    setError(null);
    try {
      await api.post('/register', payload);
      // После регистрации сразу проходим обычный вход — если у аккаунта
      // включена 2FA (по умолчанию да), это приведёт к запросу кода на
      // почту точно так же, как при обычном логине.
      const form = new URLSearchParams();
      form.set('username', payload.login);
      form.set('password', payload.password);
      const response = await api.post('/login', form);
      return await handleLoginResponse(response.data);
    } catch (err) {
      const message = getErrorMessage(err);
      setError(message);
      throw new Error(message);
    } finally {
      setLoading(false);
    }
  }, [handleLoginResponse]);

  const verifyOtp = useCallback(async (code) => {
    if (!pendingAuth) {
      const message = 'Сессия входа истекла. Начните вход заново.';
      setError(message);
      throw new Error(message);
    }
    setLoading(true);
    setError(null);
    try {
      const response = await api.post('/login/verify-otp', {
        pending_token: pendingAuth.pendingToken,
        code,
      });
      applyTokens(response.data);
      const user = await loadProfile();
      setPendingAuth(null);
      return user;
    } catch (err) {
      const message = getErrorMessage(err);
      setError(message);
      throw new Error(message);
    } finally {
      setLoading(false);
    }
  }, [pendingAuth, loadProfile]);

  const resendOtp = useCallback(async () => {
    if (!pendingAuth) return null;
    setError(null);
    try {
      const response = await api.post('/login/resend-otp', {
        pending_token: pendingAuth.pendingToken,
      });
      setPendingAuth((prev) => (prev ? {
        ...prev,
        expiresIn: response.data.expires_in,
        issuedAt: Date.now(),
      } : prev));
      return response.data;
    } catch (err) {
      const message = getErrorMessage(err);
      setError(message);
      throw new Error(message);
    }
  }, [pendingAuth]);

  const cancelOtp = useCallback(() => {
    setPendingAuth(null);
    setError(null);
  }, []);

  const logout = useCallback(() => {
    clearSession();
  }, [clearSession]);

  const value = {
    currentUser,
    isAuthenticated,
    initializing,
    loading,
    error,
    pendingAuth,
    login,
    register,
    verifyOtp,
    resendOtp,
    cancelOtp,
    logout,
    clearError,
    refreshProfile: loadProfile,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthContext;
