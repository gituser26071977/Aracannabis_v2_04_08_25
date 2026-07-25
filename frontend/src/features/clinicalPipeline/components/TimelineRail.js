// TimelineRail — chronological view of the pipeline run.
// Vertical list with HH:MM:SS timestamps.

import React from 'react';
import { Paper, Stack, Typography, Divider, Box } from '@mui/material';
import { tokens } from '../../../theme/tokens';

function fmtTime(iso) {
  if (!iso) return '—';
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString('pt-BR', { hour12: false });
  } catch {
    return iso;
  }
}

export default function TimelineRail({ entries = [] }) {
  return (
    <Paper
      elevation={0}
      sx={{
        p: 2,
        borderRadius: tokens.radius?.lg || 12,
        border: '1px solid',
        borderColor: tokens.elevation?.borderMuted || '#e0e0e0',
        position: 'sticky',
        top: 16,
      }}
      role="complementary"
      aria-label="Timeline do pipeline"
    >
      <Typography variant="overline" sx={{ letterSpacing: 1, color: 'text.secondary' }}>
        Linha do tempo
      </Typography>
      <Divider sx={{ my: 1 }} />
      {entries.length === 0 ? (
        <Typography variant="body2" color="text.disabled" sx={{ py: 2 }}>
          Sem eventos ainda. Rode o pipeline para ver a linha do tempo.
        </Typography>
      ) : (
        <Stack spacing={1.25}>
          {entries.map((e) => (
            <Stack key={e.id} direction="row" spacing={1.5} alignItems="flex-start">
              <Box
                sx={{
                  mt: 0.5,
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  backgroundColor: 'primary.main',
                  flexShrink: 0,
                }}
              />
              <Stack spacing={0.25} sx={{ minWidth: 0 }}>
                <Typography variant="caption" sx={{ fontFamily: 'monospace' }} color="text.secondary">
                  {fmtTime(e.at)}
                </Typography>
                <Typography variant="body2">{e.label}</Typography>
              </Stack>
            </Stack>
          ))}
        </Stack>
      )}
    </Paper>
  );
}
