/**
 * Protocol contract — representação canônica de um protocolo de respiração.
 *
 * Este arquivo define o SCHEMA canônico. Implementações (Zod, JSON Schema,
 * Protobuf) ficam em arquivos adjacentes.
 */

import { z } from 'zod';

import { ProtocolId, ProtocolVersion } from '../common';

/**
 * Tipos de fase de respiração suportados.
 * Mapeamento para o Breath Engine no mobile.
 */
export const BreathPhaseTypeSchema = z.enum([
  'inhale',
  'hold-in',
  'exhale',
  'hold-out',
]);
export type BreathPhaseType = z.infer<typeof BreathPhaseTypeSchema>;

/**
 * Curvas de easing aplicadas à progressão de uma fase.
 * `linear` é fallback; demais são cubic-bezier.
 */
export const EasingCurveSchema = z.enum([
  'linear',
  'ease-in',
  'ease-out',
  'ease-in-out',
]);
export type EasingCurve = z.infer<typeof EasingCurveSchema>;

/**
 * Nível de evidência científica do protocolo (GRADE-like).
 */
export const EvidenceLevelSchema = z.enum(['A', 'B', 'C', 'D']);
export type EvidenceLevel = z.infer<typeof EvidenceLevelSchema>;

/**
 * Schema de uma fase individual.
 */
export const BreathPhaseSchema = z.object({
  type: BreathPhaseTypeSchema,
  durationMs: z.number().int().positive().max(60_000),
  curve: EasingCurveSchema.default('ease-in-out'),
});
export type BreathPhase = z.infer<typeof BreathPhaseSchema>;

/**
 * Schema de configuração de áudio do protocolo.
 */
export const ProtocolAudioSchema = z.object({
  introVoiceId: z.string().min(1).optional(),
  cueVoiceId: z.string().min(1).optional(),
  ambientTrackId: z.string().min(1).optional(),
  volumeCurve: z.enum(['constant', 'fade-in', 'fade-out', 'fade-in-out']).default('constant'),
  enableEndCue: z.boolean().default(true),
});
export type ProtocolAudio = z.infer<typeof ProtocolAudioSchema>;

/**
 * Schema de configuração de animação.
 */
export const ProtocolAnimationSchema = z.object({
  shape: z.enum(['circle', 'wave', 'square']).default('circle'),
  color: z.string().regex(/^#[0-9A-Fa-f]{6}$/).optional(),
  showPhaseLabel: z.boolean().default(true),
  showCountdown: z.boolean().default(true),
});
export type ProtocolAnimation = z.infer<typeof ProtocolAnimationSchema>;

/**
 * Schema completo de um protocolo de respiração.
 */
export const ProtocolSchema = z.object({
  id: z.string().min(1).transform((s) => s as ProtocolId),
  version: z.string().regex(/^\d+\.\d+\.\d+$/).transform((s) => s as ProtocolVersion),
  title: z.string().min(1).max(100),
  subtitle: z.string().max(200).optional(),
  description: z.string().max(1000).optional(),
  evidenceLevel: EvidenceLevelSchema,
  evidenceRefs: z.array(z.string()).default([]),
  durationMs: z.number().int().positive(),
  cycles: z.number().int().positive().max(100),
  restBetweenCyclesMs: z.number().int().nonnegative().default(0),
  phases: z.array(BreathPhaseSchema).min(1),
  audio: ProtocolAudioSchema.default({}),
  animation: ProtocolAnimationSchema.default({}),
  contraindications: z.array(z.string()).default([]),
  preconditions: z
    .object({
      minAge: z.number().int().nonnegative().optional(),
      maxAge: z.number().int().positive().optional(),
      excludeConditions: z.array(z.string()).default([]),
    })
    .default({ excludeConditions: [] }),
  metadata: z
    .object({
      author: z.string().min(1),
      approvedAt: z.string().datetime(),
      tags: z.array(z.string()).default([]),
    }),
});
export type Protocol = z.infer<typeof ProtocolSchema>;

/**
 * Snapshot imutável usado para validar versionamento semântico.
 */
export const PROTOCOL_SCHEMA_VERSION = '1.0.0' as const;
