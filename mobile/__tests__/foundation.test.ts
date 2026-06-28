/**
 * Foundation smoke test.
 *
 * Verifica que os módulos foundation estão importáveis e a estrutura
 * básica está correta. Cada engine/feature ganha seus próprios
 * testes em sprints subsequentes.
 */

import { logger } from '@infrastructure/logging/logger';
import { AppError, NotImplementedError, isAppError } from '@shared/errors';
import { lightTheme, darkTheme, highContrastTheme } from '@shared/theme';
import { LocalFeatureFlagService } from '@infrastructure/feature-flags';
import { StaticRemoteConfigService, REMOTE_CONFIG_SCHEMA } from '@infrastructure/config';
import { Container, createToken } from '@infrastructure/di';

describe('Foundation smoke', () => {
  it('logger is importable and produces a child', () => {
    const child = logger.child({ test: true });
    expect(child).toBeDefined();
    expect(typeof child.info).toBe('function');
  });

  it('AppError taxonomy works', () => {
    const e1 = new NotImplementedError('timer.start');
    expect(e1.code).toBe('not_implemented');
    expect(e1.severity).toBe('warn');
    expect(isAppError(e1)).toBe(true);

    const e2 = new AppError('test', { code: 'test_error' });
    expect(e2.code).toBe('test_error');
    expect(isAppError(e2)).toBe(true);
    expect(isAppError(new Error('plain'))).toBe(false);
  });

  it('all themes are present and well-formed', () => {
    for (const theme of [lightTheme, darkTheme, highContrastTheme]) {
      expect(theme.color.brand.primary).toMatch(/^#[0-9A-Fa-f]{6}$/);
      expect(theme.spacing.md).toBeGreaterThan(0);
      expect(theme.radius.md).toBeGreaterThanOrEqual(0);
      expect(theme.typography.size.body).toBeGreaterThan(0);
    }
  });

  it('feature flags default to false', () => {
    const svc = new LocalFeatureFlagService();
    expect(svc.isEnabled('nonexistent', { userId: 'u1' })).toBe(false);
  });

  it('remote config returns schema defaults', () => {
    const cfg = new StaticRemoteConfigService();
    expect(cfg.getNumber('safety.max_session_ms')).toBe(30 * 60 * 1000);
    expect(cfg.getString('feature.onboarding.copy_locale')).toBe('pt-BR');
    expect(cfg.getBoolean('feature.experimental.haptics')).toBe(false);
    expect(Object.keys(REMOTE_CONFIG_SCHEMA).length).toBeGreaterThan(0);
  });

  it('DI container resolves and singletonizes', () => {
    const c = new Container();
    const TOKEN = createToken<{ id: string }>('thing');
    let counter = 0;
    c.register(TOKEN, () => ({ id: `instance-${(counter += 1)}` }));
    const a = c.resolve(TOKEN);
    const b = c.resolve(TOKEN);
    expect(a).toBe(b);
    expect(a.id).toBe('instance-1');
  });

  it('DI container distinguishes factory from singleton', () => {
    const c = new Container();
    const TOKEN = createToken<{ id: string }>('thing');
    c.registerFactory(TOKEN, () => ({ id: Math.random().toString() }));
    const a = c.resolve(TOKEN);
    const b = c.resolve(TOKEN);
    expect(a).not.toBe(b);
  });
});
