import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Alert,
} from '@mui/material';
import EnhancedCombinedChart from './EnhancedCombinedChart';
import SymptomsChart from './SymptomsChart';
import DosageChart from './DosageChart';
import ExamChart from './ExamChart';

/**
 * Gráficos do prontuário clínico base (sintomas + exames).
 * As opções de dosagens (canabinoide) só aparecem com o módulo
 * cannabis-medicinal ativo (`habilitarCannabis`).
 */
const CombinedChartView = ({ patientId, habilitarCannabis = false }) => {
  const [chartType, setChartType] = useState('symptoms');
  const [loading] = useState(false);
  const [error] = useState('');

  // Handle chart type change
  const handleChartTypeChange = (event) => {
    setChartType(event.target.value);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 5 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Visualização de Gráficos
      </Typography>

      <FormControl fullWidth sx={{ mb: 3 }}>
        <InputLabel id="chart-type-label">Tipo de Gráfico</InputLabel>
        <Select
          labelId="chart-type-label"
          value={chartType}
          label="Tipo de Gráfico"
          onChange={handleChartTypeChange}
        >
          <MenuItem value="symptoms">Gráfico de Sintomas</MenuItem>
          <MenuItem value="exams">Gráfico de Exames</MenuItem>
          {habilitarCannabis && (
            <>
              <MenuItem value="combined">Gráfico Combinado (Sintomas + Dosagens)</MenuItem>
              <MenuItem value="dosage">Gráfico de Dosagens</MenuItem>
            </>
          )}
        </Select>
      </FormControl>

      {chartType === 'combined' && <EnhancedCombinedChart patientId={patientId} />}

      {chartType === 'symptoms' && <SymptomsChart patientId={patientId} />}

      {chartType === 'dosage' && <DosageChart patientId={patientId} />}

      {chartType === 'exams' && <ExamChart patientId={patientId} />}
    </Paper>
  );
};

export default CombinedChartView;
