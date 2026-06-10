import React, { useState, useEffect } from 'react';
import {
  Box, Paper, Typography, CircularProgress, Alert,
  Chip, Divider, Grid, Card, CardContent
} from '@mui/material';
import {
  MedicalServices as MedicalIcon,
  Medication as MedIcon,
  History as HistoryIcon,
  Science as ScienceIcon,
  Warning as WarningIcon,
  Height as HeightIcon,
  Scale as ScaleIcon,
  LocalHospital as HospitalIcon
} from '@mui/icons-material';
import api from '../services/api';

const AnamneseViewer = ({ patientId }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [anamneses, setAnamneses] = useState([]);

  useEffect(() => {
    const fetchAnamneses = async () => {
      setLoading(true);
      try {
        const response = await api.get(`/anamneses/paciente/${patientId}`);
        if (response.data.success) {
          setAnamneses(response.data.anamneses || []);
        }
      } catch (err) {
        console.error('Erro ao carregar anamneses:', err);
        setError('Não foi possível carregar as anamneses');
      } finally {
        setLoading(false);
      }
    };
    if (patientId) fetchAnamneses();
  }, [patientId]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error" sx={{ m: 2 }}>{error}</Alert>;
  }

  if (anamneses.length === 0) {
    return (
      <Paper elevation={2} sx={{ p: 3, m: 1 }}>
        <Typography variant="body2" color="text.secondary" align="center">
          Nenhuma anamnese registrada para este paciente.
        </Typography>
      </Paper>
    );
  }

  const anamnese = anamneses[0]; // Mostrar a mais recente

  const InfoCard = ({ icon, title, value, color = 'primary' }) => (
    <Card variant="outlined" sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          {icon}
          <Typography variant="subtitle2" sx={{ ml: 1, fontWeight: 600 }}>
            {title}
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary">
          {value || 'Não informado'}
        </Typography>
      </CardContent>
    </Card>
  );

  return (
    <Paper elevation={2} sx={{ p: 3, m: 1 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" sx={{ fontWeight: 700 }}>
          <MedicalIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
          Anamnese
        </Typography>
        <Box>
          <Chip
            label={anamnese.fonte === 'lia' ? 'Coletada via LIA (WhatsApp)' : 'Entrada manual'}
            color={anamnese.fonte === 'lia' ? 'success' : 'default'}
            size="small"
          />
          {anamneses.length > 1 && (
            <Chip
              label={`${anamneses.length} registros`}
              size="small"
              sx={{ ml: 1 }}
            />
          )}
        </Box>
      </Box>

      <Typography variant="caption" color="text.secondary" sx={{ mb: 2, display: 'block' }}>
        Registrada em: {anamnese.data_anamnese ? new Date(anamnese.data_anamnese).toLocaleString('pt-BR') : 'Data não disponível'}
        {anamnese.profissional_nome && ` | Por: ${anamnese.profissional_nome}`}
      </Typography>

      <Divider sx={{ mb: 2 }} />

      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <InfoCard
            icon={<HospitalIcon color="primary" />}
            title="Condição Principal"
            value={anamnese.condicao_principal}
          />
        </Grid>
        <Grid item xs={12} md={6}>
          <InfoCard
            icon={<WarningIcon color="warning" />}
            title="Alergias"
            value={anamnese.alergias}
          />
        </Grid>
        <Grid item xs={12}>
          <InfoCard
            icon={<MedIcon color="info" />}
            title="Sintomas Atuais"
            value={anamnese.sintomas_atuais}
          />
        </Grid>
        <Grid item xs={12}>
          <InfoCard
            icon={<ScienceIcon color="secondary" />}
            title="Medicamentos em Uso"
            value={anamnese.medicamentos_uso}
          />
        </Grid>
        <Grid item xs={12} md={6}>
          <InfoCard
            icon={<HistoryIcon color="action" />}
            title="Histórico Cannabis"
            value={anamnese.historico_cannabis}
          />
        </Grid>
        <Grid item xs={12} md={6}>
          <InfoCard
            icon={<HistoryIcon color="action" />}
            title="Tratamentos Prévios"
            value={anamnese.tratamentos_previos}
          />
        </Grid>
        <Grid item xs={12}>
          <InfoCard
            icon={<ScienceIcon color="info" />}
            title="Exames Recentes"
            value={anamnese.exames_recentes}
          />
        </Grid>
        {(anamnese.peso || anamnese.altura) && (
          <>
            <Grid item xs={6} md={3}>
              <InfoCard
                icon={<ScaleIcon color="primary" />}
                title="Peso"
                value={anamnese.peso ? `${anamnese.peso} kg` : null}
              />
            </Grid>
            <Grid item xs={6} md={3}>
              <InfoCard
                icon={<HeightIcon color="primary" />}
                title="Altura"
                value={anamnese.altura ? `${anamnese.altura} m` : null}
              />
            </Grid>
          </>
        )}
      </Grid>

      {anamnese.telefone_origem && (
        <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
          Origem: WhatsApp {anamnese.telefone_origem}
        </Typography>
      )}
    </Paper>
  );
};

export default AnamneseViewer;
