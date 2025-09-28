import React, { useState, useEffect } from 'react';
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

const PagamentoPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const plano = searchParams.get('plano') || 'profissional';
  const periodo = searchParams.get('periodo') || 'mensal';

  // Configurações de preços
  const precoBase = 180.00;
  const descontos = {
    mensal: 0,
    trimestral: 0.05,
    semestral: 0.08,
    anual: 0.12
  };
  const multiplicadores = {
    mensal: 1,
    trimestral: 3,
    semestral: 6,
    anual: 12
  };

  const calcularPreco = () => {
    const precoSemDesconto = precoBase * multiplicadores[periodo];
    const desconto = descontos[periodo];
    const precoComDesconto = precoSemDesconto * (1 - desconto);
    return {
      original: precoSemDesconto,
      final: precoComDesconto,
      desconto: desconto * 100,
      economia: precoSemDesconto - precoComDesconto
    };
  };

  const precoInfo = calcularPreco();

  const planoInfo = {
    nome: 'Plano Profissional',
    descricao: 'Acesso completo ao sistema Aracannabis',
    recursos: [
      'Pacientes ilimitados',
      'Todas as funcionalidades',
      'Backup automático',
      'Suporte prioritário',
      'Relatórios avançados',
      'Conformidade LGPD',
      'Atualizações incluídas'
    ]
  };

  const periodoTexto = {
    mensal: '1 mês',
    trimestral: '3 meses',
    semestral: '6 meses',
    anual: '12 meses'
  };

  const handlePagamento = async (metodoPagamento) => {
    setLoading(true);
    setError('');

    try {
      // Simular criação de preferência no Mercado Pago
      // Em produção, isso seria uma chamada para o backend
      
      // Dados do pagamento
      const dadosPagamento = {
        plano: plano,
        periodo: periodo,
        valor: precoInfo.final,
        metodo: metodoPagamento,
        descricao: `${planoInfo.nome} - ${periodoTexto[periodo]}`
      };

      console.log('Iniciando pagamento:', dadosPagamento);

      // Simular delay da API
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Em produção, aqui seria redirecionado para o Mercado Pago
      if (metodoPagamento === 'pix') {
        // Simular PIX
        alert(`PIX gerado!\n\nValor: R$ ${precoInfo.final.toFixed(2)}\nChave PIX: 12345678901\n\nCopie e cole no seu app bancário.`);
      } else if (metodoPagamento === 'boleto') {
        // Simular Boleto
        alert(`Boleto gerado!\n\nValor: R$ ${precoInfo.final.toFixed(2)}\nVencimento: 3 dias úteis\n\nO boleto será enviado por email.`);
      } else {
        // Simular Cartão
        alert(`Redirecionando para pagamento com cartão...\n\nValor: R$ ${precoInfo.final.toFixed(2)}\n\nVocê será redirecionado para o Mercado Pago.`);
      }

      // Redirecionar para página de sucesso (simulado)
      navigate('/pagamento-sucesso');

    } catch (err) {
      console.error('Erro no pagamento:', err);
      setError('Erro ao processar pagamento. Tente novamente.');
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
              Complete sua assinatura do sistema Aracannabis
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
                    {planoInfo.nome}
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
                    • Processado pelo Mercado Pago<br/>
                    • Dados criptografados SSL<br/>
                    • Certificação PCI DSS<br/>
                    • Nota fiscal eletrônica incluída
                  </Typography>
                </Alert>

                {/* Política de Cancelamento */}
                <Box sx={{ mt: 3, p: 2, backgroundColor: 'grey.50', borderRadius: 1 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    📋 Política de Cancelamento
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    • Cancele a qualquer momento sem multas<br/>
                    • Reembolso proporcional se cancelar antes do vencimento<br/>
                    • Dados mantidos seguros por 120 dias após cancelamento<br/>
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
