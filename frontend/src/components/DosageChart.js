import React from 'react';
import { Box, Paper, Typography } from '@mui/material';
import DosageLineChart from './DosageLineChart';

const DosageChart = ({ patientId }) => {
  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Gráfico de Dosagens
      </Typography>
      <Box sx={{ height: 400 }}>
        <DosageLineChart patientId={patientId} />
      </Box>
    </Paper>
  );
};

export default DosageChart;
