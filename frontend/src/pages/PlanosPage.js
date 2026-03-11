import React, { useState, useEffect } from 'react';
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
  CircularProgress,
  ToggleButton,
  ToggleButtonGroup
} from '@mui/material';
import {
  CheckCircle as CheckIcon,
  Business as BusinessIcon,
  Star as StarIcon,
  Security as SecurityIcon,
  Payment as PaymentIcon
} from '@mui/icons-material';
import api from '../services/api';

const PlanosPage = () => {
  const [periodo, setPeriodo] = useState('mensal'); // mensal, trimestral, semestral, anual
  const [categoria, setCategoria] = useState('medico'); // medico, outros
  const [loading, setLoading] = useState(true);
  const [planosDb, setPlanosDb] = useState([]);
  const [error, setError] = useState(null);

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

  // Recursos padrão por tipo de plano (Fallback para melhorar visualização)
  const featuresMap = {
    'Plano Sem IA': [
      'Pacientes ilimitados',
      'Sem agentes de IA',
      'Armazenamento de 5GB',
      'Backup automático',
      'Conformidade LGPD',
      'Atualizações incluídas'
    ],
    'Plano Com IA': [
      'Pacientes ilimitados',
      'Agentes de IA incluídos',
      'Armazenamento de 10GB',
      'Backup automático',
      'Suporte prioritário',
      'Relatórios avançados',
      'Conformidade LGPD',
      'Atualizações incluídas'
    ]
  };

  useEffect(() => {
    fetchPlanos();
  }, []);

  const fetchPlanos = async () => {
    try {
      const response = await api.get('/planos/'); // Rota pública
      setPlanosDb(response.data);
    } catch (err) {
      console.error('Erro ao buscar planos:', err);
      // Fallback local se API falhar, para não mostrar tela branca
      setError('Não foi possível carregar os preços atualizados. Exibindo valores padrão.');
      // O mock será usado se planosDb estiver vazio, mas aqui tratamos o erro
    } finally {
      setLoading(false);
    }
  };

  const calcularPreco = (precoMensalBase, periodoSelecionado, categoriaSelecionada) => {
    // Aplica desconto de categoria (Outros profissionais pagam 60% do valor)
    const precoBaseCorrigido = categoriaSelecionada === 'outros' ? precoMensalBase * 0.6 : precoMensalBase;

    const precoSemDesconto = precoBaseCorrigido * multiplicadores[periodoSelecionado];
    const desconto = descontos[periodoSelecionado];
    const precoComDesconto = precoSemDesconto * (1 - desconto);

    return {
      original: precoSemDesconto,
      final: precoComDesconto,
      desconto: desconto * 100,
      economia: precoSemDesconto - precoComDesconto
    };
  };

  const periodosDisponiveis = [
    { id: 'mensal', nome: '1 Mês', desconto: 0 },
    { id: 'trimestral', nome: '3 Meses', desconto: 5 },
    { id: 'semestral', nome: '6 Meses', desconto: 8 },
    { id: 'anual', nome: '12 Meses', desconto: 12 }
  ];

  const handleContratarPlano = (plano) => {
    window.location.href = `/pagamento?plano=${plano.id}&periodo=${periodo}&categoria=${categoria}`;
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 10 }}>
        <CircularProgress />
      </Box>
    );
  }

  // Se a API não retornou nada, usar um fallback visual ou mensagem
  const planosParaExibir = planosDb.length > 0 ? planosDb : [];

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

        {error && <Alert severity="warning" sx={{ mb: 4 }}>{error}</Alert>}

        {/* Seletor de Categoria e Período */}
        <Box sx={{ textAlign: 'center', mb: 4 }}>
          <Box sx={{ mb: 4 }}>
            <Typography variant="subtitle1" gutterBottom fontWeight="bold">
              Qual é a sua profissão?
            </Typography>
            <ToggleButtonGroup
              color="primary"
              value={categoria}
              exclusive
              onChange={(e, newCat) => { if (newCat) setCategoria(newCat); }}
              aria-label="Categoria Profissional"
            >
              <ToggleButton value="medico" sx={{ px: 4 }}>
                Médico(a)
              </ToggleButton>
              <ToggleButton value="outros" sx={{ px: 4 }}>
                Outros Profissionais de Saúde<br />
                <Typography variant="caption" color="success.main" fontWeight="bold">
                  (-40% OFF)
                </Typography>
              </ToggleButton>
            </ToggleButtonGroup>
          </Box>

          <Typography variant="subtitle1" gutterBottom fontWeight="bold">
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
        </Box>

        {/* Cards de Planos */}
        {planosParaExibir.length === 0 ? (
          <Box textAlign="center" py={5}>
            <Typography variant="h6" color="text.secondary">Nenhum plano disponível no momento.</Typography>
          </Box>
        ) : (
          <Grid container spacing={4} justifyContent="center">
            {planosParaExibir.map((plano) => {
              const preco = calcularPreco(plano.preco_mensal, periodo, categoria);
              const recursos = featuresMap[plano.nome] || [plano.descricao]; // Fallback para descrição se não mapeado

              return (
                <Grid item xs={12} md={4} key={plano.id}>
                  <Card
                    elevation={plano.is_popular ? 8 : 2}
                    sx={{
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      position: 'relative',
                      border: plano.is_popular ? `3px solid ${plano.cor || '#2e7d32'}` : 'none',
                      transform: plano.is_popular ? 'scale(1.05)' : 'none'
                    }}
                  >
                    {plano.is_popular && (
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
                      <Typography variant="h5" gutterBottom sx={{ fontWeight: 'bold', color: plano.cor || 'primary.main' }}>
                        {plano.nome}
                      </Typography>

                      <Typography variant="body2" color="text.secondary" paragraph sx={{ minHeight: 40 }}>
                        {plano.descricao}
                      </Typography>

                      {/* Preço */}
                      <Box sx={{ my: 3 }}>
                        {plano.preco_mensal === 0 ? (
                          <Typography variant="h3" sx={{ fontWeight: 'bold', color: plano.cor }}>
                            GRATUITO
                          </Typography>
                        ) : (
                          <>
                            {preco.desconto > 0 && (
                              <Typography variant="h6" sx={{ textDecoration: 'line-through', color: 'text.secondary' }}>
                                R$ {preco.original.toFixed(2)}
                              </Typography>
                            )}
                            <Typography variant="h3" sx={{ fontWeight: 'bold', color: plano.cor || 'primary.main' }}>
                              R$ {preco.final.toFixed(2)}
                            </Typography>
                            {preco.desconto > 0 && (
                              <Chip
                                label={`Economia: R$ ${preco.economia.toFixed(2)}`}
                                color="secondary"
                                size="small"
                                sx={{ mt: 1 }}
                              />
                            )}
                          </>
                        )}
                        <Typography variant="body2" color="text.secondary">
                          {periodo === 'mensal' ? 'por mês' :
                            periodo === 'trimestral' ? 'por 3 meses' :
                              periodo === 'semestral' ? 'por 6 meses' :
                                periodo === 'anual' ? 'por 12 meses' :
                                  periodo}
                        </Typography>
                      </Box>

                      <Divider sx={{ my: 2 }} />

                      <List dense>
                        {recursos.map((recurso, index) => (
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
                        onClick={() => handleContratarPlano(plano)}
                        sx={{
                          backgroundColor: plano.cor || 'primary.main',
                          '&:hover': {
                            backgroundColor: plano.cor || 'primary.dark',
                            filter: 'brightness(0.9)'
                          }
                        }}
                        startIcon={<PaymentIcon />}
                      >
                        Contratar Agora
                      </Button>
                    </CardActions>
                  </Card>
                </Grid>
              );
            })}
          </Grid>
        )}

        {/* Informações Importantes - Fixo */}
        <Box sx={{ mt: 6 }}>
          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              <SecurityIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              Política de Dados e Segurança
            </Typography>
            <Typography variant="body2">
              • <strong>Backup automático:</strong> Seus dados são salvos automaticamente na nuvem<br />
              • <strong>Retenção de dados:</strong> Mantemos seus dados seguros por 120 dias após o vencimento<br />
              • <strong>LGPD:</strong> Totalmente compatível com a Lei Geral de Proteção de Dados
            </Typography>
          </Alert>
        </Box>
      </Paper>
    </Container>
  );
};

export default PlanosPage;
