/**
 * ids.ts — Branded identifier types + constructors.
 *
 * Coverage:
 *   - Brand type exists
 *   - ProtocolId, SessionId, EngineId, TenantId, UserId, PatientId
 *     - valid input → branded value
 *     - empty/non-string → throws AppError
 *     - format mismatch → throws AppError
 */

import {
  Brand,
  ProtocolId,
  SessionId,
  EngineId,
  TenantId,
  UserId,
  PatientId,
} from '../../src/value-objects/ids';

const VALID_ULID = '01ARZ3NDEKTSV4RRFFQ69G5FAV';

describe('value-objects/ids', () => {
  describe('Brand type', () => {
    it('is exported as a type', () => {
      // Compile-time check that Brand works as a branded type
      const branded: Brand<string, 'Test'> = 'hello' as Brand<string, 'Test'>;
      expect(typeof branded).toBe('string');
    });
  });

  describe('ProtocolId', () => {
    it('accepts valid ULID', () => {
      const id = ProtocolId(VALID_ULID);
      expect(id).toBe(VALID_ULID);
      expect(typeof id).toBe('string');
    });
    it('rejects empty string', () => {
      expect(() => ProtocolId('')).toThrow(/Invalid ProtocolId/);
    });
    it('rejects non-ULID format', () => {
      expect(() => ProtocolId('not-a-ulid')).toThrow(/Invalid ProtocolId/);
      expect(() => ProtocolId('01ARZ3NDEKTSV4RRFFQ69G5FA')).toThrow(/Invalid ProtocolId/); // 25 chars
    });
    it('error has correct code and severity', () => {
      try {
        ProtocolId('bad');
        fail('Expected throw');
      } catch (e) {
        expect((e as { code: string }).code).toBe('invalid_protocol_id');
        expect((e as { severity: string }).severity).toBe('warn');
      }
    });
  });

  describe('SessionId', () => {
    it('accepts valid ULID', () => {
      expect(SessionId(VALID_ULID)).toBe(VALID_ULID);
    });
    it('rejects empty', () => {
      expect(() => SessionId('')).toThrow(/Invalid SessionId/);
    });
    it('rejects invalid format', () => {
      expect(() => SessionId('x')).toThrow(/Invalid SessionId/);
    });
    it('error code is invalid_session_id', () => {
      try {
        SessionId('bad');
        fail('Expected throw');
      } catch (e) {
        expect((e as { code: string }).code).toBe('invalid_session_id');
      }
    });
  });

  describe('EngineId', () => {
    it('accepts valid kebab-case ids', () => {
      expect(EngineId('timer-engine')).toBe('timer-engine');
      expect(EngineId('breath-engine')).toBe('breath-engine');
      expect(EngineId('protocol-engine-v2')).toBe('protocol-engine-v2');
      expect(EngineId('a1')).toBe('a1');
      expect(EngineId('ab')).toBe('ab');
    });
    it('rejects empty string', () => {
      expect(() => EngineId('')).toThrow(/Invalid EngineId/);
    });
    it('rejects ids starting with non-letter', () => {
      expect(() => EngineId('1-engine')).toThrow(/Invalid EngineId/);
      expect(() => EngineId('-engine')).toThrow(/Invalid EngineId/);
    });
    it('rejects ids with uppercase', () => {
      expect(() => EngineId('Timer-Engine')).toThrow(/Invalid EngineId/);
    });
    it('rejects ids ending with hyphen', () => {
      expect(() => EngineId('engine-')).toThrow(/Invalid EngineId/);
    });
    it('error code is invalid_engine_id', () => {
      try {
        EngineId('Bad');
        fail('Expected throw');
      } catch (e) {
        expect((e as { code: string }).code).toBe('invalid_engine_id');
      }
    });
  });

  describe('TenantId', () => {
    it('accepts valid ULID', () => {
      expect(TenantId(VALID_ULID)).toBe(VALID_ULID);
    });
    it('rejects empty', () => {
      expect(() => TenantId('')).toThrow(/Invalid TenantId/);
    });
    it('error code is invalid_tenant_id', () => {
      try {
        TenantId('x');
        fail('Expected throw');
      } catch (e) {
        expect((e as { code: string }).code).toBe('invalid_tenant_id');
      }
    });
  });

  describe('UserId', () => {
    it('accepts valid ULID', () => {
      expect(UserId(VALID_ULID)).toBe(VALID_ULID);
    });
    it('rejects empty', () => {
      expect(() => UserId('')).toThrow(/Invalid UserId/);
    });
    it('error code is invalid_user_id', () => {
      try {
        UserId('x');
        fail('Expected throw');
      } catch (e) {
        expect((e as { code: string }).code).toBe('invalid_user_id');
      }
    });
  });

  describe('PatientId', () => {
    it('accepts valid ULID', () => {
      expect(PatientId(VALID_ULID)).toBe(VALID_ULID);
    });
    it('rejects empty', () => {
      expect(() => PatientId('')).toThrow(/Invalid PatientId/);
    });
    it('error code is invalid_patient_id', () => {
      try {
        PatientId('x');
        fail('Expected throw');
      } catch (e) {
        expect((e as { code: string }).code).toBe('invalid_patient_id');
      }
    });
  });
});
