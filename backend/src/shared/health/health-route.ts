/**
 * AraFlow — Health route plugin (Fastify).
 *
 * Registers `GET /health` returning:
 *
 *   {
 *     "status": "ok",
 *     "version": "<backend/package.json#version | ARAFLOW_VERSION>",
 *     "commit":  "<GIT_COMMIT | /app/COMMIT | 'unknown'>",
 *     "build":   "<BUILD_TIME | process start ISO>",
 *     "uptime":  <process.uptime(), seconds, float>
 *   }
 *
 * The route is intentionally side-effect free and constant-time. It does
 * not check downstream services (no DB, no Redis, no LLM gateway) because
 * AraFlow is offline-first and has no backend dependencies to probe.
 *
 * The `/health` endpoint is excluded from tenant middleware in the
 * AraOS Flask app (`tenant/middleware.py:61`) — we mirror that pattern
 * here by mounting the route at the root path with no prefix.
 */

import type { FastifyInstance, FastifyPluginAsync } from 'fastify';

import { getBuildInfo } from './build-info';

export interface HealthResponse {
  readonly status: 'ok';
  readonly version: string;
  readonly commit: string;
  readonly build: string;
  readonly uptime: number;
}

export const healthRoute: FastifyPluginAsync = async (app: FastifyInstance): Promise<void> => {
  app.get('/health', async (): Promise<HealthResponse> => {
    const info = getBuildInfo();
    return {
      status: 'ok',
      version: info.version,
      commit: info.commit,
      build: info.build,
      uptime: process.uptime(),
    };
  });
};
