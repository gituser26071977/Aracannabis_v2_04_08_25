/**
 * AraFlow — Feature Flags
 *
 * Sistema de feature flags com avaliação local e override para
 * rollout gradual. Backend de remote flags será plugado em sprints
 * subsequentes; este service aceita snapshots de flags injetados.
 *
 * Princípios:
 *   - Default-off: feature não existe até ser explicitamente habilitada.
 *   - Avaliação determinística por userId (hash) para A/B tests.
 *   - Mudança sem deploy: snapshot atualizado via Remote Config.
 *
 * Uso:
 *   flags.isEnabled('safety.excessive_usage', { userId })
 *   flags.getVariant('onboarding.copy', { userId })
 */

import { logger } from '@infrastructure/logging/logger';

export type FeatureFlagSnapshot = Readonly<Record<string, FeatureFlagDefinition>>;

export type FeatureFlagDefinition =
  | { readonly type: 'boolean'; readonly enabled: boolean; readonly rolloutPercentage?: number }
  | { readonly type: 'variant'; readonly variants: readonly VariantSpec[] }
  | { readonly type: 'numeric'; readonly value: number };

export interface VariantSpec {
  readonly name: string;
  readonly weight: number; // 0..100
}

export interface EvaluationContext {
  readonly userId: string;
  readonly attributes?: Readonly<Record<string, string | number | boolean>>;
}

export interface FeatureFlagService {
  loadSnapshot(snapshot: FeatureFlagSnapshot): void;
  isEnabled(flagName: string, context: EvaluationContext): boolean;
  getVariant(flagName: string, context: EvaluationContext): string | undefined;
  getNumeric(flagName: string, context: EvaluationContext): number | undefined;
  list(): readonly string[];
}

const log = logger.child({ component: 'feature-flags' });

/**
 * Stable, fast, non-cryptographic hash.
 * Determinístico para que a mesma `userId` sempre caia no mesmo bucket.
 */
const hashToBucket = (userId: string, salt: string): number => {
  let hash = 0;
  const input = `${salt}:${userId}`;
  for (let i = 0; i < input.length; i += 1) {
    hash = (hash * 31 + input.charCodeAt(i)) | 0;
  }
  return Math.abs(hash) % 100;
};

export class LocalFeatureFlagService implements FeatureFlagService {
  private snapshot: FeatureFlagSnapshot = {};

  public loadSnapshot(snapshot: FeatureFlagSnapshot): void {
    this.snapshot = snapshot;
    log.info('feature_flags.snapshot_loaded', { count: Object.keys(snapshot).length });
  }

  public isEnabled(flagName: string, context: EvaluationContext): boolean {
    const flag = this.snapshot[flagName];
    if (flag === undefined) {
      return false;
    }
    if (flag.type !== 'boolean') {
      log.warn('feature_flags.type_mismatch', { flagName, expected: 'boolean' });
      return false;
    }
    if (!flag.enabled) {
      return false;
    }
    const rollout = flag.rolloutPercentage ?? 100;
    if (rollout >= 100) {
      return true;
    }
    return hashToBucket(context.userId, flagName) < rollout;
  }

  public getVariant(flagName: string, context: EvaluationContext): string | undefined {
    const flag = this.snapshot[flagName];
    if (flag === undefined) {
      return undefined;
    }
    if (flag.type !== 'variant') {
      log.warn('feature_flags.type_mismatch', { flagName, expected: 'variant' });
      return undefined;
    }
    const bucket = hashToBucket(context.userId, flagName);
    let cumulative = 0;
    for (const variant of flag.variants) {
      cumulative += variant.weight;
      if (bucket < cumulative) {
        return variant.name;
      }
    }
    return flag.variants[flag.variants.length - 1]?.name;
  }

  public getNumeric(flagName: string, _context: EvaluationContext): number | undefined {
    const flag = this.snapshot[flagName];
    if (flag === undefined) {
      return undefined;
    }
    if (flag.type !== 'numeric') {
      log.warn('feature_flags.type_mismatch', { flagName, expected: 'numeric' });
      return undefined;
    }
    return flag.value;
  }

  public list(): readonly string[] {
    return Object.keys(this.snapshot);
  }
}

/**
 * Snapshot inicial vazio — features precisam ser explicitamente habilitadas.
 */
export const DEFAULT_FLAG_SNAPSHOT: FeatureFlagSnapshot = {};
