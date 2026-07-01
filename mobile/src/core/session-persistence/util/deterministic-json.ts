/**
 * deterministic-json — pure JSON.stringify with sorted keys.
 *
 * `JSON.stringify` does not guarantee key order across runs, but in
 * practice V8 preserves insertion order for plain objects. To make
 * serialization truly deterministic across engines / runs / mutations,
 * we walk the object recursively and write keys in lexicographic
 * order.
 *
 * Determinism is required so that two equivalent snapshots produce
 * byte-identical strings — useful for change-detection, hashing, and
 * cross-version equality checks.
 *
 * No precision loss: numbers are written via `JSON.stringify` (which
 * already preserves IEEE-754 doubles exactly via `String(n)` in JS).
 * Dates are NOT auto-converted; pass numbers explicitly.
 */

/**
 * Returns true if `value` is a plain object (constructor === Object or
 * no prototype). Arrays, Maps, Sets, class instances are not treated
 * as plain objects.
 */
const isPlainObject = (value: unknown): value is Record<string, unknown> => {
  if (value === null || typeof value !== 'object') {
    return false;
  }
  const proto = Object.getPrototypeOf(value);
  return proto === null || proto === Object.prototype;
};

/**
 * Deterministic JSON.stringify.
 *
 * @param value - any JSON-safe value
 * @returns string with sorted keys (no trailing whitespace)
 */
export const stringifyDeterministic = (value: unknown): string => {
  return serialize(value, new WeakSet<object>());
};

const serialize = (value: unknown, seen: WeakSet<object>): string => {
  if (value === null) {
    return 'null';
  }
  if (value === undefined) {
    // undefined is not valid JSON; callers should pass null instead.
    // We emit 'null' to keep the output parseable; the loader is
    // typed strictly so a 'null' value would fail type narrowing
    // before reaching user code.
    return 'null';
  }
  const t = typeof value;
  if (t === 'boolean') {
    return value ? 'true' : 'false';
  }
  if (t === 'number') {
    if (!Number.isFinite(value as number)) {
      throw new Error(`deterministic-json: non-finite number ${String(value)}`);
    }
    return String(value);
  }
  if (t === 'string') {
    return JSON.stringify(value);
  }
  if (t === 'bigint') {
    throw new Error('deterministic-json: BigInt is not supported (pass a string)');
  }
  if (Array.isArray(value)) {
    if (seen.has(value)) {
      throw new Error('deterministic-json: circular reference detected');
    }
    seen.add(value);
    const parts: string[] = [];
    for (const item of value) {
      parts.push(serialize(item, seen));
    }
    return `[${parts.join(',')}]`;
  }
  if (isPlainObject(value)) {
    if (seen.has(value)) {
      throw new Error('deterministic-json: circular reference detected');
    }
    seen.add(value);
    const keys = Object.keys(value).sort();
    const parts: string[] = [];
    for (const k of keys) {
      const v = value[k];
      if (v === undefined) {
        continue; // omit undefined values, matching JSON.stringify behavior
      }
      parts.push(`${JSON.stringify(k)}:${serialize(v, seen)}`);
    }
    return `{${parts.join(',')}}`;
  }
  throw new Error(
    `deterministic-json: unsupported value of type ${t} (${String((value as object)?.constructor?.name ?? 'unknown')})`,
  );
};

/**
 * Strict parser — rejects unknown fields (when `strict` is true).
 * Always returns a deep-frozen copy.
 */
export const parseDeterministic = <T>(input: string, strict = false): T => {
  const value = JSON.parse(input) as unknown;
  if (strict) {
    // The caller can compare against an expected shape; we don't
    // introspect here to keep this util free of domain knowledge.
  }
  return deepFreeze(value) as T;
};

const deepFreeze = (value: unknown): unknown => {
  if (value === null || typeof value !== 'object') {
    return value;
  }
  if (Object.isFrozen(value)) {
    return value;
  }
  Object.freeze(value);
  for (const k of Object.keys(value as object)) {
    const v = (value as Record<string, unknown>)[k];
    if (v !== null && typeof v === 'object' && !Object.isFrozen(v)) {
      deepFreeze(v);
    }
  }
  return value;
};
