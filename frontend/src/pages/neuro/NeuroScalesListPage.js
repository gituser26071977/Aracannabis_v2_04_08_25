/**
 * NeuroScalesListPage — Catálogo de Escalas Neuropsicológicas (Sprint 1)
 *
 * Lista todas as escalas disponíveis no registry plugin-based.
 * Filtros: idade (meses), busca textual.
 *
 * Rota: /neuro/scales
 */

import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Chip,
  Grid,
  IconButton,
  InputAdornment,
  Stack,
  TextField,
  Typography,
  Tooltip,
  Button,
  CircularProgress,
  Alert,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import ScienceIcon from '@mui/icons-material/Science';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import ChildCareIcon from '@mui/icons-material/ChildCare';

import { listCatalog } from '../../services/neuroService';
import PageHeader from '../../components/PageHeader';
import LoadingState from '../../components/LoadingState';
import EmptyState from '../../components/EmptyState';
import ErrorBoundary from '../../components/ErrorBoundary';

const formatAge = (target) => {
  if (!target) return '—';
  const { min, max } = target;
  const fmt = (months) => {
    if (months === null || months === undefined) return '∞';
    if (months < 24) return `${months}m`;
    const years = Math.floor(months / 12);
    const rem = months % 12;
    return rem === 0 ? `${years}a` : `${years}a${rem}m`;
  };
  return `${fmt(min)} – ${fmt(max)}`;
};

const NeuroScalesListPage = () => {
  const navigate = useNavigate();
  const [scales, setScales] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [ageMonths, setAgeMonths] = useState('');

  const carregar = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (ageMonths !== '' && !Number.isNaN(Number(ageMonths))) {
        params.ageMonths = Number(ageMonths);
      }
      const data = await listCatalog(params);
      setScales(data.scales || []);
    } catch (err) {
      setError(err?.response?.data?.message || err?.message || 'Erro ao carregar catálogo');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    carregar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const filtered = useMemo(() => {
    if (!search.trim()) return scales;
    const q = search.toLowerCase();
    return scales.filter(
      (s) =>
        s.code.toLowerCase().includes(q) ||
        s.name.toLowerCase().includes(q) ||
        (s.author || '').toLowerCase().includes(q)
    );
  }, [scales, search]);

  if (loading) return <LoadingState message="Carregando catálogo de escalas..." />;

  return (
    <ErrorBoundary>
      <Box sx={{ p: 3 }}>
        <PageHeader
          title="Escalas Neuropsicológicas"
          subtitle="Módulo NEURODESENVOLVIMENTO — plugin registry"
          icon={<ScienceIcon />}
          actions={
            <Stack direction="row" spacing={1}>
              <TextField
                size="small"
                label="Idade (meses)"
                value={ageMonths}
                onChange={(e) => setAgeMonths(e.target.value.replace(/\D/g, ''))}
                sx={{ width: 140 }}
              />
              <TextField
                size="small"
                placeholder="Buscar..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon fontSize="small" />
                    </InputAdornment>
                  ),
                }}
                sx={{ width: 240 }}
              />
              <Button variant="outlined" onClick={carregar}>
                Atualizar
              </Button>
            </Stack>
          }
        />

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {filtered.length === 0 ? (
          <EmptyState
            title="Nenhuma escala encontrada"
            description="Ajuste os filtros ou verifique se o registry está carregado."
          />
        ) : (
          <Grid container spacing={2}>
            {filtered.map((scale) => (
              <Grid item xs={12} sm={6} md={4} key={`${scale.code}-${scale.version}`}>
                <Card
                  sx={{
                    cursor: 'pointer',
                    height: '100%',
                    transition: 'transform 0.15s, box-shadow 0.15s',
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      boxShadow: 4,
                    },
                  }}
                  onClick={() => navigate(`/neuro/scales/${scale.code}`)}
                >
                  <CardContent>
                    <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
                      <Chip
                        label={scale.code}
                        size="small"
                        color="primary"
                        sx={{ fontWeight: 600 }}
                      />
                      <Chip
                        label={`v${scale.version}`}
                        size="small"
                        variant="outlined"
                      />
                      {scale.requires_training && (
                        <Chip label="Treinamento" size="small" color="warning" />
                      )}
                    </Stack>
                    <Typography variant="h6" sx={{ mb: 1 }}>
                      {scale.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
                      {scale.description || scale.author}
                    </Typography>
                    <Stack direction="row" spacing={2} sx={{ color: 'text.secondary' }}>
                      <Tooltip title="Faixa etária">
                        <Stack direction="row" alignItems="center" spacing={0.5}>
                          <ChildCareIcon fontSize="small" />
                          <Typography variant="caption">
                            {formatAge(scale.target_age_months)}
                          </Typography>
                        </Stack>
                      </Tooltip>
                      <Tooltip title="Tempo de administração">
                        <Stack direction="row" alignItems="center" spacing={0.5}>
                          <AccessTimeIcon fontSize="small" />
                          <Typography variant="caption">
                            ~{scale.administration_time_min} min
                          </Typography>
                        </Stack>
                      </Tooltip>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </Box>
    </ErrorBoundary>
  );
};

export default NeuroScalesListPage;