import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Toast from './components/Toast';
import Login from './pages/Login';
import Register from './pages/Register';
import VerifyOtp from './pages/VerifyOtp';
import Profile from './pages/Profile';
import Incidents from './pages/Incidents';
import IncidentDetail from './pages/IncidentDetail';
import Objects from './pages/Objects';
import Staff from './pages/Staff';
import VulnerabilityTypes from './pages/VulnerabilityTypes';
import ResponseMeasures from './pages/ResponseMeasures';
import Vulnerabilities from './pages/Vulnerabilities';
import ResponseLogs from './pages/ResponseLogs';
import './App.css';

function AppShell() {
  const { isAuthenticated, currentUser, logout, initializing } = useAuth();

  return (
    <div className="App">
      <header className="App-header">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true"></span>
          <div className="brand-text">
            <h1>Безопасность образовательного учреждения</h1>
            <p>Учёт инцидентов, объектов и уязвимостей</p>
          </div>
        </div>

        {isAuthenticated ? (
          <nav className="App-nav">
            <Link to="/incidents">Инциденты</Link>
            <Link to="/objects">Объекты</Link>
            <Link to="/staff">Сотрудники</Link>
            <Link to="/vulnerabilities">Уязвимости</Link>
            <Link to="/vul-types">Типы уязвимостей</Link>
            <Link to="/response-measures">Меры реагирования</Link>
            <Link to="/response-logs">Журнал реагирования</Link>
            <span className="App-nav-spacer" />
            <Link to="/profile" className="App-nav-user">{currentUser?.login}</Link>
            <button type="button" onClick={logout} className="App-nav-logout">
              Выйти
            </button>
          </nav>
        ) : (
          !initializing && (
            <nav className="App-nav">
              <Link to="/login">Войти</Link>
              <Link to="/register">Регистрация</Link>
            </nav>
          )
        )}
      </header>

      <main className="App-main">
        <Routes>
          <Route path="/login" element={isAuthenticated ? <Navigate to="/incidents" replace /> : <Login />} />
          <Route path="/register" element={isAuthenticated ? <Navigate to="/incidents" replace /> : <Register />} />
          <Route path="/verify-otp" element={isAuthenticated ? <Navigate to="/incidents" replace /> : <VerifyOtp />} />
          <Route path="/" element={<Navigate to="/incidents" replace />} />
          <Route path="/incidents" element={<ProtectedRoute><Incidents /></ProtectedRoute>} />
          <Route path="/incidents/:id" element={<ProtectedRoute><IncidentDetail /></ProtectedRoute>} />
          <Route path="/objects" element={<ProtectedRoute><Objects /></ProtectedRoute>} />
          <Route path="/staff" element={<ProtectedRoute><Staff /></ProtectedRoute>} />
          <Route path="/vulnerabilities" element={<ProtectedRoute><Vulnerabilities /></ProtectedRoute>} />
          <Route path="/vul-types" element={<ProtectedRoute><VulnerabilityTypes /></ProtectedRoute>} />
          <Route path="/response-measures" element={<ProtectedRoute><ResponseMeasures /></ProtectedRoute>} />
          <Route path="/response-logs" element={<ProtectedRoute><ResponseLogs /></ProtectedRoute>} />
          <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
        </Routes>
      </main>

      <footer className="App-footer">
        Безопасность образовательного учреждения — система учёта, 2026
      </footer>

      <Toast />
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <AppShell />
      </Router>
    </AuthProvider>
  );
}

export default App;
