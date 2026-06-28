/**
 * Biometrics — interface only.
 *
 * Implementation: react-native-biometrics (TouchID, FaceID, Fingerprint).
 */

export type BiometryType = 'touchId' | 'faceId' | 'fingerprint' | 'none';

export interface BiometricsAvailability {
  readonly available: boolean;
  readonly type: BiometryType;
}

export interface Biometrics {
  isAvailable(): Promise<BiometricsAvailability>;
  authenticate(reason: string): Promise<boolean>;
  storeSecret(key: string, value: string): Promise<void>;
  getSecret(key: string): Promise<string | null>;
  removeSecret(key: string): Promise<void>;
}
