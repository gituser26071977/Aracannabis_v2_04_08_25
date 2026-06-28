import React, { useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  Button,
  Divider,
  Alert,
  CircularProgress,
  Chip,
  TextField,
  List,
  ListItem,
  ListItemIcon,
  ListItemText
} from '@mui/material';
import {
  Payment as PaymentIcon,
  CheckCircle as CheckIcon,
  CreditCard as CreditCardIcon,
  Pix as PixIcon,
  Receipt as BoletoIcon,
  ArrowBack as ArrowBackIcon,
  Security as SecurityIcon
} from '@mui/icons-material';
import { mercadopagoService } from '../services/api';

const PagamentoPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [nome, setNome] = useState('');
  const [email, setEmail] = useState('');
  const [telefone, setTelefone] = useState('');

  const planoParam = searchParams.get('plano') || 'sem_ia';
  const periodo = searchParams.get('periodo') || 'mensal';
  const categoria = searchParams.get('categoria') || 'medico';

  const planos = {
    sem_ia: {
      nome: 'Plano Sem IA',
      descricao: 'Prontuário completo sem recursos de IA',
      precoBase: 99.00,
      recursos: [
        'Pacientes ilimitados',
        'Sem agentes de IA',
        'Armazenamento de 5GB',
        'Backup automático',
        'Conformidade LGPD',
        'Atualizações incluídas'
      ]
    },
    com_ia: {
      nome: 'Plano Com IA',
      descricao: 'Prontuário completo com recursos de IA assistiva',
      precoBase: 250.00,
      recursos: [
        'Pacientes ilimitados',
        'Agentes de IA incluídos',
        'Armazenamento de 5GB',
        'Backup automático',
        'Relatórios avançados',
        'Conformidade LGPD',
        'Atualizações incluídas'
      ]
    }
  };

  const planoSelecionado = planos[planoParam] ? planoParam : 'sem_ia';
  const planoInfo = planos[planoSelecionado];

  // Configurações de preços e aplicação do desconto da categoria (60% para não médicos)
  const precoBase = categoria === 'outros' ? (planoInfo.precoBase || 99.00) * 0.6 : (planoInfo.precoBase || 99.00);

  // Descontos baseados no plano e período
  const getDesconto = (plano, periodo) => {
    if (periodo === 'mensal') return 0;
    if (periodo === 'trimestral') return 0.05;
    if (periodo === 'semestral') return 0.08;

    if (periodo === 'anual') {
      return plano === 'com_ia' ? 0.15 : 0.08;
    }
    return 0;
  };

  const multiplicadores = {
    mensal: 1,
    trimestral: 3,
    semestral: 6,
    anual: 12
  };

  const calcularPreco = () => {
    const precoSemDesconto = precoBase * multiplicadores[periodo];
    const desconto = getDesconto(planoSelecionado, periodo);
    const precoComDesconto = precoSemDesconto * (1 - desconto);
    return {
      original: precoSemDesconto,
      final: precoComDesconto,
      desconto: desconto * 100,
      economia: precoSemDesconto - precoComDesconto
    };
  };

  const precoInfo = calcularPreco();

  const periodoTexto = {
    mensal: '1 mês',
    trimestral: '3 meses',
    semestral: '6 meses',
    anual: '12 meses'
  };

  const handlePagamento = async (metodoPagamento) => {
    setError('');

    if (!nome.trim() || !email.trim()) {
      setError('Informe nome e email para continuar.');
      return;
    }

    setLoading(true);

    try {
      const dadosPagamento = {
        plano: planoSelecionado,
        periodo: periodo,
        categoria: categoria,
        nome: nome.trim(),
        email: email.trim(),
        telefone: telefone.trim(),
        metodo: metodoPagamento
      };

      const resp = await mercadopagoService.criarPreferenciaPublica(dadosPagamento);
      const redirectUrl = resp.sandbox ? resp.sandbox_init_point : resp.init_point;

      if (redirectUrl) {
        window.location.href = redirectUrl;
      } else {
        setError('Não foi possível iniciar o pagamento.');
      }

    } catch (err) {
      if(process.env.NODE_ENV!=='production')console.error('Erro no pagamento:', err);
      setError(err?.error || 'Erro ao processar pagamento. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/planos')}
            sx={{ mb: 2 }}
          >
            Voltar aos Planos
          </Button>

          <Box sx={{ textAlign: 'center' }}>
            <PaymentIcon sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
            <Typography variant="h4" gutterBottom>
              Finalizar Pagamento
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Complete sua assinatura do AraOS — Clinical Intelligence Operating System
            </Typography>
          </Box>
        </Box>

        <Grid container spacing={4}>
          {/* Resumo do Pedido */}
          <Grid item xs={12} md={6}>
            <Card elevation={2}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  📋 Resumo do Pedido
                </Typography>

                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                    {planoInfo.nome} {categoria === 'outros' && <Chip label="-40% Parceiro" color="success" size="small" sx={{ ml: 1 }} />}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {planoInfo.descricao}
                  </Typography>
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    Período: {periodoTexto[periodo]}
                  </Typography>
                </Box>

                <Divider sx={{ my: 2 }} />

                {/* Preço */}
                <Box sx={{ mb: 2 }}>
                  {precoInfo.desconto > 0 && (
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        Valor original:
                      </Typography>
                      <Typography variant="body2" sx={{ textDecoration: 'line-through' }}>
                        R$ {precoInfo.original.toFixed(2)}
                      </Typography>
                    </Box>
                  )}

                  {precoInfo.desconto > 0 && (
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2" color="success.main">
                        Desconto ({precoInfo.desconto}%):
                      </Typography>
                      <Typography variant="body2" color="success.main">
                        -R$ {precoInfo.economia.toFixed(2)}
                      </Typography>
                    </Box>
                  )}

                  <Divider sx={{ my: 1 }} />

                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                      Total:
                    </Typography>
                    <Typography variant="h6" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                      R$ {precoInfo.final.toFixed(2)}
                    </Typography>
                  </Box>
                </Box>

                {precoInfo.desconto > 0 && (
                  <Chip
                    label={`Você economiza R$ ${precoInfo.economia.toFixed(2)}`}
                    color="success"
                    size="small"
                    sx={{ mb: 2 }}
                  />
                )}

                <Divider sx={{ my: 2 }} />

                {/* Recursos inclusos */}
                <Typography variant="subtitle2" gutterBottom>
                  ✅ Incluído no plano:
                </Typography>
                <List dense>
                  {planoInfo.recursos.slice(0, 4).map((recurso, index) => (
                    <ListItem key={index} sx={{ px: 0, py: 0.5 }}>
                      <ListItemIcon sx={{ minWidth: 24 }}>
                        <CheckIcon color="success" fontSize="small" />
                      </ListItemIcon>
                      <ListItemText
                        primary={recurso}
                        primaryTypographyProps={{ variant: 'body2' }}
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>

          {/* Métodos de Pagamento */}
          <Grid item xs={12} md={6}>
            <Card elevation={2}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  💳 Escolha a forma de pagamento
                </Typography>

                <Box sx={{ mb: 2 }}>
                  <TextField
                    fullWidth
                    label="Nome completo"
                    margin="normal"
                    value={nome}
                    onChange={(e) => setNome(e.target.value)}
                    required
                  />
                  <TextField
                    fullWidth
                    label="Email"
                    type="email"
                    margin="normal"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                  <TextField
                    fullWidth
                    label="Telefone (opcional)"
                    margin="normal"
                    value={telefone}
                    onChange={(e) => setTelefone(e.target.value)}
                  />
                </Box>

                {error && (
                  <Alert severity="error" sx={{ mb: 3 }}>
                    {error}
                  </Alert>
                )}

                <Grid container spacing={2}>
                  {/* PIX */}
                  <Grid item xs={12}>
                    <Button
                      fullWidth
                      variant="outlined"
                      size="large"
                      onClick={() => handlePagamento('pix')}
                      disabled={loading}
                      startIcon={<PixIcon />}
                      sx={{
                        p: 2,
                        justifyContent: 'flex-start',
                        textAlign: 'left',
                        '&:hover': {
                          backgroundColor: 'primary.light',
                          color: 'white'
                        }
                      }}
                    >
                      <Box>
                        <Typography variant="subtitle1">PIX</Typography>
                        <Typography variant="body2" color="text.secondary">
                          Aprovação instantânea
                        </Typography>
                      </Box>
                    </Button>
                  </Grid>

                  {/* Cartão de Crédito */}
                  <Grid item xs={12}>
                    <Button
                      fullWidth
                      variant="outlined"
                      size="large"
                      onClick={() => handlePagamento('cartao')}
                      disabled={loading}
                      startIcon={<CreditCardIcon />}
                      sx={{
                        p: 2,
                        justifyContent: 'flex-start',
                        textAlign: 'left',
                        '&:hover': {
                          backgroundColor: 'primary.light',
                          color: 'white'
                        }
                      }}
                    >
                      <Box>
                        <Typography variant="subtitle1">Cartão de Crédito</Typography>
                        <Typography variant="body2" color="text.secondary">
                          Parcelamento disponível
                        </Typography>
                      </Box>
                    </Button>
                  </Grid>

                  {/* Boleto */}
                  <Grid item xs={12}>
                    <Button
                      fullWidth
                      variant="outlined"
                      size="large"
                      onClick={() => handlePagamento('boleto')}
                      disabled={loading}
                      startIcon={<BoletoIcon />}
                      sx={{
                        p: 2,
                        justifyContent: 'flex-start',
                        textAlign: 'left',
                        '&:hover': {
                          backgroundColor: 'primary.light',
                          color: 'white'
                        }
                      }}
                    >
                      <Box>
                        <Typography variant="subtitle1">Boleto Bancário</Typography>
                        <Typography variant="body2" color="text.secondary">
                          Vencimento em 3 dias úteis
                        </Typography>
                      </Box>
                    </Button>
                  </Grid>
                </Grid>

                {loading && (
                  <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
                    <CircularProgress />
                    <Typography variant="body2" sx={{ ml: 2, alignSelf: 'center' }}>
                      Processando pagamento...
                    </Typography>
                  </Box>
                )}

                {/* Informações de Segurança */}
                <Alert severity="info" sx={{ mt: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    <SecurityIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                    Pagamento Seguro
                  </Typography>
                  <Typography variant="body2">
                    • Processado pelo Mercado Pago<br />
                    • Dados criptografados SSL<br />
                    • Certificação PCI DSS<br />
                    • Nota fiscal eletrônica incluída
                  </Typography>
                </Alert>

                {/* Política de Cancelamento */}
                <Box sx={{ mt: 3, p: 2, backgroundColor: 'grey.50', borderRadius: 1 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    📋 Política de Cancelamento
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    • Cancele a qualquer momento sem multas<br />
                    • Reembolso proporcional se cancelar antes do vencimento<br />
                    • Dados mantidos seguros por 120 dias após cancelamento<br />
                    • Suporte disponível para dúvidas
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>
    </Container>
  );
};

export default PagamentoPage;
