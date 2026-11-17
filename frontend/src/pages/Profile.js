import React from 'react';
import { useAuth } from '../context/AuthContext';
import { getRoleLabel } from '../utils/roleLabel';

const Profile = () => {
  const { currentUser, logout } = useAuth();

  if (!currentUser) return null;

  const fullName = [currentUser.surname, currentUser.name, currentUser.patronymic]
    .filter(Boolean)
    .join(' ');

  return (
    <div className="detail-container">
      <h2>Профиль</h2>
      <div className="detail-card">
        <div className="detail-title-row">
          <h2>{fullName}</h2>
          <span className="status-tag status-open">{getRoleLabel(currentUser.role)}</span>
        </div>
        <p className="detail-type">{currentUser.position}</p>
        <div className="detail-info">
          <p><strong>Логин</strong>{currentUser.login}</p>
          <p><strong>Email</strong>{currentUser.email}</p>
          <p><strong>Телефон</strong>{currentUser.phonenum}</p>
          <p><strong>ID сотрудника</strong>{currentUser.id_s}</p>
        </div>
        <div className="form-actions">
          <button type="button" className="btn btn-cancel" onClick={logout}>
            Выйти из аккаунта
          </button>
        </div>
      </div>
    </div>
  );
};

export default Profile;
