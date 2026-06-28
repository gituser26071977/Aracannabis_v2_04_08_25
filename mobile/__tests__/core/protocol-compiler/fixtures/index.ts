/**
 * Test fixtures — canonical protocol documents used across tests.
 *
 * Each fixture returns a fresh object; do not share mutable references
 * across tests.
 */

import type { ProtocolDocument } from '../../../../src/core/protocol-compiler/domain/ProtocolDocument';
import { ProtocolId } from '@araflow/shared-contracts';

/**
 * Minimal valid protocol — the smallest possible document that passes
 * all schema, semantic, and compatibility validation.
 */
export const minimalValidProtocol = (): ProtocolDocument => ({
  $schema: 'https://araflow.app/schemas/protocol/v1.json',
  id: ProtocolId('01ARZ3NDEKTSV4RRFFQ69G5FAV'),
  version: '1.0.0' as never,
  title: 'Minimal Protocol',
  breath: {
    cycles: 1,
    phases: [
      { type: 'inhale', durationMs: 4000 },
      { type: 'exhale', durationMs: 4000 },
    ],
  },
});

/**
 * Standard 4-7-8 protocol — well-known breathwork pattern.
 */
export const fourSevenEightProtocol = (): ProtocolDocument => ({
  $schema: 'https://araflow.app/schemas/protocol/v1.json',
  id: ProtocolId('01ARZ3NDEKTSV4RRFFQ69G5FAV'),
  version: '1.0.0' as never,
  title: '4-7-8 Relaxation',
  description: 'Classic relaxing breath pattern',
  breath: {
    cycles: 4,
    restBetweenCyclesMs: 1000,
    phases: [
      { type: 'inhale', durationMs: 4000, curve: 'ease-in-out' },
      { type: 'hold-in', durationMs: 7000, curve: 'linear' },
      { type: 'exhale', durationMs: 8000, curve: 'ease-in-out' },
    ],
  },
  metadata: {
    author: 'Dr. Test',
    language: 'en',
    references: ['https://example.com/study-1'],
    evidenceLevel: 'B',
    contraindications: ['severe respiratory conditions'],
    category: 'calm',
    tags: ['sleep', 'relaxation'],
    approvedAt: '2026-01-15T10:00:00.000Z' as never,
  },
});

/**
 * Full metadata protocol — exercises every metadata field.
 */
export const fullMetadataProtocol = (): ProtocolDocument => ({
  $schema: 'https://araflow.app/schemas/protocol/v1.json',
  id: ProtocolId('01BRZ3NDEKTSV4RRFFQ69G5FAV'),
  version: '1.0.0' as never,
  title: 'Full Metadata Demo',
  subtitle: 'Subtitle',
  description: 'A complete protocol with all metadata fields',
  breath: {
    cycles: 3,
    phases: [
      { type: 'inhale', durationMs: 2000, curve: 'ease-in' },
      { type: 'hold-in', durationMs: 1000 },
      { type: 'exhale', durationMs: 3000, curve: 'ease-out' },
      { type: 'hold-out', durationMs: 500 },
    ],
  },
  metadata: {
    author: 'Author Name',
    language: 'pt-BR',
    references: ['https://pubmed.ncbi.nlm.nih.gov/12345', 'doi:10.1000/xyz123'],
    evidenceLevel: 'A',
    contraindications: ['none'],
    category: 'wellness',
    tags: ['focus', 'energy'],
    approvedAt: '2026-06-01T00:00:00.000Z' as never,
  },
});

/**
 * Invalid protocol — empty phases (will fail schema validation).
 */
export const emptyPhasesProtocol = (): ProtocolDocument => ({
  $schema: 'https://araflow.app/schemas/protocol/v1.json',
  id: ProtocolId('01ARZ3NDEKTSV4RRFFQ69G5FAV'),
  version: '1.0.0' as never,
  title: 'Empty Phases',
  breath: {
    cycles: 1,
    phases: [],
  },
});

/**
 * Invalid protocol — phase too short.
 */
export const tooShortPhaseProtocol = (): ProtocolDocument => ({
  $schema: 'https://araflow.app/schemas/protocol/v1.json',
  id: ProtocolId('01ARZ3NDEKTSV4RRFFQ69G5FAV'),
  version: '1.0.0' as never,
  title: 'Too Short Phase',
  breath: {
    cycles: 1,
    phases: [
      { type: 'inhale', durationMs: 50 },
      { type: 'exhale', durationMs: 4000 },
    ],
  },
});

/**
 * Invalid protocol — too many cycles.
 */
export const tooManyCyclesProtocol = (): ProtocolDocument => {
  const phases = [
    { type: 'inhale' as const, durationMs: 1000 },
    { type: 'exhale' as const, durationMs: 1000 },
  ];
  return {
    $schema: 'https://araflow.app/schemas/protocol/v1.json',
    id: ProtocolId('01ARZ3NDEKTSV4RRFFQ69G5FAV'),
    version: '1.0.0' as never,
    title: 'Too Many Cycles',
    breath: { cycles: 200, phases },
  };
};

/**
 * Invalid JSON source string for parser tests.
 */
export const invalidJsonSource = '{"not": "valid":}';

export const validJsonSource = JSON.stringify({
  $schema: 'https://araflow.app/schemas/protocol/v1.json',
  id: '01ARZ3NDEKTSV4RRFFQ69G5FAV',
  version: '1.0.0',
  title: 'JSON Source',
  breath: {
    cycles: 1,
    phases: [
      { type: 'inhale', durationMs: 4000 },
      { type: 'exhale', durationMs: 4000 },
    ],
  },
});