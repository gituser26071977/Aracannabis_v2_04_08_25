/**
 * LoadingState — wrapper padronizado para estados de carregamento.
 *
 * Resolve:
 *   - 15+ variações de "loading" (algumas só CircularProgress, outras com texto,
 *     outras com Box de altura fixa sem centralizar)
 *
 * Uso:
 *   {loading ? <LoadingState /> : <Conteudo />}
 *
 *   <LoadingState variant="skeleton" rows={5} />
 *   <LoadingState message="Carregando pacientes..." />
 */
import React from 'react';
import { Box, CircularProgress, Typography, Skeleton, Stack } from '@mui/material';
import { tokens } from '../theme/tokens';

const SpinnerVariant = ({ message, minHeight = 240 }) => (
  <Box
    role="status"
    aria-live="polite"
    aria-busy="true"
    sx={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 2,
      minHeight,
      py: 6,
    }}
  >
    <CircularProgress size={40} thickness={4} />
    {message && (
      <Typography variant="body2" color="text.secondary">
        {message}
      </Typography>
    )}
  </Box>
);

const SkeletonVariant = ({ rows = 5, hasAvatar = false, hasActions = false }) => (
  <Stack spacing={1.5} sx={{ p: 2 }} role="status" aria-busy="true">
    {Array.from({ length: rows }).map((_, i) => (
      <Box
        key={i}
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 2,
          p: 1.5,
          borderRadius: tokens.radius.md,
          border: 1,
          borderColor: 'divider',
        }}
      >
        {hasAvatar && (
          <Skeleton variant="circular" width={40} height={40} />
        )}
        <Stack spacing={0.75} sx={{ flexGrow: 1 }}>
          <Skeleton variant="text" width="60%" height={20} />
          <Skeleton variant="text" width="40%" height={16} />
        </Stack>
        {hasActions && (
          <Stack direction="row" spacing={0.5}>
            <Skeleton variant="circular" width={32} height={32} />
            <Skeleton variant="circular" width={32} height={32} />
          </Stack>
        )}
      </Box>
    ))}
  </Stack>
);

const LoadingState = ({ variant = 'spinner', message, rows, hasAvatar, hasActions, minHeight }) => {
  if (variant === 'skeleton') {
    return <SkeletonVariant rows={rows} hasAvatar={hasAvatar} hasActions={hasActions} />;
  }
  return <SpinnerVariant message={message} minHeight={minHeight} />;
};

export default LoadingState;
