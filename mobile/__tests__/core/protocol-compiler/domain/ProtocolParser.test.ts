/**
 * ProtocolParser — registry tests.
 */

import { createParserRegistry } from '../../../../src/core/protocol-compiler/domain/ProtocolParser';

class FakeJsonParser {
  public readonly capabilities = Object.freeze({ format: 'json' as const, version: '1.0.0' });
  public parse(_src: unknown): { ok: true; value: 'parsed' } {
    return { ok: true, value: 'parsed' };
  }
}

describe('createParserRegistry', () => {
  it('starts empty', () => {
    const reg = createParserRegistry();
    expect(reg.available()).toEqual([]);
    expect(reg.resolve('json')).toBeNull();
  });

  it('registers a parser by format', () => {
    const reg = createParserRegistry();
    const parser = new FakeJsonParser();
    reg.register(parser as never);
    expect(reg.available()).toHaveLength(1);
    expect(reg.resolve('json')).toBe(parser);
  });

  it('overwrites on duplicate registration', () => {
    const reg = createParserRegistry();
    const a = new FakeJsonParser();
    const b = new FakeJsonParser();
    reg.register(a as never);
    reg.register(b as never);
    expect(reg.resolve('json')).toBe(b);
    expect(reg.available()).toHaveLength(1);
  });
});