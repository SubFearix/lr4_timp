export const getErrorMessage = (error) => {
  if (!error) return 'Неизвестная ошибка';

  if (error.response) {
    const { data, status } = error.response;
    const detail = data?.detail;

    if (typeof detail === 'string') {
      return detail;
    }
    if (Array.isArray(detail)) {
      return detail
        .map((item) => {
          const field = Array.isArray(item.loc) ? item.loc[item.loc.length - 1] : '';
          return field ? `${field}: ${item.msg}` : item.msg;
        })
        .join('; ');
    }
    return `Ошибка сервера (${status})`;
  }

  if (error.request) {
    return 'Не удалось связаться с сервером. Проверьте подключение.';
  }

  return error.message || 'Произошла ошибка при отправке запроса.';
};
