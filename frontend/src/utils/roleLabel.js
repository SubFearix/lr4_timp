import { STAFF_ROLE_OPTIONS } from './options';

export const getRoleLabel = (role) => {
  const found = STAFF_ROLE_OPTIONS.find((opt) => opt.value === role);
  return found ? found.label : (role || 'Сотрудник');
};
