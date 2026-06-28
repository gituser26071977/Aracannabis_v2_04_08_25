/**
 * BrowserWallClock — implementação padrão de WallClock.
 *
 * Usa `Date.now()` para timestamp Unix epoch e `new Date().toISOString()`
 * para ISO 8601. Disponível em qualquer runtime JavaScript moderno.
 */

import type { WallClock } from '../domain';

export const createBrowserWallClock = (): WallClock => {
  return {
    now: (): number => Date.now(),
    isoNow: (): string => new Date().toISOString(),
  };
};
