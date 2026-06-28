/**
 * Listener — callback de subscriber.
 *
 * Erros lançados pelo listener são capturados e logados mas não
 * interrompem o dispatch para outros listeners.
 */

import type { TimerEvent } from './TimerEvent';

export type TimerListener = (event: TimerEvent) => void;

export type Unsubscribe = () => void;
