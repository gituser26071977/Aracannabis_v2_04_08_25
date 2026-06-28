/**
 * Haptics — interface only.
 *
 * Implementation: react-native-haptic-feedback or expo-haptics.
 */

export type HapticPattern = 'light' | 'medium' | 'heavy' | 'success' | 'warning' | 'error';

export interface Haptics {
  trigger(pattern: HapticPattern): Promise<void>;
  isSupported(): Promise<boolean>;
}
