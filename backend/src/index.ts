/**
 * AraFlow — Backend entrypoint (RC1).
 *
 * Sprint 0 stub used to only log BACKEND_VERSION. RC1 wires a real
 * Fastify server exposing `GET /health` (liveness + build metadata).
 *
 * The endpoint contract is frozen by `shared/health/health-route.ts`:
 *   { status: 'ok', version, commit, build, uptime }
 *
 * Listens on `process.env.PORT ?? 5005`. The Docker image binds the
 * same port internally; Traefik reaches the container via the
 * `araflow-internal` Docker network (see `docker-compose.araflow.yml`).
 *
 * No external services are contacted by this process — AraFlow is
 * offline-first and the API container exists solely to satisfy the
 * `/health` contract required by the RC1 deployment mission.
 */

import Fastify, { type FastifyInstance, type FastifyServerOptions } from 'fastify';

import { healthRoute } from './shared/health/health-route';

export const BACKEND_VERSION = '1.0.0' as const;

const DEFAULT_PORT = 5005;
const DEFAULT_HOST = '0.0.0.0';

const buildServer = (): FastifyInstance => {
  const isProd = process.env['NODE_ENV'] === 'production';
  const loggerOptions: FastifyServerOptions['logger'] = isProd
    ? { level: process.env['LOG_LEVEL'] ?? 'info' }
    : {
        level: process.env['LOG_LEVEL'] ?? 'info',
        transport: {
          target: 'pino-pretty',
          options: { translateTime: 'HH:MM:ss' },
        },
      };
  const app = Fastify({
    logger: loggerOptions,
    disableRequestLogging: isProd,
  });

  // Health endpoint. Must be registered at root with no prefix so that
  // Traefik's `Path(`/health`)` router matches the request untouched.
  app.register(healthRoute);

  return app;
};

const main = async (): Promise<void> => {
  const port = Number.parseInt(process.env['PORT'] ?? String(DEFAULT_PORT), 10);
  if (Number.isNaN(port) || port <= 0 || port > 65_535) {
    process.stderr.write(`[araflow-api] invalid PORT env: ${String(process.env['PORT'])}\n`);
    process.exit(2);
  }
  const host = process.env['HOST'] ?? DEFAULT_HOST;
  const app = buildServer();
  try {
    await app.listen({ port, host });
    app.log.info(`AraFlow backend ${BACKEND_VERSION} listening on ${host}:${port}`);
  } catch (err) {
    app.log.error({ err }, 'failed to start server');
    process.exit(1);
  }
};

if (require.main === module) {
  void main();
}
