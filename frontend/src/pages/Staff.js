import React from 'react';
import EntityCrudPage from '../components/EntityCrudPage';
import { STAFF_ROLE_OPTIONS } from '../utils/options';
import { validatePasswordStrength, validatePhoneNumber } from '../utils/validators';
import { canManageStaff } from '../utils/permissions';

const config = {
  title: 'Сотрудники',
  entityLabel: 'сотрудник',
  endpoint: '/staff',
  idField: 'id_s',
  // Управлять сотрудниками (создавать/редактировать/удалять, в том
  // числе менять роли) может только администратор — это же само собой
  // разумеется проверяется и на бэкенде (backend/app/routers/staff.py),
  // здесь только скрываем недоступные кнопки.
  canCreate: canManageStaff,
  canEdit: canManageStaff,
  canDelete: canManageStaff,
  columns: [
    { key: 'id_s', label: 'ID' },
    { key: 'surname', label: 'Фамилия' },
    { key: 'name', label: 'Имя' },
    { key: 'position', label: 'Должность' },
    { key: 'phonenum', label: 'Телефон' },
    { key: 'login', label: 'Логин' },
    { key: 'role', label: 'Роль', render: (item) => (STAFF_ROLE_OPTIONS.find((r) => r.value === item.role)?.label || item.role) },
    { key: 'two_factor_enabled', label: '2FA', render: (item) => (item.two_factor_enabled ? 'Включена' : 'Отключена') },
  ],
  filters: [
    { name: 'role', label: 'Роль', type: 'select', options: STAFF_ROLE_OPTIONS },
    { name: 'search', label: 'Поиск по фамилии/логину', type: 'text', placeholder: 'Фамилия, имя или логин...' },
  ],
  fields: [
    { name: 'surname', label: 'Фамилия', type: 'text', required: true },
    { name: 'name', label: 'Имя', type: 'text', required: true },
    { name: 'patronymic', label: 'Отчество', type: 'text' },
    { name: 'position', label: 'Должность', type: 'text', required: true, placeholder: 'Например: Охранник, Завуч по безопасности' },
    {
      name: 'phonenum', label: 'Телефон', type: 'text', required: true, placeholder: '+7 900 000-00-00',
      validate: validatePhoneNumber,
    },
    { name: 'email', label: 'Email', type: 'text', required: true },
    { name: 'role', label: 'Роль', type: 'select', options: STAFF_ROLE_OPTIONS, required: true, defaultValue: 'user' },
    { name: 'login', label: 'Логин', type: 'text', requiredOnCreate: true, disabledOnEdit: true, helpText: 'Логин нельзя изменить после создания' },
    {
      name: 'password', label: 'Пароль', type: 'password', requiredOnCreate: true,
      helpText: 'Минимум 8 символов, заглавная и строчная буква, цифра',
      validate: validatePasswordStrength,
    },
    { name: 'two_factor_enabled', label: 'Двухфакторная аутентификация', type: 'checkbox', defaultValue: true, checkboxLabel: 'Включить двухфакторную аутентификацию (код на почту при входе)' },
  ],
};

const Staff = () => <EntityCrudPage config={config} />;

export default Staff;
