// GenomeCard — answers "was a genome created?" + its hashes.

import React from 'react';
import { Stack, Typography } from '@mui/material';
import CardShell from './CardShell';

export default function GenomeCard({ state, vm, errorMessage, onRetry }) {
  return (
    <CardShell
      title="O genome foi criado?"
      subtitle={vm?.id || '—'}
      state={state}
      errorMessage={errorMessage}
      onRetry={onRetry}
      emptyMessage="Nenhum genome persistido ainda."
    >
      <Stack spacing={1}>
        <Stack direction="row" spacing={3}>
          <Stat label="Genes" value={vm?.geneCount ?? 0} />
          <Stat label="Correlações" value={vm?.correlationCount ?? 0} />
          <Stat label="Hipóteses" value={vm?.hypothesisCount ?? 0} />
        </Stack>
        <Typography variant="body2" color="text.secondary">
          O <em>state_hash</em> garante que esta representação é idêntica à reconstruída
          por replay — ou seja, o conteúdo é determinístico.
        </Typography>
        <Typography variant="caption" color="text.disabled">
          state_hash: <code>{vm?.stateHash || '—'}</code>
        </Typography>
        <Typography variant="caption" color="text.disabled">
          Identificador: <code>{vm?.urn || '—'}</code>
        </Typography>
      </Stack>
    </CardShell>
  );
}

function Stat({ label, value }) {
  return (
    <Stack>
      <Typography variant="caption" color="text.secondary">{label}</Typography>
      <Typography variant="h6" sx={{ fontWeight: 600 }}>{value}</Typography>
    </Stack>
  );
}
