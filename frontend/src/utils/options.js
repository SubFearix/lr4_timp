// Статические справочные наборы значений для select-полей. Поля в БД —
// свободный varchar (см. отчёт), но на уровне UI удобнее и надёжнее давать
// пользователю выбор из фиксированного набора, а не текстовое поле.

export const OBJECT_TYPE_OPTIONS = [
  { value: 'Учебный корпус', label: 'Учебный корпус' },
  { value: 'Спортивный зал', label: 'Спортивный зал' },
  { value: 'Столовая', label: 'Столовая' },
  { value: 'Общежитие', label: 'Общежитие' },
  { value: 'Библиотека', label: 'Библиотека' },
  { value: 'Медпункт', label: 'Медпункт' },
  { value: 'КПП', label: 'КПП / проходная' },
  { value: 'Иное', label: 'Иное' },
];

export const STAFF_ROLE_OPTIONS = [
  { value: 'admin', label: 'Администратор системы' },
  { value: 'operator', label: 'Охранник / дежурный' },
  { value: 'user', label: 'Сотрудник учреждения' },
];

// При саморегистрации роль "Администратор" недоступна для выбора —
// backend всё равно её отклонит (кроме самого первого пользователя в
// системе, который становится администратором автоматически), но не
// стоит и предлагать вариант, который приведёт к ошибке.
export const SELF_REGISTER_ROLE_OPTIONS = STAFF_ROLE_OPTIONS.filter((opt) => opt.value !== 'admin');

export const INCIDENT_TYPE_OPTIONS = [
  { value: 'Пожар', label: 'Пожар / возгорание' },
  { value: 'Эвакуация', label: 'Эвакуация / учебная тревога' },
  { value: 'Нарушение доступа', label: 'Нарушение пропускного режима' },
  { value: 'Травма', label: 'Травма / несчастный случай' },
  { value: 'Конфликт', label: 'Конфликт / буллинг' },
  { value: 'Техническая неисправность', label: 'Техническая неисправность' },
  { value: 'Кибератака', label: 'Кибератака' },
  { value: 'Иное', label: 'Иное' },
];

export const INCIDENT_STATE_OPTIONS = [
  { value: 'новый', label: 'Новый' },
  { value: 'в обработке', label: 'В обработке' },
  { value: 'устранён', label: 'Устранён' },
  { value: 'закрыт', label: 'Закрыт' },
];

export const FIX_STATUS_OPTIONS = [
  { value: 'не устранена', label: 'Не устранена' },
  { value: 'в процессе', label: 'В процессе' },
  { value: 'устранена', label: 'Устранена' },
];

export const staffLabel = (staff) =>
  `${staff.surname} ${staff.name}${staff.patronymic ? ' ' + staff.patronymic : ''} (${staff.position})`;

export const objectLabel = (obj) => `${obj.obj_name} (${obj.obj_type})`;
