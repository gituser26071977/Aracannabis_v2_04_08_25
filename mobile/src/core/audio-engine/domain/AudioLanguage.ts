/**
 * AudioLanguage — the language of spoken guidance assets.
 *
 * Sprint 10 ships only PT-BR and EN-US. Future sprints may add more
 * via `AudioLanguage` literal extension (the Engine looks up cues in
 * `DEFAULT_CUE_TABLE[language]`).
 */

export type AudioLanguage = 'pt-BR' | 'en-US';

export const AUDIO_LANGUAGES: readonly AudioLanguage[] = ['pt-BR', 'en-US'] as const;

export const isAudioLanguage = (v: unknown): v is AudioLanguage =>
  typeof v === 'string' && (AUDIO_LANGUAGES as readonly string[]).includes(v);

export const DEFAULT_AUDIO_LANGUAGE: AudioLanguage = 'pt-BR';