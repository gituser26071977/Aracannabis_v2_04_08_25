/**
 * AraFlow — Placeholder screen
 *
 * Tela mínima exibida na Sprint 0 enquanto features reais não estão
 * implementadas. Será substituída pelo router real no Sprint 2.
 */

import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { useTokens } from '@shared/theme/useTokens';
import { useTranslation } from 'react-i18next';

export const PlaceholderScreen: React.FC = () => {
  const tokens = useTokens();
  const { t } = useTranslation('common');

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
        {t('app.name')}
      </Text>
      <Text
        style={{
          color: tokens.color.text.secondary,
          fontSize: tokens.typography.size.body,
          marginTop: tokens.spacing.md,
        }}
      >
        {t('placeholder.foundationReady')}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
