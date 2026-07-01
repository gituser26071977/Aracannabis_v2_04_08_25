/**
 * Clinical MVP — Protocol catalog.
 *
 * Three clinical-grade breathing protocols exposed to the single
 * clinical screen. Each entry carries:
 *   - the i18n key (under `protocols.*` in pt-BR / en-US)
 *   - a stable id matching the JSON's ProtocolId
 *   - the JSON source string (ready for `JsonSource()`)
 *   - approximate total duration (precomputed for UI hints)
 *
 * No new protocols can be added without an explicit follow-up
 * sprint (per the brief: "Nenhum outro protocolo.").
 */

import boxProtocol from './box-4-4-4-4.json';
import diaphragmaticProtocol from './diaphragmatic-breathing.json';
import physiologicalSighProtocol from './physiological-sigh.json';

export type ProtocolI18nKey = 'diaphragmatic' | 'box_4_4_4_4' | 'physiological_sigh';

export interface ClinicalProtocolEntry {
  readonly i18nKey: ProtocolI18nKey;
  readonly id: string;
  readonly title: string;
  readonly source: string;
  readonly approxDurationMs: number;
}

/**
 * 6 cycles × (4000 + 4000 + 6000) = 84_000 ms.
 */
const DIAPHRAGMATIC_DURATION_MS = 6 * (4000 + 4000 + 6000);

/**
 * 6 cycles × (4000 + 4000 + 4000 + 4000) = 96_000 ms.
 */
const BOX_DURATION_MS = 6 * (4000 + 4000 + 4000 + 4000);

/**
 * 8 cycles × (2000 + 500 + 6000) = 68_000 ms.
 */
const PHYSIOLOGICAL_SIGH_DURATION_MS = 8 * (2000 + 500 + 6000);

export const CLINICAL_PROTOCOLS: readonly ClinicalProtocolEntry[] = Object.freeze([
  {
    i18nKey: 'diaphragmatic',
    id: '01ARZ3NDEKTSV4RRFFQ69G5FA2',
    title: 'Respiração Diafragmática',
    source: JSON.stringify(diaphragmaticProtocol),
    approxDurationMs: DIAPHRAGMATIC_DURATION_MS,
  },
  {
    i18nKey: 'box_4_4_4_4',
    id: '01ARZ3NDEKTSV4RRFFQ69G5FBX',
    title: 'Respiração Quadrada 4-4-4-4',
    source: JSON.stringify(boxProtocol),
    approxDurationMs: BOX_DURATION_MS,
  },
  {
    i18nKey: 'physiological_sigh',
    id: '01ARZ3NDEKTSV4RRFFQ69G5PHY',
    title: 'Suspiro Fisiológico',
    source: JSON.stringify(physiologicalSighProtocol),
    approxDurationMs: PHYSIOLOGICAL_SIGH_DURATION_MS,
  },
]);

export const DEFAULT_CLINICAL_PROTOCOL: ClinicalProtocolEntry = CLINICAL_PROTOCOLS[0]!;

export const findClinicalProtocol = (id: string): ClinicalProtocolEntry | null => {
  for (const p of CLINICAL_PROTOCOLS) {
    if (p.id === id) {
      return p;
    }
  }
  return null;
};
