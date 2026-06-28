/**
 * Listener — callback de subscriber.
 *
 * Erros lançados pelo listener são capturados e logados mas não
 * interrompem o dispatch para outros listeners.
 */

import type { BreathEvent } from './BreathEvent';

export type BreathListener = (event: BreathEvent) => void;

export type BreathUnsubscribe = () => void;