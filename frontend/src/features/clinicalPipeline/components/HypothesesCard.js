// HypothesesCard — answers "which hypotheses emerged?".

import React from 'react';
import { Stack, Typography, LinearProgress, Chip } from '@mui/material';
import CardShell from './CardShell';

function pct(n) {
  if (n === null || n === undefined) return 0;
  return Math.max(0, Math.min(100, Math.round(n * 100)));
}

export default function HypothesesCard({ state, vm, errorMessage, onRetry }) {
  return (
    <CardShell
      title="Quais hipóteses surgiram?"
      subtitle={`${vm?.count ?? 0} afirmações`}
      state={state}
      errorMessage={errorMessage}
      onRetry={onRetry}
      emptyMessage="Nenhuma hipótese ainda."
    >
      <Stack spacing={1.5}>
        <Typography variant="body2" color="text.secondary">
          Cada hipótese combina as correlações acima com regras clínicas versionadas.
          O AraOS não sugere diagnóstico — apenas organiza padrões.
        </Typography>
        <Stack direction="row" spacing={3}>
          <Metric label="Confiança máxima" value={vm?.maxConfidence ?? '—'} />
          <Metric label="Confiança média" value={vm?.meanConfidence ?? '—'} />
        </Stack>
        {vm?.top3?.length ? (
          <Stack spacing={1}>
            <Typography variant="caption" color="text.secondary">
              As 3 hipóteses mais confiáveis neste paciente
            </Typography>
            {vm.top3.map((h) => (
              <Stack key={h.id} spacing={0.25}>
                <Stack direction="row" alignItems="center" spacing={1}>
                  <Typography variant="body2" sx={{ flex: 1 }}>{h.claim}</Typography>
                  <Chip size="small" label={`${pct(h.confidence)}%`} variant="outlined" />
                </Stack>
                <LinearProgress variant="determinate" value={pct(h.confidence)} sx={{ height: 4, borderRadius: 2 }} />
                <Typography variant="caption" color="text.disabled">
                  regra: <code>{h.ruleId}</code> · {h.supportingGenes.length} a favor · {h.contradictingGenes.length} contra
                </Typography>
              </Stack>
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
