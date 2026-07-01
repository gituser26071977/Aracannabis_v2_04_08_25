/**
 * AudioEngineState — the 7-state FSM that governs AudioEngine lifecycle.
 *
 * Transitions are validated by `canAudioEngineTransition`. The Engine
 * itself never short-circuits — every transition is explicit.
 *
 *   uninitialized → loaded | errored | disposed
 *   loaded        → playing | stopped | disposed
 *   playing       → paused | stopped | errored | disposed
 *   paused        → playing | stopped | disposed
 *   stopped       → loaded | playing | disposed
 *   errored       → loaded | disposed
 *   disposed      → (terminal)
 */

export type AudioEngineState =
  | 'uninitialized'
  | 'loaded'
  | 'playing'
  | 'paused'
  | 'stopped'
  | 'errored'
  | 'disposed';

export const AUDIO_ENGINE_STATES: readonly AudioEngineState[] = [
  'uninitialized',
  'loaded',
  'playing',
  'paused',
  'stopped',
  'errored',
  'disposed',
] as const;

export const TERMINAL_AUDIO_ENGINE_STATES: readonly AudioEngineState[] = ['disposed'] as const;

const LEGAL_TRANSITIONS: Readonly<Record<AudioEngineState, readonly AudioEngineState[]>> = Object.freeze({
  uninitialized: ['loaded', 'errored', 'disposed'],
  loaded: ['loaded', 'playing', 'stopped', 'disposed'],
  playing: ['paused', 'stopped', 'errored', 'disposed'],
  paused: ['playing', 'stopped', 'disposed'],
  stopped: ['loaded', 'playing', 'disposed'],
  errored: ['loaded', 'disposed'],
  disposed: [],
});

export const isAudioEngineState = (v: unknown): v is AudioEngineState =>
  typeof v === 'string' && (AUDIO_ENGINE_STATES as readonly string[]).includes(v);

export const isTerminalAudioEngineState = (state: AudioEngineState): boolean =>
  (TERMINAL_AUDIO_ENGINE_STATES as readonly AudioEngineState[]).includes(state);

export const canAudioEngineTransition = (
  from: AudioEngineState,
  to: AudioEngineState,
): boolean => (LEGAL_TRANSITIONS[from] as readonly AudioEngineState[]).includes(to);

export const labelForAudioEngineState = (state: AudioEngineState): string => {
  switch (state) {
    case 'uninitialized':
      return 'Não inicializado';
    case 'loaded':
      return 'Pronto';
    case 'playing':
      return 'Reproduzindo';
    case 'paused':
      return 'Pausado';
    case 'stopped':
      return 'Parado';
    case 'errored':
      return 'Erro';
    case 'disposed':
      return 'Liberado';
  }
};