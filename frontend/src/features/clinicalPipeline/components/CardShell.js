// CardShell — 5-state container that every pipeline card uses.
// States: loading | empty | error | success | offline
//
// Visual treatment is intentionally calm: a thin border, generous padding,
// one icon, no modals. The state's severity is signaled by border colour only.

import React from 'react';
import { Box, Paper, Stack, Typography, Skeleton, Alert, Button } from '@mui/material';
import InboxOutlinedIcon from '@mui/icons-material/InboxOutlined';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import WifiOffOutlinedIcon from '@mui/icons-material/WifiOffOutlined';
import { tokens } from '../../../theme/tokens';

const STATE_BORDER = {
  loading: tokens.elevation?.borderMuted || '#e0e0e0',
  empty: tokens.elevation?.borderMuted || '#e0e0e0',
  error: '#d32f2f',
  success: tokens.elevation?.borderMuted || '#e0e0e0',
  offline: '#ed6c02',
};

const STATE_ICON = {
  empty: <InboxOutlinedIcon fontSize="small" />,
  error: <ErrorOutlineIcon fontSize="small" color="error" />,
  offline: <WifiOffOutlinedIcon fontSize="small" sx={{ color: '#ed6c02' }} />,
};

function Header({ title, subtitle, accent }) {
  return (
    <Stack direction="row" alignItems="baseline" justifyContent="space-between" mb={1.5}>
      <Stack direction="row" spacing={1} alignItems="baseline">
        <Typography variant="overline" sx={{ letterSpacing: 1, color: 'text.secondary' }}>
          {title}
        </Typography>
        {accent ? (
          <Typography variant="caption" sx={{ color: 'text.disabled' }}>
            {accent}
          </Typography>
        ) : null}
      </Stack>
      {subtitle ? (
        <Typography variant="caption" sx={{ color: 'text.disabled' }}>
          {subtitle}
        </Typography>
      ) : null}
    </Stack>
  );
}

function LoadingBody({ rows = 3 }) {
  return (
    <Stack spacing={1}>
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} variant="text" height={28} />
      ))}
    </Stack>
  );
}

function EmptyBody({ message = 'Sem dados ainda.' }) {
  return (
    <Stack direction="row" spacing={1.5} alignItems="center" sx={{ color: 'text.secondary', py: 2 }}>
      {STATE_ICON.empty}
      <Typography variant="body2">{message}</Typography>
    </Stack>
  );
}

function ErrorBody({ message, onRetry }) {
  return (
    <Alert
      severity="error"
      icon={STATE_ICON.error}
      action={
        onRetry ? (
          <Button color="inherit" size="small" onClick={onRetry}>
            Tentar novamente
          </Button>
        ) : null
      }
      sx={{ alignItems: 'center' }}
    >
      {message || 'Falha ao carregar.'}
    </Alert>
  );
}

function OfflineBody() {
  return (
    <Alert severity="warning" icon={STATE_ICON.offline} sx={{ alignItems: 'center' }}>
      Sem conexão com a API.
    </Alert>
  );
}

/**
 * @param {{
 *   title: string,
 *   subtitle?: string,
 *   accent?: string,
 *   state: 'loading' | 'empty' | 'error' | 'success' | 'offline',
 *   errorMessage?: string,
 *   onRetry?: () => void,
 *   loadingRows?: number,
 *   emptyMessage?: string,
 *   children: React.ReactNode,
 * }} props
 */
export default function CardShell({
  title,
  subtitle,
  accent,
  state,
  errorMessage,
  onRetry,
  loadingRows = 3,
  emptyMessage,
  children,
}) {
  const borderColor = STATE_BORDER[state] || STATE_BORDER.success;
  const isInteractive = state === 'success';
  return (
    <Paper
      elevation={0}
      sx={{
        p: 3,
        borderRadius: tokens.radius?.lg || 12,
        border: '1px solid',
        borderColor,
        backgroundColor: 'background.paper',
        transition: tokens.transition?.fast || 'all 120ms ease',
      }}
      role="region"
      aria-label={title}
      aria-busy={state === 'loading'}
    >
      <Header title={title} subtitle={subtitle} accent={accent} />
      {state === 'loading' && <LoadingBody rows={loadingRows} />}
      {state === 'empty' && <EmptyBody message={emptyMessage} />}
      {state === 'error' && <ErrorBody message={errorMessage} onRetry={onRetry} />}
      {state === 'offline' && <OfflineBody />}
      {isInteractive && <Box>{children}</Box>}
    </Paper>
  );
}
