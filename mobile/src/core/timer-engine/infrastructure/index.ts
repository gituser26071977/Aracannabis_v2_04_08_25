/**
 * Infrastructure — barrel.
 *
 * Adaptadores platform-agnostic para produção. Todos funcionam em
 * qualquer runtime JavaScript moderno com setTimeout/setInterval
 * e performance.now() (ou fallback para Date.now()).
 */

export { createBrowserMonotonicClock } from './BrowserMonotonicClock';
export { createBrowserWallClock } from './BrowserWallClock';
export {
  createDefaultClockProvider,
  type DefaultClockProviderOptions,
} from './DefaultClockProvider';
