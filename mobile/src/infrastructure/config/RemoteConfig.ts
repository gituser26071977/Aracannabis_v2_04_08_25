/**
 * AraFlow — Remote Config (architecture only)
 *
 * Esta é a DEFINIÇÃO da interface e do contrato. A IMPLEMENTAÇÃO
 * concreta (Firebase Remote Config, Unleash, self-hosted) será
 * plugada em sprint subsequente via DI.
 *
 * O contrato:
 *   - O app chama `getValue('safety.max_session_ms')` a qualquer momento.
 *   - A implementação resolve para: valor remoto, valor cached local,
 *     valor default, nesta ordem.
 *   - `refresh()` puxa valores novos do backend (best-effort).
 *
 * Princípios:
 *   - Sync-only API (retorna valor, não promise), porque a UI não
 *     bloqueia esperando config.
 *   - Defaults sempre disponíveis; ausência de rede nunca quebra o app.
 *   - Schema do payload é versionado.
 */

import { logger } from '@infrastructure/logging/logger';

export type RemoteConfigValue = string | number | boolean;

export interface RemoteConfigSchema {
  readonly [key: string]: {
    readonly type: 'string' | 'number' | 'boolean';
    readonly defaultValue: RemoteConfigValue;
    readonly description?: string;
  };
}

export interface RemoteConfigService {
  getValue<K extends keyof RemoteConfigSchema & string>(
    key: K,
  ): RemoteConfigSchema[K]['type'] extends 'string'
    ? string
    : RemoteConfigSchema[K]['type'] extends 'number'
      ? number
      : boolean;
  getNumber(key: string): number;
  getString(key: string): string;
  getBoolean(key: string): boolean;
  refresh(): Promise<void>;
  readonly lastFetchedAt: number | null;
}

const log = logger.child({ component: 'remote-config' });

/**
 * Schema padrão (declarado em código; pode ser sobrescrito pelo
 * snapshot remoto).
 *
 * IMPORTANTE: Adicionar aqui toda chave que o app espera.
 */
export const REMOTE_CONFIG_SCHEMA = {
  'safety.max_session_ms': {
    type: 'number',
    defaultValue: 30 * 60 * 1000,
    description: 'Duração máxima de uma sessão (ms)',
  },
  'safety.max_sessions_per_day': {
    type: 'number',
    defaultValue: 12,
    description: 'Número máximo de sessões em 24h',
  },
  'safety.max_sessions_per_hour': {
    type: 'number',
    defaultValue: 4,
    description: 'Número máximo de sessões em 1h',
  },
  'feature.onboarding.copy_locale': {
    type: 'string',
    defaultValue: 'pt-BR',
    description: 'Locale default do onboarding',
  },
  'feature.experimental.haptics': {
    type: 'boolean',
    defaultValue: false,
    description: 'Habilita feedback haptico experimental',
  },
} as const satisfies RemoteConfigSchema;

export type RemoteConfigKey = keyof typeof REMOTE_CONFIG_SCHEMA;

const isRemoteConfigKey = (key: string): key is RemoteConfigKey => {
  return key in REMOTE_CONFIG_SCHEMA;
};

export class StaticRemoteConfigService implements RemoteConfigService {
  public lastFetchedAt: number | null = null;

  public getValue<K extends RemoteConfigKey>(
    key: K,
  ): (typeof REMOTE_CONFIG_SCHEMA)[K]['defaultValue'] {
    const entry = REMOTE_CONFIG_SCHEMA[key];
    if (entry === undefined) {
      log.warn('remote_config.unknown_key', { key });
      return undefined as never;
    }
    return entry.defaultValue;
  }

  public getNumber(key: string): number {
    if (!isRemoteConfigKey(key)) {
      return 0;
    }
    const value = this.getValue(key);
    return typeof value === 'number' ? value : 0;
  }

  public getString(key: string): string {
    if (!isRemoteConfigKey(key)) {
      return '';
    }
    const value = this.getValue(key);
    return typeof value === 'string' ? value : '';
  }

  public getBoolean(key: string): boolean {
    if (!isRemoteConfigKey(key)) {
      return false;
    }
    const value = this.getValue(key);
    return typeof value === 'boolean' ? value : false;
  }

  public async refresh(): Promise<void> {
    // No-op: static service has no backend.
    this.lastFetchedAt = Date.now();
  }
}
