/**
 * AraFlow — i18n configuration
 *
 * Configuração do i18next com namespaces, fallback chain, e detecção
 * de locale do dispositivo.
 */

import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import { NativeModules, Platform } from 'react-native';

import enUS from './locales/en-US.json';
import ptBR from './locales/pt-BR.json';

const resources = {
  'en-US': { common: enUS },
  'pt-BR': { common: ptBR },
} as const;

const getDeviceLocale = (): string => {
  try {
    if (Platform.OS === 'ios') {
      const settings = NativeModules.SettingsManager?.settings;
      const locale = settings?.AppleLocale ?? settings?.AppleLanguages?.[0];
      if (typeof locale === 'string') {
        return locale.replace(/_/g, '-');
      }
    } else {
      const locale = NativeModules.I18nManager?.localeIdentifier;
      if (typeof locale === 'string') {
        return locale.replace(/_/g, '-');
      }
    }
  } catch {
    // Fall through to default
  }
  return 'pt-BR';
};

export const SUPPORTED_LOCALES = ['pt-BR', 'en-US'] as const;
export type SupportedLocale = (typeof SUPPORTED_LOCALES)[number];

export const isSupportedLocale = (locale: string): locale is SupportedLocale => {
  return (SUPPORTED_LOCALES as readonly string[]).includes(locale);
};

export const configureI18n = (locale?: string): typeof i18n => {
  const resolved = locale ?? getDeviceLocale();
  const initial = isSupportedLocale(resolved) ? resolved : 'pt-BR';

  if (!i18n.isInitialized) {
    void i18n.use(initReactI18next).init({
      resources,
      lng: initial,
      fallbackLng: 'pt-BR',
      defaultNS: 'common',
      ns: ['common'],
      interpolation: {
        escapeValue: false, // React Native already escapes
      },
      react: {
        useSuspense: false,
      },
      returnNull: false,
    });
  }
  return i18n;
};

export default i18n;
