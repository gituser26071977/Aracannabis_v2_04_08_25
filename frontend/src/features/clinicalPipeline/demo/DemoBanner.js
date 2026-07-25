// DemoBanner — top banner that frames the page as a guided experience.
// Visually calm: emerald accent + soft background. Dismissable; remembers nothing.

import React from 'react';
import { Alert, Box, Stack, Typography, Button } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import ScienceIcon from '@mui/icons-material/Science';

export default function DemoBanner({ onClose }) {
  return (
    <Alert
      severity="info"
      icon={<ScienceIcon fontSize="small" />}
      sx={{
        mt: 1,
        mb: 2,
        backgroundColor: 'rgba(16, 185, 129, 0.06)',
        border: '1px solid rgba(16, 185, 129, 0.25)',
        '& .MuiAlert-icon': { color: '#10b981' },
      }}
      action={
        onClose ? (
          <Button size="small" onClick={onClose} startIcon={<CloseIcon fontSize="small" />}>
            Sair do demo
          </Button>
        ) : null
      }
    >
      <Stack direction={{ xs: 'column', md: 'row' }} spacing={1} alignItems={{ md: 'center' }}>
        <Box>
          <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
            Modo Demonstração · paciente exemplo
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Você está visualizando o pipeline clínico do AraOS com dados representativos.
            Nada é persistido. Os resultados são reproduzíveis (state_hash idêntico) e
            auditáveis.
          </Typography>
        </Box>
      </Stack>
    </Alert>
  );
}