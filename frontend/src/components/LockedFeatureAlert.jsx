import React from 'react';
import { Box, Card, CardContent, Typography, Button, Stack, Chip } from '@mui/material';
import LockIcon from '@mui/icons-material/Lock';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import RefreshIcon from '@mui/icons-material/Refresh';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

/**
 * LockedFeatureAlert — banner de recurso bloqueado por gating de plano.
 *
 * Exibe mensagem explicando que o recurso está disponível apenas em planos
 * superiores, com dois CTAs:
 *   - Primário: "Ver Planos" (vai para /planos)
 *   - Secundário: "Já sou Premium" (recarrega o plano do user)
 *
 * Props:
 *   feature: string — nome amigável do recurso (ex: "Gestão da Clínica")
 *   planRequired: string — slug do plano necessário (ex: "premium")
 *   description: string — descrição opcional do que o recurso entrega
 *
 * Uso:
 *   <LockedFeatureAlert
 *     feature="Gestão da Clínica"
 *     planRequired="premium"
 *     description="Cadastre a clínica, gerencie profissionais e dispensa."
 *   />
 */
const LockedFeatureAlert = ({
  feature = 'Este recurso',
  planRequired = 'premium',
  description,
}) => {
  const navigate = useNavigate();
  const { refreshUserPlan } = useAuth();

  const planLabel = {
    basico: 'Básico',
    premium: 'Premium',
    enterprise: 'Enterprise',
  }[planRequired] || planRequired;

  const handleRefresh = async () => {
    await refreshUserPlan();
    // Recarrega a página para re-gating do conteúdo
    window.location.reload();
  };

  return (
    <Card
      sx={{
        background: (theme) =>
          `linear-gradient(135deg, ${theme.palette.primary.main}0A 0%, ${theme.palette.primary.light}05 100%)`,
        borderLeft: (theme) => `4px solid ${theme.palette.primary.main}`,
      }}
    >
      <CardContent>
        <Stack alignItems="center" spacing={3} sx={{ py: 4, px: 2, textAlign: 'center' }}>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 72,
              height: 72,
              borderRadius: '50%',
              bgcolor: (theme) => `${theme.palette.primary.main}15`,
              color: 'primary.main',
            }}
          >
            <LockIcon sx={{ fontSize: 40 }} />
          </Box>

          <Box>
            <Stack direction="row" spacing={1} alignItems="center" justifyContent="center" sx={{ mb: 1 }}>
              <Typography variant="h5" sx={{ fontWeight: 700 }}>
                🔒 {feature} bloqueado
              </Typography>
              <Chip
                label={planLabel}
                size="small"
                color="primary"
                variant="outlined"
                sx={{ fontWeight: 700 }}
              />
            </Stack>
            <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 560, mx: 'auto' }}>
              {description ||
                `Este recurso está disponível nos planos ${planLabel} e superiores.`}{' '}
              Faça upgrade do seu plano para liberá-lo.
            </Typography>
          </Box>

          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <Button
              variant="contained"
              size="large"
              endIcon={<ArrowForwardIcon />}
              onClick={() => navigate('/planos')}
            >
              Ver planos
            </Button>
            <Button
              variant="outlined"
              size="large"
              startIcon={<RefreshIcon />}
              onClick={handleRefresh}
            >
              Já sou {planLabel}
            </Button>
          </Stack>
        </Stack>
      </CardContent>
    </Card>
  );
};

export default LockedFeatureAlert;
