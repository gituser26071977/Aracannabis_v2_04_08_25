import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  CircularProgress,
  Alert,
  Slider,
  Container,
  Stack,
} from '@mui/material';
import { useParams } from 'react-router-dom';
import AutoAwesome from '@mui/icons-material/AutoAwesome';
import CheckCircle from '@mui/icons-material/CheckCircle';
import api from '../services/api';

const PreAtendimentoPage = () => {
  const { slug } = useParams();
  const [meta, setMeta] = useState(null);
  const [perguntas, setPerguntas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [sucesso, setSucesso] = useState(false);

  const [form, setForm] = useState({
    nome: '',
    telefone: '',
    cpf: '',
    email: '',
    data_nascimento: '',
    genero: '',
    intensidade: 5,
  });

  useEffect(() => {
    if (!slug) return;
    const load = async () => {
      setLoading(true);
      setError('');
      try {
        const r = await api.get(`/public/pre-atendimento/${slug}`);
        setMeta(r.data);
        setPerguntas(r.data?.questionario?.perguntas || []);
      } catch (e) {
        setError(e?.response?.data?.error || 'Instituto não encontrado.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [slug]);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const enviar = async () => {
    setEnviando(true);
    setError('');
    try {
      await api.post(`/public/pre-atendimento/${slug}`, {
        ...form,
        intensidade: String(form.intensidade),
      });
      setSucesso(true);
    } catch (e) {
      setError(e?.response?.data?.error || 'Erro ao enviar. Tente novamente.');
    } finally {
      setEnviando(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error && !meta) {
    return (
      <Container maxWidth="sm" sx={{ mt: 6 }}>
        <Alert severity="warning">{error}</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ py: 5 }}>
      <Paper elevation={3} sx={{ p: { xs: 3, md: 5 }, borderRadius: 3 }}>
        {sucesso ? (
          <Box textAlign="center" py={4}>
            <CheckCircle color="success" sx={{ fontSize: 64, mb: 2 }} />
            <Typography variant="h5" gutterBottom>
              Pré-atendimento recebido!
            </Typography>
            <Typography color="text.secondary">
              Obrigado, {form.nome.split(' ')[0]}! Suas informações foram enviadas com sucesso.
              Nossa equipe entrará em contato em breve.
            </Typography>
          </Box>
        ) : (
          <>
            <Stack direction="row" spacing={1.5} alignItems="center" mb={1}>
              <AutoAwesome color="primary" />
              <Typography variant="h5" sx={{ fontWeight: 700 }}>
                {meta?.instituto}
              </Typography>
            </Stack>
            <Typography color="text.secondary" gutterBottom mb={3}>
              {meta?.boas_vindas}
            </Typography>

            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Nome completo *"
                  fullWidth
                  value={form.nome}
                  onChange={set('nome')}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Telefone"
                  fullWidth
                  value={form.telefone}
                  onChange={set('telefone')}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField label="CPF" fullWidth value={form.cpf} onChange={set('cpf')} />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField label="E-mail" fullWidth value={form.email} onChange={set('email')} />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Data de nascimento"
                  type="date"
                  fullWidth
                  value={form.data_nascimento}
                  onChange={set('data_nascimento')}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField label="Gênero" fullWidth value={form.genero} onChange={set('genero')} />
              </Grid>

              {perguntas.map((q) => (
                <Grid item xs={12} key={q.key}>
                  <TextField
                    label={q.pergunta}
                    fullWidth
                    multiline
                    rows={2}
                    value={form[q.key] || ''}
                    onChange={(e) => setForm((f) => ({ ...f, [q.key]: e.target.value }))}
                  />
                </Grid>
              ))}

              <Grid item xs={12}>
                <Typography gutterBottom>
                  Intensidade do desconforto: {form.intensidade}/10
                </Typography>
                <Slider
                  value={Number(form.intensidade) || 0}
                  onChange={(_, v) => setForm((f) => ({ ...f, intensidade: v }))}
                  min={0}
                  max={10}
                  step={1}
                  marks
                  valueLabelDisplay="auto"
                />
              </Grid>
            </Grid>

            <Button
              variant="contained"
              size="large"
              fullWidth
              sx={{ mt: 3, py: 1.5, borderRadius: 2 }}
              onClick={enviar}
              disabled={enviando || !form.nome.trim()}
            >
              {enviando ? 'Enviando...' : 'Enviar pré-atendimento'}
            </Button>
          </>
        )}
      </Paper>
    </Container>
  );
};

export default PreAtendimentoPage;
