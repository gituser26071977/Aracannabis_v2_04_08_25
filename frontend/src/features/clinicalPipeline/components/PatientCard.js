// PatientCard — answers "which patient is this pipeline about?".

import React from 'react';
import { Stack, Typography } from '@mui/material';
import CardShell from './CardShell';

function fmt(iso) {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleDateString('pt-BR', { year: 'numeric', month: 'short', day: '2-digit' });
  } catch {
    return iso;
  }
}

export default function PatientCard({ state, vm, errorMessage, onRetry }) {
  return (
    <CardShell
      title="Quem é o paciente?"
      subtitle={vm?.id || '—'}
      state={state}
      errorMessage={errorMessage}
      onRetry={onRetry}
      emptyMessage="Nenhum paciente selecionado. Use o campo acima para iniciar."
    >
      <Stack spacing={0.5}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>
          {vm?.id || '—'}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Janela analisada: {fmt(vm?.windowStart)} → {fmt(vm?.windowEnd)}
        </Typography>
        {vm?.windowLabel ? (
          <Typography variant="caption" color="text.disabled">
            Rótulo: {vm.windowLabel}
          </Typography>
        ) : null}
      </Stack>
    </CardShell>
  );
}
