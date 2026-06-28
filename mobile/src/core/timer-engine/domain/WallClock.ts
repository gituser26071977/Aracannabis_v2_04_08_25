/**
 * WallClock — interface para o relógio civil.
 *
 * `now()` é afetado por mudanças no wall clock (NTP sync, ajustes
 * manuais, DST). Use APENAS para timestamps persistentes e exibição
 * ao usuário. NUNCA para medição de intervalos.
 *
 * `isoNow()` retorna a representação ISO 8601 do instante atual,
 * pronta para serialização em logs e APIs.
 */

export interface WallClock {
  /** Returns milliseconds since Unix epoch (1970-01-01T00:00:00Z). */
  now(): number;

  /** Returns current instant as ISO 8601 string with millisecond precision. */
  isoNow(): string;
}
