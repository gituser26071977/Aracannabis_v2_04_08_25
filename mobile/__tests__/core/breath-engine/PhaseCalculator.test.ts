/**
 * PhaseCalculator — unit tests for pure phase computation.
 */

import {
  computePhaseInfo,
  DEFAULT_BREATH_CYCLE_CONFIG,
} from '@core/breath-engine';

const BOX_CONFIG = {
  inhaleMs: 4_000,
  holdAfterInhaleMs: 4_000,
  exhaleMs: 4_000,
  holdAfterExhaleMs: 4_000,
  cycles: 3,
};

describe('PhaseCalculator — preparation phase', () => {
  const configWithPrep = { ...BOX_CONFIG, prepMs: 5_000 };

  test('returns "preparing" before prepMs elapses', () => {
    const info = computePhaseInfo(configWithPrep, 1_000);
    expect(info.activity).toBe('preparing');
    expect(info.phase).toBeNull();
    expect(info.cycleIndex).toBe(0);
    expect(info.phaseProgress).toBeCloseTo(0.2, 5);
  });

  test('prep phase ends exactly at prepMs', () => {
    const info = computePhaseInfo(configWithPrep, 5_000);
    expect(info.activity).toBe('active');
    expect(info.phase).toBe('inhaling');
    expect(info.phaseProgress).toBe(0);
    expect(info.cycleIndex).toBe(0);
  });

  test('prep phase without prepMs config skips preparing', () => {
    const info = computePhaseInfo(BOX_CONFIG, 0);
    expect(info.activity).toBe('active');
    expect(info.phase).toBe('inhaling');
  });
});

describe('PhaseCalculator — first cycle phases', () => {
  test('inhaling: t in [0, 4000)', () => {
    const info = computePhaseInfo(BOX_CONFIG, 1_000);
    expect(info.activity).toBe('active');
    expect(info.phase).toBe('inhaling');
    expect(info.cycleIndex).toBe(0);
    expect(info.phaseProgress).toBeCloseTo(0.25, 5);
    expect(info.phaseElapsedMs).toBe(1_000);
    expect(info.phaseRemainingMs).toBe(3_000);
  });

  test('holdAfterInhale: t in [4000, 8000)', () => {
    const info = computePhaseInfo(BOX_CONFIG, 6_000);
    expect(info.phase).toBe('holdAfterInhale');
    expect(info.phaseElapsedMs).toBe(2_000);
    expect(info.phaseRemainingMs).toBe(2_000);
    expect(info.phaseProgress).toBeCloseTo(0.5, 5);
  });

  test('exhaling: t in [8000, 12000)', () => {
    const info = computePhaseInfo(BOX_CONFIG, 10_000);
    expect(info.phase).toBe('exhaling');
    expect(info.phaseElapsedMs).toBe(2_000);
    expect(info.phaseProgress).toBeCloseTo(0.5, 5);
  });

  test('holdAfterExhale: t in [12000, 16000)', () => {
    const info = computePhaseInfo(BOX_CONFIG, 14_000);
    expect(info.phase).toBe('holdAfterExhale');
    expect(info.phaseElapsedMs).toBe(2_000);
    expect(info.phaseProgress).toBeCloseTo(0.5, 5);
  });
});

describe('PhaseCalculator — cycle boundaries', () => {
  test('cycle 0 ends at t=16000', () => {
    const info = computePhaseInfo(BOX_CONFIG, 15_999);
    expect(info.cycleIndex).toBe(0);
    expect(info.cycleProgress).toBeCloseTo(15_999 / 16_000, 3);
  });

  test('cycle 1 starts at t=16000', () => {
    const info = computePhaseInfo(BOX_CONFIG, 16_000);
    expect(info.cycleIndex).toBe(1);
    expect(info.phase).toBe('inhaling');
    expect(info.phaseProgress).toBe(0);
    expect(info.cycleProgress).toBe(0);
  });

  test('last cycle boundary', () => {
    const info = computePhaseInfo(BOX_CONFIG, 32_000);
    expect(info.cycleIndex).toBe(2);
    expect(info.phase).toBe('inhaling');
  });
});

describe('PhaseCalculator — completion', () => {
  test('completed state when sessionElapsedMs >= sessionDurationMs', () => {
    const info = computePhaseInfo(BOX_CONFIG, 48_000);
    expect(info.activity).toBe('completed');
    expect(info.phase).toBeNull();
    expect(info.cycleIndex).toBe(BOX_CONFIG.cycles);
    expect(info.totalRemainingMs).toBe(0);
    expect(info.phaseProgress).toBe(1);
  });

  test('completed state at exactly sessionDurationMs', () => {
    const info = computePhaseInfo(BOX_CONFIG, 48_000);
    expect(info.activity).toBe('completed');
  });

  test('completed state past sessionDurationMs', () => {
    const info = computePhaseInfo(BOX_CONFIG, 100_000);
    expect(info.activity).toBe('completed');
    expect(info.cycleIndex).toBe(BOX_CONFIG.cycles);
  });
});

describe('PhaseCalculator — zero-duration phases', () => {
  const configNoHolds = {
    inhaleMs: 4_000,
    holdAfterInhaleMs: 0,
    exhaleMs: 4_000,
    holdAfterExhaleMs: 0,
    cycles: 3,
  };

  test('zero holdAfterInhale: t=4000 jumps to exhaling', () => {
    const info = computePhaseInfo(configNoHolds, 4_000);
    expect(info.phase).toBe('exhaling');
    expect(info.phaseProgress).toBe(0);
  });

  test('zero holdAfterExhale: t=8000 jumps to next cycle inhaling', () => {
    const info = computePhaseInfo(configNoHolds, 8_000);
    expect(info.phase).toBe('inhaling');
    expect(info.cycleIndex).toBe(1);
  });

  test('cycle duration is sum of phase durations', () => {
    const info = computePhaseInfo(configNoHolds, 0);
    expect(info.cycleDurationMs).toBe(8_000);
  });
});

describe('PhaseCalculator — session totals', () => {
  test('totalDurationMs includes prepMs', () => {
    const config = { ...BOX_CONFIG, prepMs: 2_000 };
    const info = computePhaseInfo(config, 0);
    expect(info.totalDurationMs).toBe(50_000); // 2000 prep + 48000 session
  });

  test('sessionDurationMs excludes prep', () => {
    const config = { ...BOX_CONFIG, prepMs: 2_000 };
    const info = computePhaseInfo(config, 0);
    expect(info.sessionDurationMs).toBe(48_000);
  });

  test('totalRemainingMs decreases as session progresses', () => {
    const early = computePhaseInfo(BOX_CONFIG, 1_000);
    const late = computePhaseInfo(BOX_CONFIG, 10_000);
    expect(late.totalRemainingMs).toBeLessThan(early.totalRemainingMs);
  });
});

describe('PhaseCalculator — negative and edge inputs', () => {
  test('negative totalElapsedMs treated as 0', () => {
    const info = computePhaseInfo(BOX_CONFIG, -100);
    expect(info.totalElapsedMs).toBe(0);
    expect(info.activity).toBe('active');
    expect(info.phase).toBe('inhaling');
  });
});

describe('PhaseCalculator — default config', () => {
  test('default config: 4-4-4-4 × 5 = 80 seconds', () => {
    const info = computePhaseInfo(DEFAULT_BREATH_CYCLE_CONFIG, 0);
    expect(info.cycleDurationMs).toBe(16_000);
    expect(info.sessionDurationMs).toBe(80_000);
  });
});