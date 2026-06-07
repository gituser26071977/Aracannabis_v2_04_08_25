import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Button,
  Box,
  Grid,
  Card,
  CardContent,
  Divider,
  LinearProgress,
  Avatar,
  Chip,
  Alert
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  People as PeopleIcon,
  Event as EventIcon,
  SmartToy as SmartToyIcon,
  CheckCircle as CheckCircleIcon,
  Star as StarIcon,
  ArrowForward as ArrowForwardIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';

const DEPOIMENTOS = [
  {
    nome: "Dra. Ana Paula Silva",
    especialidade: "Neurologista",
    texto: "O Aracannabis transformou minha prática clínica. Consigo acompanhar meus pacientes de cannabis medicinal com precisão e segurança.",
    avatar: "AS"
  },
  {
    nome: "Dr. Ricardo Mendes",
    especialidade: "Psiquiatra",
    texto: "A IA assistente é um diferencial enorme. Me ajuda com dosagens e interações medicamentosas em tempo real.",
    avatar: "RM"
  },
  {
    nome: "Dra. Carla Fonseca",
    especialidade: "Medicina da Dor",
    texto: "Em 3 meses de uso, aumentei em 40% a eficiência no acompanhamento dos meus pacientes. Recomendo!",
    avatar: "CF"
  }
];

const TrialEndingPage = () => {
  const navigate = useNavigate();
  const { currentUser } = useAuth();
  const [stats, setStats] = useState({ pacientes: 0, consultas: 0, evolucoes: 0 });
  const [daysLeft, setDaysLeft] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [pacRes, consRes, evoRes] = await Promise.all([
          api.get('/pacientes/').catch(() => ({ data: [] })),
          api.get('/consultas/').catch(() => ({ data: [] })),
          api.get('/evolucoes/busca?termo=').catch(() => ({ data: [] }))
        ]);
        setStats({
          pacientes: Array.isArray(pacRes.data) ? pacRes.data.length : 0,
          consultas: Array.isArray(consRes.data) ? consRes.data.length : 0,
          evolucoes: Array.isArray(evoRes.data) ? evoRes.data.length : 0
        });
      } catch (err) {
        console.error('Erro ao buscar estatísticas:', err);
      } finally {
        setLoading(false);
      }
    };

    if (currentUser?.data_expiracao) {
      const exp = new Date(currentUser.data_expiracao);
      const now = new Date();
      const diffMs = exp - now;
      setDaysLeft(Math.ceil(diffMs / (1000 * 60 * 60 * 24)));
    }

    fetchStats();
  }, [currentUser]);

  const usageProgress = Math.min(100, ((stats.pacientes + stats.consultas + stats.evolucoes) / 30) * 100);

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: { xs: 3, sm: 5 }, borderRadius: 4, textAlign: 'center' }}>
        <Typography variant="h3" gutterBottom fontWeight={800}>
          ⏳ Seu Trial está chegando ao fim
        </Typography>
        <Typography variant="h6" color="text.secondary" gutterBottom>
          Não perca o acesso aos seus dados e às funcionalidades que você já começou a usar.
        </Typography>

        {daysLeft <= 0 && (
          <Alert severity="error" sx={{ mt: 3, textAlign: 'left' }}>
            <strong>Seu trial expirou.</strong> Seus dados estão seguros por 30 dias. Renove agora para recuperar o acesso completo.
          </Alert>
        )}

        {/* Resumo de Uso */}
        <Box sx={{ mt: 5, mb: 4 }}>
          <Typography variant="h5" gutterBottom fontWeight={700}>
            📊 Seu Resumo de Uso
          </Typography>
          <Grid container spacing={3} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={4}>
              <Card variant="outlined" sx={{ borderRadius: 3, py: 2 }}>
                <CardContent>
                  <PeopleIcon color="primary" sx={{ fontSize: 40, mb: 1 }} />
                  <Typography variant="h3" fontWeight="bold">{stats.pacientes}</Typography>
                  <Typography variant="body2" color="text.secondary">Pacientes cadastrados</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Card variant="outlined" sx={{ borderRadius: 3, py: 2 }}>
                <CardContent>
                  <EventIcon color="secondary" sx={{ fontSize: 40, mb: 1 }} />
                  <Typography variant="h3" fontWeight="bold">{stats.consultas}</Typography>
                  <Typography variant="body2" color="text.secondary">Consultas registradas</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Card variant="outlined" sx={{ borderRadius: 3, py: 2 }}>
                <CardContent>
                  <SmartToyIcon color="success" sx={{ fontSize: 40, mb: 1 }} />
                  <Typography variant="h3" fontWeight="bold">{stats.evolucoes}</Typography>
                  <Typography variant="body2" color="text.secondary">Evoluções / IA usos</Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
          <Box sx={{ mt: 3, px: { sm: 4 } }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Índice de engajamento
            </Typography>
            <LinearProgress
              variant="determinate"
              value={usageProgress}
              sx={{ height: 10, borderRadius: 5 }}
            />
            <Typography variant="caption" color="text.secondary">
              {Math.round(usageProgress)}% de adesão à plataforma
            </Typography>
          </Box>
        </Box>

        <Divider sx={{ my: 4 }} />

        {/* CTA Principal */}
        <Box sx={{ mb: 5 }}>
          <Typography variant="h4" gutterBottom fontWeight={700}>
            🚀 Escolha seu Plano Agora
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            Continue aproveitando todas as funcionalidades sem interrupções.
          </Typography>
          <Button
            variant="contained"
            size="large"
            color="primary"
            onClick={() => navigate('/planos')}
            endIcon={<ArrowForwardIcon />}
            sx={{
              py: 1.5,
              px: 5,
              fontSize: '1.1rem',
              fontWeight: 700,
              borderRadius: 3,
              background: 'linear-gradient(135deg, #0d7377 0%, #14a085 100%)',
              boxShadow: '0 8px 25px rgba(13,115,119,0.35)',
              '&:hover': {
                transform: 'translateY(-2px)',
                boxShadow: '0 12px 35px rgba(13,115,119,0.45)',
              }
            }}
          >
            Ver Planos e Preços
          </Button>
        </Box>

        <Divider sx={{ my: 4 }} />

        {/* Social Proof */}
        <Box>
          <Typography variant="h5" gutterBottom fontWeight={700}>
            💬 O que dizem os colegas
          </Typography>
          <Grid container spacing={3} sx={{ mt: 1, textAlign: 'left' }}>
            {DEPOIMENTOS.map((dep, idx) => (
              <Grid item xs={12} md={4} key={idx}>
                <Card variant="outlined" sx={{ borderRadius: 3, height: '100%' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                      <Avatar sx={{ bgcolor: 'primary.main' }}>{dep.avatar}</Avatar>
                      <Box>
                        <Typography variant="subtitle2" fontWeight={700}>{dep.nome}</Typography>
                        <Typography variant="caption" color="text.secondary">{dep.especialidade}</Typography>
                      </Box>
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                      "{dep.texto}"
                    </Typography>
                    <Box sx={{ mt: 2, display: 'flex', gap: 0.5 }}>
                      {[1,2,3,4,5].map(s => (
                        <StarIcon key={s} sx={{ fontSize: 16, color: '#ffc107' }} />
                      ))}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>

        <Box sx={{ mt: 4 }}>
          <Typography variant="body2" color="text.secondary">
            Dúvidas? Fale com nosso suporte:{' '}
            <strong>suporte@aracannabis.com.br</strong>
          </Typography>
        </Box>
      </Paper>
    </Container>
  );
};

export default TrialEndingPage;
