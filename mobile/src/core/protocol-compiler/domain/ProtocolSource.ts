/**
 * ProtocolSource — raw, unparsed source fed to the compiler.
 *
 * The compiler accepts a `ProtocolSource` (format + raw bytes) and
 * produces either a `ProtocolDocument` (parsed + structurally valid)
 * or a typed error.
 *
 * The source is intentionally format-agnostic at this level. The
 * parser handles format-specific concerns (JSON.parse, YAML, etc.).
 */

/**
 * ProtocolSourceFormat — supported source formats.
 *
 * Sprint 3 only implements `json`. The compiler is designed so that
 * future formats can be added without changing the pipeline.
 */
export type ProtocolSourceFormat = 'json';

/**
 * Raw protocol source — bytes + format + provenance.
 *
 * `origin` is optional metadata (e.g., "filesystem", "embedded",
 * "https://...") used for diagnostics and checksums, never for logic.
 *
 * `fetchedAt` is the wall-clock time the source was acquired; the
 * compiler uses it only for logs and the `compiledAt` derivation.
 */
export interface ProtocolSource {
  readonly format: ProtocolSourceFormat;
  readonly raw: string;
  readonly origin?: string;
  readonly fetchedAt?: string;
}

/**
 * Constructs a ProtocolSource from a JSON string.
 */
export const JsonSource = (
  raw: string,
  origin?: string,
): ProtocolSource => {
  const base: ProtocolSource = { format: 'json', raw };
  return origin !== undefined ? { ...base, origin } : base;
};

/**
 * Type guard for ProtocolSource shape.
 */
export const isProtocolSource = (v: unknown): v is ProtocolSource =>
  typeof v === 'object' &&
  v !== null &&
  typeof (v as { format?: unknown }).format === 'string' &&
  typeof (v as { raw?: unknown }).raw === 'string';
