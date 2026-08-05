import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Stack,
  Alert,
  CircularProgress,
  Card,
  CardContent,
} from '@mui/material';
import { EventAvailable, Chat, Payments } from '@mui/icons-material';
import { dashboardService, faturamentoService } from '../services/api';
import EmptyState from '../components/EmptyState';

const money = (v) =>
  v == null ? '—' : v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

function DailyBoardPage() {
  const [dados, setDados] = useState(null);
  const [fin, setFin] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    // eslint-disable-next-line react-hooks/exhaustive-deps
    Promise.all([
      dashboardService.pacientesDoDia(),
      faturamentoService.minhaSituacao().catch(() => null),
    ])
      .then(([d, f]) => {
        setDados(d);
        setFin(f);
      })
      .catch((e) => setError(e?.error || 'Erro ao carregar o dia'))
      .finally(() => setLoading(false));
  }, []);

  const dataFormatada = dados?.data
    ? new Date(dados.data + 'T12:00:00').toLocaleDateString('pt-BR', {
        weekday: 'long',
        day: '2-digit',
        month: 'long',
      })
    : '';

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        <EventAvailable sx={{ verticalAlign: 'middle', mr: 1 }} />
        Pacientes do dia
      </Typography>
      <Typography color="text.secondary" gutterBottom>
        {dataFormatada} · {dados?.total ?? 0} atendimento(s)
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      {loading && <CircularProgress />}

      {/* Resumo financeiro discreto */}
      {fin && (
        <Card sx={{ mb: 2, maxWidth: 560, bgcolor: 'background.paper' }}>
          <CardContent sx={{ py: 1.5 }}>
            <Stack direction="row" spacing={3} alignItems="center">
              <Typography variant="subtitle2" color="text.secondary" sx={{ minWidth: 130 }}>
                <Payments sx={{ verticalAlign: 'middle', mr: 0.5, fontSize: 18 }} />
                Seu financeiro
              </Typography>
              <Stack direction="row" spacing={3}>
                <Box>
                  <Typography variant="caption" color="text.secondary" display="block">
                    Lançado
                  </Typography>
                  <Typography fontWeight="bold">{money(fin.total_lancado)}</Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="success.main" display="block">
                    Recebido
                  </Typography>
                  <Typography fontWeight="bold">{money(fin.recebido)}</Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="warning.main" display="block">
                    Pendente
                  </Typography>
                  <Typography fontWeight="bold">{money(fin.pendente)}</Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="primary.main" display="block">
                    Seu repasse
                  </Typography>
                  <Typography fontWeight="bold">{money(fin.repasse_due)}</Typography>
                </Box>
              </Stack>
            </Stack>
          </CardContent>
        </Card>
      )}

      {!loading && !error && dados && dados.pacientes.length === 0 && (
        <EmptyState
          title="Nenhum atendimento hoje"
          description="Você não tem pacientes agendados para hoje."
        />
      )}

      {!loading && !error && dados && dados.pacientes.length > 0 && (
        <TableContainer component={Paper}>
          <Table size="medium">
            <TableHead>
              <TableRow>
                <TableCell>Hora</TableCell>
                <TableCell>Paciente</TableCell>
                <TableCell>Queixa principal</TableCell>
                <TableCell>Pré-consulta</TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {dados.pacientes.map((p) => (
                <TableRow key={p.consulta_id} hover>
                  <TableCell sx={{ fontWeight: 'bold' }}>{p.hora}</TableCell>
                  <TableCell>{p.paciente_nome}</TableCell>
                  <TableCell>
                    {p.pre_consulta?.feita ? (
                      <Stack direction="row" spacing={0.5} alignItems="center">
                        <Chat sx={{ fontSize: 16, color: 'text.secondary' }} />
                        <span>{p.pre_consulta.queixa_principal || '—'}</span>
                      </Stack>
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        sem pré-consulta
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    {p.pre_consulta?.feita ? (
                      <Chip
                        size="small"
                        color="success"
                        icon={<Chat sx={{ fontSize: 14 }} />}
                        label={p.pre_consulta.canal === 'telegram' ? 'Telegram ✓' : 'Web ✓'}
                      />
                    ) : (
                      <Chip size="small" variant="outlined" label="Pendente" />
                    )}
                  </TableCell>
                  <TableCell>
                    <Chip
                      size="small"
                      color={p.status === 'confirmada' ? 'primary' : 'default'}
                      label={p.status}
                    />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
}

export default DailyBoardPage;
