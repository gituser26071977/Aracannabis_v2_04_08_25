/**
 * AraFlow — Mobile App Root
 *
 * Componente raiz. Apenas inicializa o container de DI, o sistema de
 * logging, o error boundary global, e o theme provider. Nenhuma
 * feature, nenhum engine, nenhuma tela é montada aqui.
 *
 * No MVP, este componente renderiza uma tela placeholder; em sprints
 * subsequentes, as features são montadas pelo router.
 */

import React from 'react';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { StatusBar, useColorScheme } from 'react-native';

import { container } from '@infrastructure/di/container';
import { GlobalErrorBoundary } from '@shared/errors/GlobalErrorBoundary';
import { ThemeProvider } from '@shared/theme/ThemeProvider';
import { I18nProvider } from '@shared/i18n/I18nProvider';
import { configureI18n } from '@shared/i18n/configureI18n';

import { logger } from '@infrastructure/logging/logger';

import { PlaceholderScreen } from './PlaceholderScreen';

configureI18n();

const log = logger.child({ layer: 'app' });

log.info('AraFlow app initializing');

export const App: React.FC = () => {
  const systemColorScheme = useColorScheme();
  const themeMode = systemColorScheme === 'dark' ? 'dark' : 'light';

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <GlobalErrorBoundary>
          <I18nProvider>
            <ThemeProvider mode={themeMode}>
              <StatusBar
                barStyle={themeMode === 'dark' ? 'light-content' : 'dark-content'}
                backgroundColor="transparent"
                translucent
              />
              <PlaceholderScreen />
            </ThemeProvider>
          </I18nProvider>
        </GlobalErrorBoundary>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
};

// Ensure container is referenced to avoid tree-shaking removal in some build
// configurations. Side-effect import keeps DI alive throughout app lifecycle.
void container;
