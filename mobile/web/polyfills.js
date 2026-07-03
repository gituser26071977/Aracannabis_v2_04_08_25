/**
 * AraFlow — Web polyfills.
 *
 * React Native modules assume Node-style globals (`process`, `Buffer`,
 * `events.EventEmitter`) that the browser does not provide. We polyfill
 * them once here so every subsequent import works without modification.
 *
 * Order matters: `process` must be installed before any RN module that
 * reads `process.env` at top level.
 */

import { Buffer } from 'buffer';

import process from 'process/browser';

// `window.process` is what react-native-web looks for first.
if (typeof window !== 'undefined') {
  window.Buffer = window.Buffer ?? Buffer;
  window.process = window.process ?? process;
}

// Provide an EventEmitter shim via the standard `events` package.
if (typeof window !== 'undefined' && !window.EventEmitter) {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const { EventEmitter } = require('events');
  window.EventEmitter = EventEmitter;
}
