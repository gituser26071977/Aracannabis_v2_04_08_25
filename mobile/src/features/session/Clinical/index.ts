/**
 * @features/session/Clinical — Public API.
 *
 * The Clinical MVP: a single end-to-end clinical screen that wires
 * the entire AraFlow Core (Runtime + Animation + Audio + Session
 * Orchestrator + Persistence) without modifying any Core module.
 *
 * Consumers go through this barrel. Internal modules under
 * `./protocols/`, `./feedback/`, and `./ClinicalSession*` are
 * implementation details.
 *
 * Version: 0.1.0
 */

export { ClinicalScreen } from './ClinicalScreen';
export type { ClinicalScreenProps } from './ClinicalScreen';
export { startClinicalSession, CLINICAL_RUNTIME_ID } from './ClinicalSession';
export type { ClinicalSessionOptions } from './ClinicalSession';
export type { ClinicalSessionHandle, ClinicalSessionStatus } from './ClinicalSessionHandle';

// --- Protocols ---
export { CLINICAL_PROTOCOLS, DEFAULT_CLINICAL_PROTOCOL, findClinicalProtocol } from './protocols';
export type { ClinicalProtocolEntry, ProtocolI18nKey } from './protocols';

// --- Feedback ---
export {
  FEELING_AFTER_OPTIONS,
  FEELING_AFTER_EMOJI,
  FEELING_AFTER_LABEL_KEY,
  isFeelingAfter,
} from './feedback/FEELING_AFTER_OPTIONS';
export type { FeelingAfter } from './feedback/FEELING_AFTER_OPTIONS';
export {
  FEEDBACK_STORAGE_PREFIX,
  buildFeedbackKey,
  saveFeedback,
  listFeedback,
  clearAllFeedback,
  isFeedbackRecord,
} from './feedback/FeedbackStorage';
export type { FeedbackRecord, FeedbackEntry } from './feedback/FeedbackStorage';

// --- Version ---
export const CLINICAL_MVP_VERSION = '0.1.0' as const;
