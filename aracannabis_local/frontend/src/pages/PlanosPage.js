import React, { useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Alert,
  Divider,
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  CheckCircle as CheckIcon,
  School as SchoolIcon,
  Business as BusinessIcon,
  Star as StarIcon,
  Security as SecurityIcon,
  Schedule as ScheduleIcon,
  Payment as PaymentIcon
} from '@mui/icons-material';

const PlanosPage = () => {
  const [periodo, setPeriodo] = useState('mensal'); // mensal, trimestral, semestral, anual
  const [showInstitucional, setShowInstitucional] = useState(false);

  // Preços base
  const precoBase = 180.00;
  
  // Descontos
  const descontos = {
    mensal: 0,
    trimestral: 0.05, // 5%
    semestral: 0.08,  // 8%
    anual: 0.12       // 12%
  };

  // Multiplicadores de período
  const multiplicadores = {
    mensal: 1,
    trimestral: 3,
    semestral: 6,
    anual: 12
  };

  const calcularPreco = (periodo) => {
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

  const planos = [
    {
      id: 'free',
      nome: 'Plano Free',
      periodo: 'Permanente',
      preco: 0,
      popular: false,
      cor: '#ff9800',
      descricao: 'Versão gratuita com anúncios',
      recursos: [
        'Até 5 pacientes',
        'Funcionalidades básicas',
        'Anúncios de parceiros',
        'Suporte por email',
        'Backup manual'
      ]
    },
    {
      id: 'avaliacao',
      nome: 'Avaliação Gratuita',
      periodo: '7 dias',
      preco: 0,
      popular: false,
      cor: '#4caf50',
      descricao: 'Teste todas as funcionalidades',
      recursos: [
        'Acesso completo por 7 dias',
        'Até 10 pacientes',
        'Todas as funcionalidades',
        'Suporte por email',
        'Sem compromisso'
      ]
    },
    {
      id: 'profissional',
      nome: 'Profissional',
      periodo: periodo,
      preco: calcularPreco(periodo),
      popular: true,
      cor: '#2e7d32',
      descricao: 'Para profissionais de saúde',
      recursos: [
        'Pacientes ilimitados',
        'Todas as funcionalidades',
        'Backup automático',
        'Suporte prioritário',
        'Relatórios avançados',
        'Conformidade LGPD',
        'Atualizações incluídas'
      ]
    },
    {
      id: 'institucional',
      nome: 'Institucional',
      periodo: 'Gratuito',
      preco: 0,
      popular: false,
      cor: '#1976d2',
      descricao: 'Para instituições de ensino públicas',
      recursos: [
        'Acesso completo gratuito',
        'Para fins educacionais',
        'Múltiplos usuários',
        'Suporte dedicado',
        'Treinamento incluído',
        'Documentação completa'
      ]
    }
  ];

  const periodosDisponiveis = [
    { id: 'mensal', nome: '1 Mês', desconto: 0 },
    { id: 'trimestral', nome: '3 Meses', desconto: 5 },
    { id: 'semestral', nome: '6 Meses', desconto: 8 },
    { id: 'anual', nome: '12 Meses', desconto: 12 }
  ];

  const handleContratarPlano = (planoId) => {
    if (planoId === 'avaliacao') {
      // Redirecionar para cadastro
      window.location.href = '/cadastro-profissionais';
    } else if (planoId === 'institucional') {
      // Redirecionar para cadastro institucional
      window.location.href = '/cadastro-institucional';
    } else {
      // Redirecionar para pagamento
      window.location.href = `/pagamento?plano=${planoId}&periodo=${periodo}`;
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        {/* Header */}
        <Box sx={{ textAlign: 'center', mb: 6 }}>
          <Typography variant="h3" gutterBottom sx={{ fontWeight: 'bold', color: 'primary.main' }}>
            💰 Planos e Preços
          </Typography>
          <Typography variant="h6" color="text.secondary" paragraph>
            Escolha o plano ideal para suas necessidades
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Sistema completo de prontuário eletrônico para cannabis medicinal
          </Typography>
        </Box>

        {/* Seletor de Período */}
        <Box sx={{ textAlign: 'center', mb: 4 }}>
          <Typography variant="h6" gutterBottom>
            Período de Contratação
          </Typography>
          <Grid container spacing={2} justifyContent="center" sx={{ mb: 2 }}>
            {periodosDisponiveis.map((per) => (
              <Grid item key={per.id}>
                <Button
                  variant={periodo === per.id ? 'contained' : 'outlined'}
                  onClick={() => setPeriodo(per.id)}
                  sx={{ minWidth: 120 }}
                >
                  {per.nome}
                  {per.desconto > 0 && (
                    <Chip
                      label={`-${per.desconto}%`}
                      size="small"
                      color="secondary"
                      sx={{ ml: 1 }}
                    />
                  )}
                </Button>
              </Grid>
            ))}
          </Grid>
          
          <FormControlLabel
            control={
              <Switch
                checked={showInstitucional}
                onChange={(e) => setShowInstitucional(e.target.checked)}
              />
            }
            label="Mostrar plano institucional"
          />
        </Box>

        {/* Cards de Planos */}
        <Grid container spacing={4} justifyContent="center">
          {planos
            .filter(plano => showInstitucional || plano.id !== 'institucional')
            .map((plano) => (
            <Grid item xs={12} md={4} key={plano.id}>
              <Card
                elevation={plano.popular ? 8 : 2}
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  position: 'relative',
                  border: plano.popular ? `3px solid ${plano.cor}` : 'none',
                  transform: plano.popular ? 'scale(1.05)' : 'none'
                }}
              >
                {plano.popular && (
                  <Chip
                    label="MAIS POPULAR"
                    color="primary"
                    icon={<StarIcon />}
                    sx={{
                      position: 'absolute',
                      top: -12,
                      left: '50%',
                      transform: 'translateX(-50%)',
                      fontWeight: 'bold'
                    }}
                  />
                )}

                <CardContent sx={{ flexGrow: 1, textAlign: 'center' }}>
                  {/* Nome do Plano */}
                  <Typography variant="h5" gutterBottom sx={{ fontWeight: 'bold', color: plano.cor }}>
                    {plano.nome}
                  </Typography>
                  
                  <Typography variant="body2" color="text.secondary" paragraph>
                    {plano.descricao}
                  </Typography>

                  {/* Preço */}
                  <Box sx={{ my: 3 }}>
                    {plano.preco === 0 ? (
                      <Typography variant="h3" sx={{ fontWeight: 'bold', color: plano.cor }}>
                        GRATUITO
                      </Typography>
                    ) : (
                      <>
                        {plano.preco.desconto > 0 && (
                          <Typography variant="h6" sx={{ textDecoration: 'line-through', color: 'text.secondary' }}>
                            R$ {plano.preco.original.toFixed(2)}
                          </Typography>
                        )}
                        <Typography variant="h3" sx={{ fontWeight: 'bold', color: plano.cor }}>
                          R$ {plano.preco.final.toFixed(2)}
                        </Typography>
                        {plano.preco.desconto > 0 && (
                          <Chip
                            label={`Economia: R$ ${plano.preco.economia.toFixed(2)}`}
                            color="secondary"
                            size="small"
                            sx={{ mt: 1 }}
                          />
                        )}
                      </>
                    )}
                    <Typography variant="body2" color="text.secondary">
                      {plano.periodo === 'mensal' ? 'por mês' : 
                       plano.periodo === 'trimestral' ? 'por 3 meses' :
                       plano.periodo === 'semestral' ? 'por 6 meses' :
                       plano.periodo === 'anual' ? 'por 12 meses' :
                       plano.periodo}
                    </Typography>
                  </Box>

                  <Divider sx={{ my: 2 }} />

                  {/* Recursos */}
                  <List dense>
                    {plano.recursos.map((recurso, index) => (
                      <ListItem key={index} sx={{ px: 0 }}>
                        <ListItemIcon sx={{ minWidth: 32 }}>
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

                <CardActions sx={{ p: 2 }}>
                  <Button
                    fullWidth
                    variant="contained"
                    size="large"
                    onClick={() => handleContratarPlano(plano.id)}
                    sx={{
                      backgroundColor: plano.cor,
                      '&:hover': {
                        backgroundColor: plano.cor,
                        filter: 'brightness(0.9)'
                      }
                    }}
                    startIcon={
                      plano.id === 'avaliacao' ? <ScheduleIcon /> :
                      plano.id === 'institucional' ? <SchoolIcon /> :
                      <PaymentIcon />
                    }
                  >
                    {plano.id === 'avaliacao' ? 'Começar Avaliação' :
                     plano.id === 'institucional' ? 'Solicitar Acesso' :
                     'Contratar Agora'}
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>

        {/* Informações Importantes */}
        <Box sx={{ mt: 6 }}>
          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              <SecurityIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              Política de Dados e Segurança
            </Typography>
            <Typography variant="body2">
              • <strong>Backup automático:</strong> Seus dados são salvos automaticamente na nuvem<br/>
              • <strong>Retenção de dados:</strong> Mantemos seus dados seguros por 120 dias após o vencimento<br/>
              • <strong>Aviso de vencimento:</strong> Enviamos lembretes por email antes do vencimento<br/>
              • <strong>Período de graça:</strong> 30 dias adicionais para fazer backup após o vencimento<br/>
              • <strong>LGPD:</strong> Totalmente compatível com a Lei Geral de Proteção de Dados
            </Typography>
          </Alert>

          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" gutterBottom color="primary">
                    <BusinessIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                    Para Profissionais
                  </Typography>
                  <Typography variant="body2">
                    • Pagamento via Mercado Pago (cartão, PIX, boleto)<br/>
                    • Renovação automática opcional<br/>
                    • Nota fiscal eletrônica<br/>
                    • Suporte técnico prioritário<br/>
                    • Atualizações automáticas incluídas
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" gutterBottom color="primary">
                    <SchoolIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                    Para Instituições de Ensino
                  </Typography>
                  <Typography variant="body2">
                    • Acesso gratuito para instituições públicas<br/>
                    • Múltiplos usuários por instituição<br/>
                    • Treinamento e capacitação incluídos<br/>
                    • Suporte dedicado para educação<br/>
                    • Documentação completa para pesquisa
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Box>

        {/* FAQ Rápido */}
        <Box sx={{ mt: 4, textAlign: 'center' }}>
          <Typography variant="h6" gutterBottom>
            Dúvidas Frequentes
          </Typography>
          <Typography variant="body2" color="text.secondary">
            <strong>Posso cancelar a qualquer momento?</strong> Sim, sem multas ou taxas.<br/>
            <strong>Os dados ficam seguros?</strong> Sim, backup automático e criptografia.<br/>
            <strong>Há limite de pacientes?</strong> Não, pacientes ilimitados no plano profissional.<br/>
            <strong>Funciona offline?</strong> Algumas funcionalidades sim, sincroniza quando conecta.<br/>
            <strong>Tem suporte técnico?</strong> Sim, suporte por email e chat.
          </Typography>
        </Box>
      </Paper>
    </Container>
  );
};

export default PlanosPage;
