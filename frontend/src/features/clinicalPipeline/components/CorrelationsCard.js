// CorrelationsCard — answers "how many correlations were found?".

import React from 'react';
import { Stack, Typography, Chip } from '@mui/material';
import CardShell from './CardShell';

export default function CorrelationsCard({ state, vm, errorMessage, onRetry }) {
  return (
    <CardShell
      title="Quais correlações foram encontradas?"
      subtitle={`${vm?.count ?? 0} encontradas`}
      state={state}
      errorMessage={errorMessage}
      onRetry={onRetry}
      emptyMessage="Nenhuma correlação ainda."
    >
      <Stack spacing={1.5}>
        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
          {vm?.methods?.length ? (
            vm.methods.map((m) => <Chip key={m} size="small" label={m} variant="outlined" />)
          ) : (
            <Typography variant="caption" color="text.disabled">—</Typography>
          )}
        </Stack>
        <Stack direction="row" spacing={3}>
          <Metric label="ρ mais forte" value={vm?.max ?? '—'} />
          <Metric label="ρ médio" value={vm?.mean ?? '—'} />
        </Stack>
        {vm?.top5?.length ? (
          <Stack spacing={0.5}>
            <Typography variant="caption" color="text.secondary">
              As 5 correlações mais fortes — pares de genes que mais se movem juntos
              neste paciente.
            </Typography>
            {vm.top5.map((c) => (
              <Typography key={c.id} variant="body2">
                <code>{c.geneX}</code> × <code>{c.geneY}</code> — ρ <strong>{c.coefficient}</strong> · {c.method}
              </Typography>
            ))}
          </Stack>
        ) : null}
      </Stack>
    </CardShell>
  );
}

function Metric({ label, value }) {
  return (
    <Stack>
      <Typography variant="caption" color="text.secondary">{label}</Typography>
      <Typography variant="h6" sx={{ fontWeight: 600 }}>{value}</Typography>
    </Stack>
  );
}
