// Ролевая модель доступа — зеркало backend/app/permissions.py. UI
// использует её только для того, чтобы не показывать заведомо
// недоступные кнопки/страницы; реальная защита — на сервере (см.
// backend/app/routers/*.py), так что даже прямой запрос в обход
// интерфейса будет отклонён с 403.

export const ROLES = {
  ADMIN: 'admin',
  OPERATOR: 'operator',
  USER: 'user',
};

// Управление сотрудниками, объектами и справочниками (типы уязвимостей,
// меры реагирования) — только администратор.
export const canManageStaff = (role) => role === ROLES.ADMIN;
export const canManageReferenceData = (role) => role === ROLES.ADMIN;

// Оперативные данные (инциденты, уязвимости, журнал реагирования):
// создавать/редактировать может admin и operator, удалять — только admin.
export const canWriteOperationalData = (role) => role === ROLES.ADMIN || role === ROLES.OPERATOR;
export const canDeleteOperationalData = (role) => role === ROLES.ADMIN;

export const isAdmin = (role) => role === ROLES.ADMIN;
