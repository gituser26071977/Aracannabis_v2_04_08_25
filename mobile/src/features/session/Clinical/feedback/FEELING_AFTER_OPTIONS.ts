/**
 * Clinical MVP — Feedback options.
 *
 * The brief specifies five post-session feeling options, mapped from
 * a 5-point Likert scale to emoji + i18n keys. The order is fixed
 * (worst → best) and the enum is the single source of truth used by
 * the FeedbackStorage and the ClinicalScreen.
 */

export const FEELING_AFTER_OPTIONS = [
  'much-worse',
  'worse',
  'same',
  'better',
  'much-better',
] as const;

export type FeelingAfter = (typeof FEELING_AFTER_OPTIONS)[number];

export const isFeelingAfter = (v: unknown): v is FeelingAfter =>
  typeof v === 'string' && (FEELING_AFTER_OPTIONS as readonly string[]).includes(v);

export const FEELING_AFTER_EMOJI: Readonly<Record<FeelingAfter, string>> = Object.freeze({
  'much-worse': '😟',
  worse: '🙁',
  same: '😐',
  better: '🙂',
  'much-better': '😄',
});

export const FEELING_AFTER_LABEL_KEY: Readonly<Record<FeelingAfter, string>> = Object.freeze({
  'much-worse': 'feedback.feeling.muchWorse',
  worse: 'feedback.feeling.worse',
  same: 'feedback.feeling.same',
  better: 'feedback.feeling.better',
  'much-better': 'feedback.feeling.muchBetter',
});
