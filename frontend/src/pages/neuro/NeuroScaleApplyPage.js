/**
 * NeuroScaleApplyPage — Aplicação de Escala (Sprint 1)
 *
 * Renderiza dinamicamente o formulário a partir do JSON Schema da escala
 * (suporta qualquer escala do registry sem deploy de FE).
 *
 * Rota: /neuro/scales/:code
 */

import React, { useEffect, useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Chip,
  Stack,
  Typography,
  TextField,
  Button,
  RadioGroup,
  FormControlLabel,
  Radio,
  Alert,
  Divider,
  CircularProgress,
  Paper,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';

import { getScaleSpec, applyScale } from '../../services/neuroService';
import { useNotifier } from '../../hooks/useNotifier';
import PageHeader from '../../components/PageHeader';
import LoadingState from '../../components/LoadingState';
import ErrorBoundary from '../../components/ErrorBoundary';

const LIKERT_OPTIONS = [
  { value: 0, label: 'Nenhuma' },
  { value: 1, label: 'Vários dias' },
  { value: 2, label: 'Mais da metade dos dias' },
  { value: 3, label: 'Quase todos os dias' },
];

const NeuroScaleApplyPage = () => {
  const { code } = useParams();
  const navigate = useNavigate();
  const { notifySuccess, notifyError } = useNotifier();

  const [spec, setSpec] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [responses, setResponses] = useState({});
  const [patientId, setPatientId] = useState('');
  const [result, setResult] = useState(null);

  // Carrega spec da escala
  useEffect(() => {
    const carregar = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getScaleSpec(code);
        setSpec(data);
        // Inicializa respostas com null
        const initial = {};
        Object.keys(data.json_schema?.properties || {}).forEach((k) => {
          initial[k] = null;
        });
        setResponses(initial);
      } catch (err) {
        setError(err?.response?.data?.message || err?.message || 'Erro ao carregar escala');
      } finally {
        setLoading(false);
      }
    };
    carregar();
  }, [code]);

  const properties = useMemo(
    () => spec?.json_schema?.properties || {},
    [spec]
  );
  const requiredFields = useMemo(
    () => spec?.json_schema?.required || [],
    [spec]
  );

  const isComplete = useMemo(() => {
    return requiredFields.every((f) => responses[f] !== null && responses[f] !== undefined);
  }, [requiredFields, responses]);

  const handleSubmit = async () => {
    if (!patientId.trim()) {
      notifyError('Informe o ID do paciente');
      return;
    }
    if (!isComplete) {
      notifyError('Responda todas as questões');
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const data = await applyScale(code, {
        patient_id: patientId.trim(),
        raw_responses: responses,
      });
      setResult(data);
      notifySuccess(`Escala ${code} aplicada com sucesso`);
    } catch (err) {
      const msg = err?.response?.data?.message || err?.message || 'Erro ao aplicar escala';
      setError(msg);
      notifyError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <LoadingState message={`Carregando ${code}...`} />;
  if (!spec) {
    return (
      <Alert severity="error" sx={{ m: 3 }}>
        {error || 'Escala não encontrada'}
      </Alert>
    );
  }

  // Exibe resultado após submissão
  if (result) {
    const interp = result.interpretation?.total || {};
    return (
      <Box sx={{ p: 3 }}>
        <PageHeader
          title={`${spec.code} — Resultado`}
          subtitle={spec.name}
          actions={
            <Button
              startIcon={<ArrowBackIcon />}
              onClick={() => navigate('/neuro/scales')}
              variant="outlined"
            >
              Voltar ao catálogo
            </Button>
          }
        />
        <Card sx={{ mb: 2, borderTop: `4px solid ${interp.color || '#0d7377'}` }}>
          <CardContent>
            <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
              <Chip label={spec.code} color="primary" />
              <Chip label={`v${spec.scale_version}`} variant="outlined" />
              <Chip
                label={interp.band || '—'}
                sx={{ backgroundColor: interp.color, color: '#fff' }}
              />
            </Stack>
            <Typography variant="h4" sx={{ mb: 1 }}>
              Escore Total: {Object.values(result.computed_scores)[0]}
            </Typography>
            <Typography variant="h6" sx={{ mb: 2 }}>
              {interp.label_pt}
            </Typography>
            <Divider sx={{ my: 2 }} />
            <Typography variant="body1" sx={{ whiteSpace: 'pre-line' }}>
              {interp.recommendation}
            </Typography>
            {interp.references?.length > 0 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="caption" color="text.secondary">
                  Referências: {interp.references.join('; ')}
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
        <Alert severity="info">
          Resposta gravada (id: <code>{result.id}</code>). Disponível no
          histórico clínico do paciente.
        </Alert>
      </Box>
    );
  }

  // Formulário dinâmico
  return (
    <ErrorBoundary>
      <Box sx={{ p: 3 }}>
        <PageHeader
          title={`${spec.code} — ${spec.name}`}
          subtitle={`v${spec.version} · ${spec.author}`}
          actions={
            <Button
              startIcon={<ArrowBackIcon />}
              onClick={() => navigate('/neuro/scales')}
              variant="outlined"
            >
              Voltar
            </Button>
          }
        />

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Paper sx={{ p: 2, mb: 2 }}>
          <Typography variant="caption" color="text.secondary">
            {spec.scientific_reference}
          </Typography>
        </Paper>

        <Card sx={{ mb: 2 }}>
          <CardContent>
            <TextField
              fullWidth
              label="ID do Paciente"
              value={patientId}
              onChange={(e) => setPatientId(e.target.value)}
              required
              helperText="UUID do paciente (Sistema AraOS) ou ID interno"
            />
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Stack spacing={3}>
              {Object.entries(properties).map(([key, prop]) => {
                const value = responses[key];
                const isLikert = prop.type === 'integer' && prop.minimum === 0 && prop.maximum === 3;

                return (
                  <Box key={key}>
                    <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 500 }}>
                      {prop.title || key}
                      {requiredFields.includes(key) && (
                        <Typography component="span" color="error" sx={{ ml: 0.5 }}>
                          *
                        </Typography>
                      )}
                    </Typography>
                    {prop.description && (
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        {prop.description}
                      </Typography>
                    )}
                    {isLikert ? (
                      <RadioGroup
                        row
                        value={value ?? ''}
                        onChange={(e) =>
                          setResponses((prev) => ({ ...prev, [key]: Number(e.target.value) }))
                        }
                      >
                        {LIKERT_OPTIONS.map((opt) => (
                          <FormControlLabel
                            key={opt.value}
                            value={String(opt.value)}
                            control={<Radio />}
                            label={opt.label}
                          />
                        ))}
                      </RadioGroup>
                    ) : (
                      <TextField
                        type="number"
                        value={value ?? ''}
                        onChange={(e) =>
                          setResponses((prev) => ({ ...prev, [key]: Number(e.target.value) }))
                        }
                        inputProps={{
                          min: prop.minimum,
                          max: prop.maximum,
                        }}
                        sx={{ width: 200 }}
                      />
                    )}
                  </Box>
                );
              })}
            </Stack>
          </CardContent>
        </Card>

        <Box sx={{ mt: 3, display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
          <Button
            variant="outlined"
            onClick={() => navigate('/neuro/scales')}
            disabled={submitting}
          >
            Cancelar
          </Button>
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={!isComplete || !patientId.trim() || submitting}
            startIcon={submitting ? <CircularProgress size={16} /> : null}
          >
            {submitting ? 'Aplicando...' : 'Aplicar Escala'}
          </Button>
        </Box>
      </Box>
    </ErrorBoundary>
  );
};

export default NeuroScaleApplyPage;