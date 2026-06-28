/**
 * Feature flag snapshot seed.
 *
 * Snapshot inicial das feature flags do app. Será sobrescrito pelo
 * Remote Config em sprints futuros. Nenhuma flag habilitada por padrão.
 */

import type { FeatureFlagSnapshot } from '@infrastructure/feature-flags';

export const SEED_FLAG_SNAPSHOT: FeatureFlagSnapshot = {
  'session.timer_engine': {
    type: 'boolean',
    enabled: true,
    rolloutPercentage: 100,
  },
  'session.breath_engine': {
    type: 'boolean',
    enabled: true,
    rolloutPercentage: 100,
  },
  'session.audio_engine': {
    type: 'boolean',
    enabled: false,
    rolloutPercentage: 0,
  },
  'session.animation_engine': {
    type: 'boolean',
    enabled: true,
    rolloutPercentage: 100,
  },
  'session.safety_engine': {
    type: 'boolean',
    enabled: true,
    rolloutPercentage: 100,
  },
  'protocol.box_4_4_4_4': {
    type: 'boolean',
    enabled: true,
    rolloutPercentage: 100,
  },
  'protocol.diaphragmatic': {
    type: 'boolean',
    enabled: true,
    rolloutPercentage: 100,
  },
  'protocol.physiological_sigh': {
    type: 'boolean',
    enabled: true,
    rolloutPercentage: 100,
  },
  'safety.excessive_usage_alert': {
    type: 'boolean',
    enabled: true,
    rolloutPercentage: 100,
  },
  'analytics.opt_in_default': {
    type: 'boolean',
    enabled: false,
    rolloutPercentage: 0,
  },
} as const;
