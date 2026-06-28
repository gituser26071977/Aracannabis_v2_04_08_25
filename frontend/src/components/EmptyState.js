/**
 * EmptyState — Componente reutilizável para telas vazias.
 *
 * Uso:
 *   <EmptyState
 *     icon={<PeopleIcon />}
 *     title="Nenhum paciente cadastrado"
 *     description="Comece cadastrando seu primeiro paciente."
 *     actionLabel="Cadastrar paciente"
 *     onAction={() => navigate('/pacientes/novo')}
 *   />
 */
import React from 'react';
import { Box, Typography, Button, Paper } from '@mui/material';
import InboxOutlinedIcon from '@mui/icons-material/InboxOutlined';

const EmptyState = ({
  icon,
  title = 'Nada por aqui ainda',
  description,
  actionLabel,
  onAction,
  minHeight = 320,
}) => {
  return (
    <Paper
      variant="outlined"
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
        p: 4,
        minHeight,
        bgcolor: 'background.default',
      }}
    >
      <Box sx={{ color: 'text.disabled', mb: 2, fontSize: 64, lineHeight: 1 }}>
        {icon || <InboxOutlinedIcon fontSize="inherit" />}
      </Box>
      <Typography variant="h6" gutterBottom>
        {title}
      </Typography>
      {description && (
        <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 480, mb: actionLabel ? 3 : 0 }}>
          {description}
        </Typography>
      )}
      {actionLabel && onAction && (
        <Button variant="contained" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </Paper>
  );
};

export default EmptyState;
