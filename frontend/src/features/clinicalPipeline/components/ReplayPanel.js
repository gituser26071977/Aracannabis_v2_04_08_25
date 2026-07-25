// ReplayPanel — answers "does replay reproduce the original state_hash?".
// Calls POST /research/sessions/{id}/replay.
//
// Includes a session picker so the user can choose which session to replay.

import React from 'react';
import { Stack, Typography, Button, Alert, Chip, TextField, MenuItem } from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import CardShell from './CardShell';

export default function ReplayPanel({
  state,
  sessionId,
  sessions = [],
  onSelectSession,
  replay,
  isReplaying,
  onReplay,
  errorMessage,
}) {
  const hasSession = !!sessionId;
  return (
    <CardShell
      title="O replay reproduz exatamente o mesmo estado?"
      subtitle={hasSession ? `sessão: ${sessionId}` : '—'}
      state={state === 'success' ? 'success' : state}
      emptyMessage="Sem sessão para replicar. Selecione abaixo."
      errorMessage={errorMessage}
    >
      <Stack spacing={1.5}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5} alignItems={{ md: 'center' }}>
          <TextField
            select
            size="small"
            label="Sessão"
            value={sessionId || ''}
            onChange={(e) => onSelectSession?.(e.target.value)}
            sx={{ minWidth: 280 }}
            disabled={sessions.length === 0}
          >
            {sessions.length === 0 ? (
              <MenuItem value="" disabled>
                Nenhuma sessão disponível
              </MenuItem>
            ) : (
              sessions.map((s) => (
                <MenuItem key={s.session_id} value={s.session_id}>
                  {s.session_id} · {s.analysis_type}
                </MenuItem>
              ))
            )}
          </TextField>
          <Button
            variant="contained"
            color="primary"
            startIcon={<PlayArrowIcon />}
            disabled={!hasSession || isReplaying}
            onClick={() => onReplay(sessionId)}
            aria-label="Executar replay"
          >
            {isReplaying ? 'Reproduzindo…' : 'Executar Replay'}
          </Button>
          {replay?.match === true ? (
            <Chip
              icon={<CheckCircleOutlineIcon />}
              color="success"
              variant="outlined"
              label="Replay OK · state_hash idêntico"
            />
          ) : replay?.match === false ? (
            <Chip
              icon={<ErrorOutlineIcon />}
              color="error"
              variant="outlined"
              label="Diferença encontrada"
            />
          ) : null}
        </Stack>

        {replay ? (
          <Alert severity={replay.match ? 'success' : 'error'} sx={{ alignItems: 'center' }}>
            {replay.match ? (
              <>
                Reproduzido em {(replay.durationSeconds * 1000).toFixed(0)} ms. Novo{' '}
                <code>session_id</code>: <code>{replay.sessionId}</code>.
              </>
            ) : (
              <>
                <Typography variant="body2">
                  <strong>state_hash original:</strong> <code>{replay.diff?.original}</code>
                </Typography>
                <Typography variant="body2">
                  <strong>state_hash replay:</strong> <code>{replay.diff?.replay}</code>
                </Typography>
              </>
            )}
          </Alert>
        ) : null}
      </Stack>
    </CardShell>
  );
}
