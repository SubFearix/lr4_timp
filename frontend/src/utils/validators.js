// Общие правила валидации для форм — используются и на регистрации, и в
// генерик-форме сотрудников (EntityCrudPage), чтобы пользователь видел
// понятную причину ошибки ещё до отправки на сервер (сервер всё равно
// проверяет то же самое ещё раз — см. backend/app/schemas.py).

export const PASSWORD_RULES = [
  { id: 'length', label: 'Минимум 8 символов', test: (pwd) => pwd.length >= 8 },
  { id: 'lower', label: 'Хотя бы одна строчная буква (a-z)', test: (pwd) => /[a-z]/.test(pwd) },
  { id: 'upper', label: 'Хотя бы одна заглавная буква (A-Z)', test: (pwd) => /[A-Z]/.test(pwd) },
  { id: 'digit', label: 'Хотя бы одна цифра (0-9)', test: (pwd) => /\d/.test(pwd) },
];

export const validatePasswordStrength = (password) => {
  const pwd = password || '';
  const failed = PASSWORD_RULES.filter((rule) => !rule.test(pwd));
  return failed.length === 0 ? null : 'Пароль не соответствует требованиям ниже';
};

const PHONE_PATTERN = /^\+?[\d\s\-()]+$/;

export const validatePhoneNumber = (value) => {
  const trimmed = (value || '').trim();
  if (!trimmed) return 'Номер телефона обязателен';
  if (!PHONE_PATTERN.test(trimmed)) {
    return 'Телефон может содержать только цифры, пробелы, +, - и скобки';
  }
  const digitCount = (trimmed.match(/\d/g) || []).length;
  if (digitCount < 10 || digitCount > 15) {
    return 'Номер телефона должен содержать от 10 до 15 цифр';
  }
  return null;
};
