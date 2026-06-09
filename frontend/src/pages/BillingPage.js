import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  Stack,
  Alert,
  LinearProgress,
  Divider
} from '@mui/material';
import { MonetizationOn, CheckCircle, Bolt } from '@mui/icons-material';
import { billingService } from '../services/api';

const BillingPage = () => {
  const [planos, setPlanos] = useState([]);
  const [faturas, setFaturas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [info, setInfo] = useState('');
  const [error, setError] = useState('');

  const carregar = async () => {
    setLoading(true);
    setError('');
    try {
      const [plansResp, invoicesResp] = await Promise.all([
        billingService.listarPlanos(),
        billingService.listarFaturas()
      ]);
      setPlanos(plansResp.planos || []);
      setFaturas(invoicesResp.faturas || []);
    } catch (err) {
      setError(err?.error || 'Não foi possível carregar billing.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    carregar();
  }, []);

  const formatPacientes = (limite) => {
    if (limite === null || limite === undefined || limite <= 0) {
      return 'Ilimitado';
    }
    return `ate ${limite}`;
  };

  const formatAgentes = (limite) => {
    if (limite === null || limite === undefined) {
      return 'Nao definido';
    }
    if (limite <= 0) {
      return 'Nenhum';
    }
    return `${limite}`;
  };

  const formatArmazenamento = (limiteMb) => {
    if (limiteMb === null || limiteMb === undefined) {
      return 'Nao definido';
    }
    if (limiteMb > 0 && limiteMb % 1024 === 0) {
      return `${limiteMb / 1024} GB`;
    }
    return `${limiteMb} MB`;
  };

  const assinar = async (planoId) => {
    try {
      setInfo('Gerando assinatura e cobrança...');
      const resp = await billingService.assinarPlano({ plano_id: planoId, metodo: 'pix' });
      setInfo(`Assinatura/trial criada. Fatura: ${resp?.fatura?.id || 'N/A'}`);
      await carregar();
    } catch (err) {
      setError(err?.error || 'Falha ao assinar plano.');
    }
  };

  const pagarFatura = async (faturaId) => {
    try {
      setInfo('Marcando fatura como paga (mock)...');
      await billingService.pagarFatura(faturaId);
      await carregar();
    } catch (err) {
      setError(err?.error || 'Falha ao pagar fatura.');
    }
  };

  return (
    <Box sx={{ py: 4 }}>
      <Stack direction="row" spacing={1} alignItems="center" mb={2}>
        <MonetizationOn color="success" />
        <Typography variant="h5">Planos e Cobranças</Typography>
        <Chip label="SaaS" size="small" color="success" />
      </Stack>
      <Typography variant="body1" color="text.secondary" mb={3}>
        Escolha um plano, gere cobrança (PIX/boleto/cartão) e acompanhe faturas. (Integração de gateway mockada.)
      </Typography>
      {loading && <LinearProgress sx={{ mb: 2 }} />}
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {info && <Alert severity="info" sx={{ mb: 2 }}>{info}</Alert>}

      <Grid container spacing={2}>
        {planos.map((plano) => (
          <Grid item xs={12} md={4} key={plano.id}>
            <Card variant="outlined">
              <CardContent>
                <Stack direction="row" spacing={1} alignItems="center" mb={1}>
                  <Bolt color="warning" />
                  <Typography variant="h6">{plano.nome}</Typography>
                </Stack>
                <Typography variant="h4" color="success.main">R${plano.preco_mensal}/mês</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ my: 1 }}>
                  {plano.descricao || 'Plano do AraOS — Clinical Intelligence Operating System'}
                </Typography>
                <Stack spacing={1}>
                  <Chip label={`Pacientes: ${formatPacientes(plano.limite_pacientes)}`} size="small" />
                  <Chip label={`Agentes IA: ${formatAgentes(plano.limite_agentes_ia)}`} size="small" />
                  <Chip label={`Armazenamento: ${formatArmazenamento(plano.limite_armazenamento_mb)}`} size="small" />
                </Stack>
              </CardContent>
              <CardActions>
                <Button fullWidth variant="contained" onClick={() => assinar(plano.id)}>
                  Assinar (PIX)
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Divider sx={{ my: 3 }} />
      <Typography variant="h6" gutterBottom>Faturas</Typography>
      {faturas.length === 0 ? (
        <Alert severity="info">Nenhuma fatura gerada.</Alert>
      ) : (
        <Stack spacing={1}>
          {faturas.map((f) => (
            <Paper key={f.id} variant="outlined" sx={{ p: 2 }}>
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} alignItems="center">
                <Typography flex={1}>
                  Fatura #{f.id} - R${f.valor} - Status: <strong>{f.status}</strong>
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Venc.: {f.vencimento ? new Date(f.vencimento).toLocaleDateString() : '-'}
                </Typography>
                {f.status !== 'paga' && (
                  <Button size="small" variant="contained" onClick={() => pagarFatura(f.id)}>
                    Marcar como paga
                  </Button>
                )}
                {f.status === 'paga' && <CheckCircle color="success" />}
              </Stack>
            </Paper>
          ))}
        </Stack>
      )}
    </Box>
  );
};

export default BillingPage;
