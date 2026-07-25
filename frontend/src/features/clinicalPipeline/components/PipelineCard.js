// PipelineCard — answers "did the pipeline run?" + shows technical metadata.

import React from 'react';
import { Stack, Typography, Chip } from '@mui/material';
import CardShell from './CardShell';

function fmtMs(seconds) {
  if (seconds === null || seconds === undefined) return '—';
  return `${(seconds * 1000).toFixed(0)} ms`;
}

export default function PipelineCard({ state, vm, requestMeta, errorMessage, onRetry }) {
  const correlationId = vm?.timeline?.[0]?.correlationId || requestMeta?.correlation_id;
  const requestId = vm?.timeline?.[0]?.requestId || requestMeta?.request_id;
  return (
    <CardShell
      title="O pipeline executou?"
      subtitle={fmtMs(vm?.pipeline?.durationSeconds)}
      accent={vm?.pipeline?.version ? `v${vm.pipeline.version}` : null}
      state={state}
      errorMessage={errorMessage}
      onRetry={onRetry}
      emptyMessage="Nenhum pipeline executado ainda. Rode acima para começar."
    >
      <Stack spacing={1.25}>
        <Typography variant="body2" color="text.secondary">
          Toda a cadeia — correlações, hipóteses e grafo — foi processada em um único
          fluxo reprodutível.
        </Typography>
        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
          <Chip size="small" label={`Identificador: ${requestId || '—'}`} variant="outlined" />
          <Chip size="small" label={`Trilha: ${correlationId || '—'}`} variant="outlined" />
        </Stack>
        <Typography variant="caption" color="text.disabled">
          Início: {vm?.pipeline?.startedAt || '—'} · Fim: {vm?.pipeline?.completedAt || '—'}
        </Typography>
      </Stack>
    </CardShell>
  );
}
