/**
 * I18nProvider — wrap children with I18nextProvider.
 *
 * The hook useTranslation is provided by react-i18next and is
 * available anywhere in the tree.
 */

import React from 'react';
import { I18nextProvider } from 'react-i18next';

import i18n from './configureI18n';

export interface I18nProviderProps {
  readonly children: React.ReactNode;
}

export const I18nProvider: React.FC<I18nProviderProps> = ({ children }) => {
  return <I18nextProvider i18n={i18n}>{children}</I18nextProvider>;
};
