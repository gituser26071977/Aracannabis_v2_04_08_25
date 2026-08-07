import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  TextField,
  Button,
  Stack,
  Alert,
  Chip,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  CircularProgress,
} from '@mui/material';
import { VerifiedUser, Save, UploadFile } from '@mui/icons-material';
import api from '../services/api';

function CertificacaoDigitalPage() {
  const [config, setConfig] = useState(null);
  const [form, setForm] = useState({
    provedor: 'birdid',
    client_id: '',
    client_secret: '',
    base_url: '',
  });
  const [saving, setSaving] = useState(false);
  const [signing, setSigning] = useState(false);
  const [tx, setTx] = useState(null); // { tcn, status }
  const [polling, setPolling] = useState(false);
  const [error, setError] = useState('');
  const [ok, setOk] = useState('');
  const [arquivo, setArquivo] = useState(null);

  useEffect(() => {
    api
      .get('/certificacao-digital/config')
      .then((r) => {
        if (r.data.config) {
          setConfig(r.data.config);
          setForm({
            provedor: r.data.config.provedor || 'birdid',
            client_id: r.data.config.client_id || '',
            client_secret: '',
            certificate_alias: r.data.config.certificate_alias || '',
            base_url: r.data.config.base_url || '',
          });
        }
      })
      .catch(() => {});
  }, []);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const salvar = async () => {
    setSaving(true);
    setError('');
    setOk('');
    try {
      const r = await api.post('/certificacao-digital/config', form);
      setConfig(r.data.config);
      setOk('Configuração salva.');
    } catch (e) {
      setError(e.response?.data?.error || 'Erro ao salvar');
    } finally {
      setSaving(false);
    }
  };

  const assinar = async () => {
    if (!arquivo) {
      setError('Selecione um PDF para assinar');
      return;
    }
    setSigning(true);
    setError('');
    setTx(null);
    const fd = new FormData();
    fd.append('file', arquivo);
    fd.append('provedor', form.provedor);
    try {
      const r = await api.post('/certificacao-digital/assinar', fd);
      setTx({ tcn: r.data.tcn, status: r.data.status });
      iniciarPolling(r.data.tcn);
    } catch (e) {
      setError(e.response?.data?.error || 'Erro ao iniciar assinatura');
    } finally {
      setSigning(false);
    }
  };

  const iniciarPolling = async (tcn) => {
    setPolling(true);
    for (let i = 0; i < 60; i++) {
      await new Promise((res) => setTimeout(res, 5000));
      try {
        const r = await api.get(`/certificacao-digital/assinatura/${tcn}`);
        const st = r.data.status_documento || r.data.transacao_status;
        setTx((t) => ({ ...t, status: st === 'SIGNED' ? 'assinado' : 'aguardando' }));
        if (st === 'SIGNED' || st === 'ERROR') break;
      } catch (e) {
        break;
      }
    }
    setPolling(false);
  };

  return (
    <Box p={3}>
      <Typography variant="h4" fontWeight={800} gutterBottom>
        <VerifiedUser sx={{ verticalAlign: 'middle', mr: 1 }} />
        Certificação Digital
      </Typography>
      <Typography color="text.secondary" gutterBottom>
        Assinatura digital de prescrições, laudos e relatórios via plataformas como Bird ID.
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card elevation={0} sx={{ border: '1px solid', borderColor: 'divider' }}>
            <CardContent>
              <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">Credenciais do provedor</Typography>
                {config && (
                  <Chip
                    size="small"
                    color={
                      config.status === 'ativo'
                        ? 'success'
                        : config.status === 'erro'
                          ? 'error'
                          : 'warning'
                    }
                    label={config.status || 'pendente'}
                  />
                )}
              </Stack>
              <Stack spacing={2}>
                <FormControl fullWidth size="small">
                  <InputLabel>Provedor</InputLabel>
                  <Select value={form.provedor} label="Provedor" onChange={set('provedor')}>
                    <MenuItem value="birdid">Bird ID</MenuItem>
                    <MenuItem value="valid">Valid (em breve)</MenuItem>
                  </Select>
                </FormControl>
                <TextField
                  size="small"
                  label="Client ID"
                  value={form.client_id}
                  onChange={set('client_id')}
                />
                <TextField
                  size="small"
                  label="Client Secret"
                  type="password"
                  value={form.client_secret}
                  placeholder={config ? '(deixe vazio para manter o atual)' : ''}
                  onChange={set('client_secret')}
                />
                <TextField
                  size="small"
                  label="Base URL (opcional, sandbox)"
                  value={form.base_url}
                  onChange={set('base_url')}
                />
                {error && <Alert severity="error">{error}</Alert>}
                {ok && <Alert severity="success">{ok}</Alert>}
                <Button
                  variant="contained"
                  startIcon={<Save />}
                  onClick={salvar}
                  disabled={saving || !form.client_id || !form.client_secret}
                >
                  {saving ? 'Salvando…' : 'Salvar configuração'}
                </Button>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card elevation={0} sx={{ border: '1px solid', borderColor: 'divider' }}>
            <CardContent>
              <Typography variant="h6" mb={1}>
                Assinar um documento
              </Typography>
              <Stack direction="row" spacing={1} mb={2}>
                <Button component="label" variant="outlined" startIcon={<UploadFile />}>
                  Escolher PDF
                  <input
                    type="file"
                    accept="application/pdf"
                    hidden
                    onChange={(e) => {
                      setArquivo(e.target.files?.[0] || null);
                    }}
                  />
                </Button>
                <Button
                  variant="contained"
                  onClick={assinar}
                  disabled={signing || polling || !arquivo}
                >
                  {signing ? 'Enviando…' : 'Assinar'}
                </Button>
              </Stack>
              {arquivo && (
                <Typography variant="body2" color="text.secondary">
                  {arquivo.name}
                </Typography>
              )}
              {(signing || polling) && <CircularProgress size={20} sx={{ mt: 1 }} />}
              {tx && (
                <Alert severity={tx.status === 'assinado' ? 'success' : 'info'} sx={{ mt: 1 }}>
                  <b>Assinatura {tx.status === 'assinado' ? 'concluída' : 'em andamento'}.</b>
                  <br />
                  {tx.status === 'assinado' ? (
                    <a href={`/api/certificacao-digital/assinatura/${tx.tcn}/download`}>
                      Baixar PDF assinado
                    </a>
                  ) : (
                    'Valide no aplicativo Bird ID (push/QR) para concluir.'
                  )}
                </Alert>
              )}
              <Alert severity="info" sx={{ mt: 2 }}>
                A prescrição, laudo ou relatório é enviada à plataforma (Bird ID), onde o
                profissional conclui a assinatura digital. Documentos assinados ficam com validade
                jurídica (MP 2.200-2/2001).
              </Alert>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default CertificacaoDigitalPage;
