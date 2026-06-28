/**
 * Features — barrel.
 *
 * Cada feature é uma pasta isolada com sua própria Clean Architecture
 * interna (presentation/application/domain/infrastructure). Features
 * podem importar de core/, shared/, e infrastructure/ — mas nunca
 * de outras features.
 */

export const ARAFLOW_FEATURES_VERSION = '0.0.0-foundation' as const;
