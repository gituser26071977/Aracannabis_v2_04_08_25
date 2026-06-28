/**
 * AraFlow — GlobalErrorBoundary
 *
 * Captura erros não tratados na árvore de componentes. Em produção,
 * registra no Sentry (stubbed em Sprint 0) e exibe tela de erro mínima.
 */

import React from 'react';
import { ErrorInfo, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { isAppError } from './AppError';
import { logger } from '@infrastructure/logging/logger';
import { useTokens } from '@shared/theme/useTokens';
import { useTranslation } from 'react-i18next';

interface GlobalErrorBoundaryState {
  error: Error | null;
}

interface GlobalErrorBoundaryProps {
  readonly children: React.ReactNode;
}

const log = logger.child({ component: 'GlobalErrorBoundary' });

export class GlobalErrorBoundary extends React.Component<
  GlobalErrorBoundaryProps,
  GlobalErrorBoundaryState
> {
  public override state: GlobalErrorBoundaryState = { error: null };

  public static getDerivedStateFromError(error: Error): GlobalErrorBoundaryState {
    return { error };
  }

  public override componentDidCatch(error: Error, info: ErrorInfo): void {
    const context: Record<string, unknown> = { componentStack: info.componentStack };
    if (isAppError(error)) {
      log.error('uncaught.app_error', { code: error.code, ...context });
    } else {
      log.error('uncaught.unexpected', { message: error.message, ...context });
    }
    // Sentry.captureException will be wired in a later sprint.
  }

  private readonly handleReset = (): void => {
    this.setState({ error: null });
  };

  public override render(): React.ReactNode {
    const { error } = this.state;
    if (error === null) {
      return this.props.children;
    }
    return <ErrorFallback error={error} onReset={this.handleReset} />;
  }
}

interface ErrorFallbackProps {
  readonly error: Error;
  readonly onReset: () => void;
}

const ErrorFallback: React.FC<ErrorFallbackProps> = ({ error, onReset }) => {
  const tokens = useTokens();
  const { t } = useTranslation('errors');
  const code = isAppError(error) ? error.code : 'unexpected';

  return (
    <View
      style={[
        styles.container,
        { backgroundColor: tokens.color.background.base, padding: tokens.spacing.lg },
      ]}
    >
      <Text
        style={{
          color: tokens.color.text.primary,
          fontSize: tokens.typography.size.heading,
          fontWeight: tokens.typography.weight.bold,
        }}
      >
        {t('global.title')}
      </Text>
      <Text
        style={{
          color: tokens.color.text.secondary,
          fontSize: tokens.typography.size.body,
          marginTop: tokens.spacing.md,
        }}
      >
        {t('global.body')}
      </Text>
      <Text
        style={{
          color: tokens.color.text.tertiary,
          fontSize: tokens.typography.size.caption,
          marginTop: tokens.spacing.lg,
        }}
      >
        {t('global.code', { code })}
      </Text>
      <TouchableOpacity
        accessibilityRole="button"
        accessibilityLabel={t('global.retry')}
        onPress={onReset}
        style={[
          styles.button,
          {
            backgroundColor: tokens.color.brand.primary,
            padding: tokens.spacing.md,
            marginTop: tokens.spacing.xl,
            borderRadius: tokens.radius.md,
          },
        ]}
      >
        <Text style={{ color: tokens.color.text.inverse, fontWeight: tokens.typography.weight.bold }}>
          {t('global.retry')}
        </Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  button: {
    minWidth: 200,
    alignItems: 'center',
  },
});
