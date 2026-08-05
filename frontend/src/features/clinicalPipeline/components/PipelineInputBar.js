// PipelineInputBar — single form to launch the pipeline.
// Three inputs + one Run button + a tiny "last run" summary.

import React, { useState } from 'react';
import { Stack, TextField, Button, Typography, Alert } from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';

function nowMinusMonthsIso(months) {
  const d = new Date();
  d.setMonth(d.getMonth() - months);
  return d.toISOString();
}

export default function PipelineInputBar({ onRun, isRunning, lastSummary, errorMessage, demoMode }) {
  const [patientId, setPatientId] = useState('');
  const [windowStart, setWindowStart] = useState(() => nowMinusMonthsIso(6));
  const [windowEnd, setWindowEnd] = useState(() => new Date().toISOString());
  const [windowLabel, setWindowLabel] = useState('6_months');
  const [validationError, setValidationError] = useState(null);

  const submit = (e) => {
    e?.preventDefault();
    setValidationError(null);
    if (!patientId.trim()) {
      setValidationError('Informe um identificador de paciente para começar.');
      return;
    }
    if (new Date(windowEnd).getTime() <= new Date(windowStart).getTime()) {
      setValidationError('A janela final precisa ser depois da inicial.');
      return;
    }
    onRun({
      patient_id: patientId.trim(),
      window_start: windowStart,
      window_end: windowEnd,
      window_label: windowLabel || null,
      methods: [],
      include_graph: true,
    });
  };

  return (
    <Stack
      component="form"
      onSubmit={submit}
      direction={{ xs: 'column', md: 'row' }}
      spacing={2}
      alignItems={{ xs: 'stretch', md: 'flex-end' }}
      sx={{
        p: 2,
        borderRadius: 2,
        border: '1px solid',
        borderColor: 'divider',
        backgroundColor: 'background.paper',
      }}
      aria-label="Executar pipeline"
    >
      <TextField
        label="Identificador do paciente"
        value={patientId}
        onChange={(e) => setPatientId(e.target.value)}
        size="small"
        required
        inputProps={{ 'aria-label': 'patient_id' }}
        placeholder={demoMode ? 'ex.: patient_demo_a1' : ''}
      />
      <TextField
        label="Início da janela (ISO 8601)"
        value={windowStart}
        onChange={(e) => setWindowStart(e.target.value)}
        size="small"
        required
      />
      <TextField
        label="Fim da janela (ISO 8601)"
        value={windowEnd}
        onChange={(e) => setWindowEnd(e.target.value)}
        size="small"
        required
      />
      <TextField
        label="Rótulo da janela"
        value={windowLabel}
        onChange={(e) => setWindowLabel(e.target.value)}
        size="small"
      />
      <Button
        type="submit"
        variant="contained"
        startIcon={<PlayArrowIcon />}
        disabled={isRunning}
        sx={{ minWidth: 180 }}
      >
        {isRunning ? 'Executando…' : 'Rodar pipeline'}
      </Button>

      {validationError ? (
        <Alert severity="warning" sx={{ width: '100%' }}>{validationError}</Alert>
      ) : null}
      {errorMessage ? (
        <Alert severity="error" sx={{ width: '100%' }}>{errorMessage}</Alert>
      ) : null}
      {lastSummary && !validationError && !errorMessage ? (
        <Typography variant="caption" color="text.secondary">
          {lastSummary}
        </Typography>
      ) : null}
    </Stack>
  );
}
