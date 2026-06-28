/**
 * Public API — barrel re-exports.
 *
 * Verifies every public name from shared-contracts is reachable via the
 * top-level index, so downstream packages can rely on a single import path.
 */

import * as API from '../src';

describe('public API (index barrel)', () => {
  describe('Version constant', () => {
    it('exports SHARED_CONTRACTS_VERSION', () => {
      expect(API.SHARED_CONTRACTS_VERSION).toBe('2.5.0');
    });
  });

  describe('Value Objects', () => {
    it('exports validation helpers', () => {
      expect(typeof API.AppError).toBe('function');
      expect(API.ULID_PATTERN).toBeInstanceOf(RegExp);
      expect(API.ISO8601_PATTERN).toBeInstanceOf(RegExp);
      expect(API.SEMVER_PATTERN).toBeInstanceOf(RegExp);
      expect(API.UUID_V4_PATTERN).toBeInstanceOf(RegExp);
      expect(typeof API.isNonEmptyString).toBe('function');
      expect(typeof API.isFiniteNumber).toBe('function');
      expect(typeof API.isInteger).toBe('function');
      expect(typeof API.isInRange).toBe('function');
    });
    it('exports id constructors', () => {
      expect(typeof API.ProtocolId).toBe('function');
      expect(typeof API.SessionId).toBe('function');
      expect(typeof API.EngineId).toBe('function');
      expect(typeof API.TenantId).toBe('function');
      expect(typeof API.UserId).toBe('function');
      expect(typeof API.PatientId).toBe('function');
    });
    it('exports numeric value objects', () => {
      expect(typeof API.Duration).toBe('function');
      expect(typeof API.DurationFromSeconds).toBe('function');
      expect(typeof API.DurationFromMinutes).toBe('function');
      expect(typeof API.DurationZero).toBe('function');
      expect(typeof API.durationToSeconds).toBe('function');
      expect(typeof API.durationToMinutes).toBe('function');
      expect(typeof API.Timestamp).toBe('function');
      expect(typeof API.TimestampNow).toBe('function');
      expect(typeof API.Percentage).toBe('function');
      expect(typeof API.Progress).toBe('function');
      expect(typeof API.ProgressFromPercentage).toBe('function');
      expect(typeof API.CycleIndex).toBe('function');
      expect(typeof API.PhaseIndex).toBe('function');
      expect(typeof API.Iso8601).toBe('function');
      expect(typeof API.Iso8601FromTimestamp).toBe('function');
      expect(typeof API.Iso8601ToTimestamp).toBe('function');
    });
    it('exports semantic version helpers', () => {
      expect(typeof API.SemanticVersion).toBe('function');
      expect(typeof API.parseSemanticVersion).toBe('function');
      expect(typeof API.compareSemanticVersions).toBe('function');
      expect(typeof API.isVersionCompatible).toBe('function');
    });
  });

  describe('Enums', () => {
    it('exports state enums', () => {
      expect(Array.isArray(API.ENGINE_STATES)).toBe(true);
      expect(Array.isArray(API.PROTOCOL_STATES)).toBe(true);
      expect(Array.isArray(API.SESSION_STATES)).toBe(true);
      expect(typeof API.isEngineState).toBe('function');
      expect(typeof API.isProtocolState).toBe('function');
      expect(typeof API.isSessionState).toBe('function');
    });
    it('exports breath enums', () => {
      expect(Array.isArray(API.BREATH_PHASES)).toBe(true);
      expect(Array.isArray(API.CURVE_TYPES)).toBe(true);
      expect(Array.isArray(API.INTERPOLATION_TYPES)).toBe(true);
      expect(typeof API.isBreathPhase).toBe('function');
      expect(typeof API.isCurveType).toBe('function');
      expect(typeof API.isInterpolationType).toBe('function');
    });
    it('exports priority/severity enums', () => {
      expect(Array.isArray(API.PRIORITIES)).toBe(true);
      expect(Array.isArray(API.SEVERITIES)).toBe(true);
      expect(API.PRIORITY_RANK.critical).toBe(5);
      expect(API.SEVERITY_RANK.fatal).toBe(3);
      expect(typeof API.isPriority).toBe('function');
      expect(typeof API.isSeverity).toBe('function');
    });
  });

  describe('Patterns', () => {
    it('exports Result', () => {
      expect(typeof API.Ok).toBe('function');
      expect(typeof API.Err).toBe('function');
      expect(typeof API.isOk).toBe('function');
      expect(typeof API.isErr).toBe('function');
      expect(typeof API.mapResult).toBe('function');
      expect(typeof API.mapError).toBe('function');
      expect(typeof API.flatMapResult).toBe('function');
      expect(typeof API.unwrap).toBe('function');
      expect(typeof API.unwrapOr).toBe('function');
      expect(typeof API.allResults).toBe('function');
    });
    it('exports Option', () => {
      expect(typeof API.Some).toBe('function');
      expect(typeof API.None).toBe('function');
      expect(typeof API.isSome).toBe('function');
      expect(typeof API.isNone).toBe('function');
      expect(typeof API.mapOption).toBe('function');
      expect(typeof API.flatMapOption).toBe('function');
      expect(typeof API.unwrapOptionOr).toBe('function');
      expect(typeof API.zip2).toBe('function');
      expect(typeof API.firstSome).toBe('function');
    });
    it('exports Either', () => {
      expect(typeof API.Left).toBe('function');
      expect(typeof API.Right).toBe('function');
      expect(typeof API.isLeft).toBe('function');
      expect(typeof API.isRight).toBe('function');
      expect(typeof API.mapLeft).toBe('function');
      expect(typeof API.mapRight).toBe('function');
      expect(typeof API.unwrapEither).toBe('function');
    });
    it('exports Failure', () => {
      expect(typeof API.Failure).toBe('function');
      expect(typeof API.isFailure).toBe('function');
      expect(typeof API.groupFailuresBySeverity).toBe('function');
      expect(typeof API.hasBlockingFailures).toBe('function');
    });
  });

  describe('Utilities', () => {
    it('exports UUID and ULID helpers', () => {
      expect(typeof API.generateUuidV4).toBe('function');
      expect(typeof API.validateUuidV4).toBe('function');
      expect(typeof API.generateUlidLike).toBe('function');
    });
    it('exports time-unit helpers', () => {
      expect(Array.isArray(API.TIME_UNITS)).toBe(true);
      expect(typeof API.toMilliseconds).toBe('function');
      expect(typeof API.fromMilliseconds).toBe('function');
      expect(typeof API.isTimeUnit).toBe('function');
    });
  });

  describe('Errors', () => {
    it('exports all typed error classes', () => {
      expect(typeof API.AppError).toBe('function');
      expect(typeof API.ValidationError).toBe('function');
      expect(typeof API.CompilationError).toBe('function');
      expect(typeof API.EngineError).toBe('function');
      expect(typeof API.ProtocolError).toBe('function');
      expect(typeof API.TimerError).toBe('function');
      expect(typeof API.BreathError).toBe('function');
    });
  });

  describe('Events', () => {
    it('exports CANONICAL_EVENT_TYPES tuple', () => {
      expect(API.CANONICAL_EVENT_TYPES).toHaveLength(9);
      expect(API.CANONICAL_EVENT_TYPES[0]).toBe('engine-started');
    });
  });

  describe('End-to-end smoke test', () => {
    it('full pipeline: construct IDs, validate, build event', () => {
      const pid = API.ProtocolId('01ARZ3NDEKTSV4RRFFQ69G5FAV');
      const ver = API.SemanticVersion('1.0.0');
      const dur = API.Duration(2000);
      const iso = API.Iso8601FromTimestamp(API.TimestampNow());
      const ok = API.Ok(pid);
      const evt: API.ProtocolCompiledEvent = {
        type: 'protocol-compiled',
        monotonicMs: 0,
        protocolId: pid,
        version: ver,
        compiledAt: iso,
        totalDuration: dur,
      };
      expect(API.unwrap(ok)).toBe(pid);
      expect(evt.type).toBe('protocol-compiled');
    });
  });
});
