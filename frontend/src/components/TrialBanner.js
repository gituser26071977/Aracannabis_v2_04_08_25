import React, { useState, useEffect } from 'react';
import { Box, Typography, Button, Chip } from '@mui/material';
import { AccessTime as AccessTimeIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const TrialBanner = () => {
  const navigate = useNavigate();
  const { currentUser } = useAuth();
  const [daysLeft, setDaysLeft] = useState(null);

  useEffect(() => {
    if (currentUser?.data_expiracao) {
      const exp = new Date(currentUser.data_expiracao);
      const now = new Date();
      const diffMs = exp - now;
      const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));
      setDaysLeft(diffDays);
    }
  }, [currentUser]);

  if (daysLeft === null) return null;
  if (currentUser?.role === 'admin' || currentUser?.role === 'superadmin') return null;

  const getColor = () => {
    if (daysLeft > 3) return 'success';
    if (daysLeft >= 1) return 'warning';
    return 'error';
  };

  const getBgColor = () => {
    if (daysLeft > 3) return 'rgba(76, 175, 80, 0.08)';
    if (daysLeft >= 1) return 'rgba(255, 152, 0, 0.08)';
    return 'rgba(244, 67, 54, 0.08)';
  };

  const getBorderColor = () => {
    if (daysLeft > 3) return 'rgba(76, 175, 80, 0.3)';
    if (daysLeft >= 1) return 'rgba(255, 152, 0, 0.3)';
    return 'rgba(244, 67, 54, 0.3)';
  };

  const getMessage = () => {
    if (daysLeft > 3) return `${daysLeft} dias restantes no trial`;
    if (daysLeft === 3) return `3 dias restantes no trial`;
    if (daysLeft === 2) return `2 dias restantes no trial`;
    if (daysLeft === 1) return `Último dia do trial`;
    if (daysLeft === 0) return `Seu trial expira hoje`;
    return `Trial expirado - Renove agora`;
  };

  return (
    <Box
      sx={{
        width: '100%',
        py: 1.5,
        px: 2,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 2,
        flexWrap: 'wrap',
        backgroundColor: getBgColor(),
        borderBottom: `1px solid ${getBorderColor()}`,
        backdropFilter: 'blur(8px)',
      }}
    >
      <AccessTimeIcon color={getColor()} fontSize="small" />
      <Typography variant="body2" fontWeight={600} color={`${getColor()}.dark`}>
        {getMessage()}
      </Typography>
      <Chip
        label={daysLeft > 0 ? `${daysLeft}d` : 'Expirado'}
        color={getColor()}
        size="small"
        sx={{ fontWeight: 700 }}
      />
      <Button
        variant="contained"
        size="small"
        color={getColor()}
        onClick={() => navigate('/planos')}
        sx={{ fontWeight: 600, textTransform: 'none', borderRadius: 2 }}
      >
        Escolher Plano
      </Button>
    </Box>
  );
};

export default TrialBanner;
