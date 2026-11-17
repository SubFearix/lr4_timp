import { render, screen } from '@testing-library/react';
import App from './App';

// axios делает реальные HTTP-запросы (например, GET /profile при
// инициализации AuthProvider) — в тестовом окружении jsdom их не
// выполнить, поэтому мокаем модуль axios-клиента целиком.
jest.mock('./api/axios', () => ({
  __esModule: true,
  default: {
    get: jest.fn(() => Promise.reject(new Error('no token in tests'))),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  },
  API_BASE_URL: '/api',
}));

test('неавторизованный пользователь видит форму входа', async () => {
  render(<App />);
  const heading = await screen.findByRole('heading', { name: /вход в систему/i });
  expect(heading).toBeInTheDocument();
});

test('шапка отображает название системы', () => {
  render(<App />);
  expect(screen.getByRole('heading', { level: 1, name: /безопасность образовательного учреждения/i })).toBeInTheDocument();
});
