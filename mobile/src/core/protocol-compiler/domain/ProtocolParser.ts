/**
 * ProtocolParser — interface for converting a ProtocolSource into a
 * structurally-valid ProtocolDocument.
 *
 * Implementations:
 *   - JsonProtocolParser (Sprint 3)
 *   - YamlProtocolParser (future)
 *   - VisualEditorParser (future — drag-and-drop GUI output)
 *   - AflDslParser (future — AraFlow DSL)
 *
 * All implementations must:
 *   - Be pure functions (no I/O, no mutation)
 *   - Return Result<ProtocolDocument, ValidationError> for typed errors
 *   - Never throw for expected failures (only for programmer errors)
 */

import type { ProtocolSource, ProtocolSourceFormat } from './ProtocolSource';
import type { ProtocolDocument } from './ProtocolDocument';
import type { Result } from '@araflow/shared-contracts';
import type { ValidationError } from '@araflow/shared-contracts';

/**
 * Parser capabilities advertised by an implementation.
 *
 * Used by the compiler to choose the right parser and by tooling to
 * report which formats are supported at runtime.
 */
export interface ParserCapabilities {
  readonly format: ProtocolSourceFormat;
  readonly version: string;
}

/**
 * Parser contract.
 *
 * Implementations should be registered via a registry; the compiler
 * resolves the right parser by format.
 */
export interface ProtocolParser {
  readonly capabilities: ParserCapabilities;
  parse(source: ProtocolSource): Result<ProtocolDocument, ValidationError>;
}

/**
 * A registry of parsers keyed by format.
 *
 * Pure data structure; the compiler instantiates it once and asks
 * for the parser matching a given source format.
 */
export interface ParserRegistry {
  register(parser: ProtocolParser): void;
  resolve(format: ProtocolSourceFormat): ProtocolParser | null;
  available(): readonly ParserCapabilities[];
}

export const createParserRegistry = (): ParserRegistry => {
  const parsers = new Map<ProtocolSourceFormat, ProtocolParser>();
  return Object.freeze({
    register: (parser: ProtocolParser): void => {
      parsers.set(parser.capabilities.format, parser);
    },
    resolve: (format: ProtocolSourceFormat): ProtocolParser | null =>
      parsers.get(format) ?? null,
    available: (): readonly ParserCapabilities[] =>
      Array.from(parsers.values()).map((p) => p.capabilities),
  });
};
