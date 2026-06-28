/**
 * React provider + hook for FeatureFlagService.
 */

import React, { createContext, useContext, useMemo } from 'react';

import {
  FeatureFlagService,
  LocalFeatureFlagService,
  DEFAULT_FLAG_SNAPSHOT,
} from './FeatureFlagService';

const FeatureFlagContext = createContext<FeatureFlagService | undefined>(undefined);

export interface FeatureFlagProviderProps {
  readonly service?: FeatureFlagService;
  readonly children: React.ReactNode;
}

export const FeatureFlagProvider: React.FC<FeatureFlagProviderProps> = ({
  service,
  children,
}) => {
  const value = useMemo<FeatureFlagService>(() => {
    if (service !== undefined) {
      return service;
    }
    const local = new LocalFeatureFlagService();
    local.loadSnapshot(DEFAULT_FLAG_SNAPSHOT);
    return local;
  }, [service]);

  return <FeatureFlagContext.Provider value={value}>{children}</FeatureFlagContext.Provider>;
};

export const useFeatureFlags = (): FeatureFlagService => {
  const ctx = useContext(FeatureFlagContext);
  if (ctx === undefined) {
    throw new Error('useFeatureFlags must be used within FeatureFlagProvider');
  }
  return ctx;
};
