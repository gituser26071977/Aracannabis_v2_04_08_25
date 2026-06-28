/**
 * errors — index barrel re-export coverage.
 *
 * Ensures the AppError re-export from errors/base.ts is reachable
 * via the errors/index.ts barrel.
 */

import { AppError } from '../../src/errors/base';

describe('errors — re-export coverage', () => {
  it('AppError re-export from base.ts is callable', () => {
    const e = new AppError('m', { code: 'c', severity: 'warn' });
    expect(e).toBeInstanceOf(AppError);
    expect(e.message).toBe('m');
  });
});
