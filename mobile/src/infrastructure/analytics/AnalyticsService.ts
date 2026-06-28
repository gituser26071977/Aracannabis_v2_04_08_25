/**
 * Analytics — interface only.
 *
 * Implementation: custom HTTP uploader to backend (Sprint 7).
 * Note: AnalyticsEngine wraps this and adds event queueing,
 * retry, opt-in categories. This file defines the contract.
 */

export type AnalyticsEventCategory =
  | 'essential'
  | 'product_analytics'
  | 'performance'
  | 'research'
  | 'marketing';

export interface AnalyticsEvent {
  readonly name: string;
  readonly category: AnalyticsEventCategory;
  readonly properties: Readonly<Record<string, string | number | boolean | null>>;
  readonly timestamp: number;
}

export interface AnalyticsService {
  track(event: AnalyticsEvent): void;
  flush(): Promise<void>;
  setUser(userId: string, tenantId: string): void;
  setOptIn(category: AnalyticsEventCategory, optedIn: boolean): void;
  isOptedIn(category: AnalyticsEventCategory): boolean;
}
