/**
 * AraFlow — health-route plugin tests.
 *
 * Uses Fastify's `.inject()` (no network socket) to assert the response
 * shape and HTTP semantics of `GET /health`.
 */

import Fastify, { type FastifyInstance } from 'fastify';

import { __resetBuildInfoCacheForTests } from '../build-info';
import { healthRoute } from '../health-route';

interface EnvSnapshot {
  ARAFLOW_VERSION: string | undefined;
  GIT_COMMIT: string | undefined;
  BUILD_TIME: string | undefined;
}

const snapshotEnv = (): EnvSnapshot => ({
  ARAFLOW_VERSION: process.env['ARAFLOW_VERSION'],
  GIT_COMMIT: process.env['GIT_COMMIT'],
  BUILD_TIME: process.env['BUILD_TIME'],
});

const restoreEnv = (snap: EnvSnapshot): void => {
  for (const key of Object.keys(snap) as Array<keyof EnvSnapshot>) {
    if (snap[key] === undefined) {
      delete process.env[key];
    } else {
      process.env[key] = snap[key];
    }
  }
};

describe('health-route — GET /health', () => {
  let app: FastifyInstance;
  let env: EnvSnapshot;

  beforeAll(async () => {
    env = snapshotEnv();
    process.env['ARAFLOW_VERSION'] = '1.2.3-test';
    process.env['GIT_COMMIT'] = 'deadbeef';
    process.env['BUILD_TIME'] = '2026-07-01T12:00:00.000Z';
    __resetBuildInfoCacheForTests();

    app = Fastify({ logger: false });
    await app.register(healthRoute);
    await app.ready();
  });

  afterAll(async () => {
    await app.close();
    restoreEnv(env);
    __resetBuildInfoCacheForTests();
  });

  it('returns 200 with the canonical health JSON', async () => {
    const res = await app.inject({ method: 'GET', url: '/health' });
    expect(res.statusCode).toBe(200);
    const body = res.json() as Record<string, unknown>;
    expect(body['status']).toBe('ok');
    expect(body['version']).toBe('1.2.3-test');
    expect(body['commit']).toBe('deadbeef');
    expect(body['build']).toBe('2026-07-01T12:00:00.000Z');
    expect(typeof body['uptime']).toBe('number');
    expect(body['uptime']).toBeGreaterThanOrEqual(0);
  });

  it('uptime is non-decreasing across calls', async () => {
    const first = (await app.inject({ method: 'GET', url: '/health' })).json() as {
      uptime: number;
    };
    // Force a tiny delay by yielding to the event loop.
    await new Promise((r) => setTimeout(r, 5));
    const second = (await app.inject({ method: 'GET', url: '/health' })).json() as {
      uptime: number;
    };
    expect(second.uptime).toBeGreaterThanOrEqual(first.uptime);
  });

  it('returns JSON content-type', async () => {
    const res = await app.inject({ method: 'GET', url: '/health' });
    expect(res.headers['content-type']).toContain('application/json');
  });

  it('does not require any request body', async () => {
    const res = await app.inject({ method: 'GET', url: '/health' });
    expect(res.statusCode).toBe(200);
  });
});
