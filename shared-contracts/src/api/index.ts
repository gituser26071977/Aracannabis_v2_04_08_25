/**
 * API contract — tipos de request/response compartilhados.
 *
 * Estes tipos definem o CONTRATO. Endpoints e implementação vivem no backend.
 */

import { z } from 'zod';

import {
  Iso8601,
  PatientId,
  ProtocolId,
  ProtocolVersion,
  SessionId,
  TenantId,
  UserId,
} from '../common';

/**
 * DTO de uma sessão completa (post-session).
 */
export const SessionDtoSchema = z.object({
  id: z.string().transform((s) => s as SessionId),
  patientId: z.string().transform((p) => p as PatientId).nullable(),
  protocolId: z.string().transform((p) => p as ProtocolId),
  protocolVersion: z.string().transform((v) => v as ProtocolVersion),
  startedAt: z.string().datetime().transform((s) => s as Iso8601),
  endedAt: z.string().datetime().transform((s) => s as Iso8601).nullable(),
  durationMs: z.number().int().nonnegative(),
  status: z.enum(['completed', 'cancelled', 'interrupted']),
  completedCycles: z.number().int().nonnegative(),
  preMood: z.number().int().min(1).max(5).optional(),
  postMood: z.number().int().min(1).max(5).optional(),
  preEnergy: z.number().int().min(1).max(5).optional(),
  postEnergy: z.number().int().min(1).max(5).optional(),
  deviceInfo: z.record(z.string(), z.string()).optional(),
  appVersion: z.string().optional(),
  tenantId: z.string().transform((t) => t as TenantId),
});
export type SessionDto = z.infer<typeof SessionDtoSchema>;

/**
 * Request de criação de sessão (apenas no MVP Wellness, sessões são
 * locais; sync é offline-first com este endpoint como destino eventual).
 */
export const CreateSessionRequestSchema = SessionDtoSchema.omit({
  id: true,
});
export type CreateSessionRequest = z.infer<typeof CreateSessionRequestSchema>;

/**
 * Response genérica de API.
 */
export const ApiErrorSchema = z.object({
  code: z.string(),
  message: z.string(),
  details: z.record(z.string(), z.unknown()).optional(),
  traceId: z.string().optional(),
});
export type ApiError = z.infer<typeof ApiErrorSchema>;

export type ApiResponse<T> =
  | { readonly success: true; readonly data: T }
  | { readonly success: false; readonly error: ApiError };

/**
 * Auth — payload de token decodificado.
 */
export const AuthTokenPayloadSchema = z.object({
  sub: z.string().transform((s) => s as UserId),
  tenantId: z.string().transform((t) => t as TenantId),
  iat: z.number().int(),
  exp: z.number().int(),
  scopes: z.array(z.string()),
});
export type AuthTokenPayload = z.infer<typeof AuthTokenPayloadSchema>;
