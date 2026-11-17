const { createProxyMiddleware } = require('http-proxy-middleware');

// В деве CRA обслуживает фронтенд на :3000, а бэкенд FastAPI поднят на
// :8000. Чтобы axios мог одинаково обращаться к /api/... как в деве, так
// и в проде (за nginx, см. frontend/nginx.conf), здесь тот же принцип:
// префикс /api срезается перед проксированием на реальный бэкенд.
module.exports = function (app) {
  app.use(
    '/api',
    createProxyMiddleware({
      target: process.env.BACKEND_URL || 'http://localhost:8000',
      changeOrigin: true,
      pathRewrite: { '^/api': '' },
    })
  );
};
