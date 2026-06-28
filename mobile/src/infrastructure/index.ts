/**
 * Infrastructure — barrel.
 *
 * All concrete adapters (HTTP, persistence, audio, haptics,
 * biometrics, crash, analytics) are declared here as interfaces.
 * Implementations are registered with the DI container at app
 * bootstrap.
 */

export * from './api';
export * from './persistence';
export * from './audio';
export * from './haptics';
export * from './biometrics';
export * from './crash';
export * from './analytics';
export * from './config';
export * from './feature-flags';
export * from './logging';
export * from './di';
