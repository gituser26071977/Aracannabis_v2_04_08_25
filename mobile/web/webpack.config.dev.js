/**
 * AraFlow — Webpack dev-server configuration.
 *
 * Extends the base config with webpack-dev-server options for local
 * `npm run web:dev` usage. Listens on `127.0.0.1:8080` and proxies
 * `/health` to the Fastify API on `127.0.0.1:5005` so the web bundle
 * can call the RC1 health endpoint without CORS pain during dev.
 */

const base = require('./webpack.config.js');

module.exports = (env, argv) => {
  const cfg = base(env, argv);
  return {
    ...cfg,
    devServer: {
      host: '127.0.0.1',
      port: 8080,
      historyApiFallback: true,
      hot: true,
      open: false,
      allowedHosts: 'all',
      client: {
        overlay: { errors: true, warnings: false },
      },
      proxy: [
        {
          context: ['/health'],
          target: 'http://127.0.0.1:5005',
          changeOrigin: false,
        },
      ],
    },
  };
};
