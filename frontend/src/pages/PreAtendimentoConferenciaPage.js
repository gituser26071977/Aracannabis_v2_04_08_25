import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Button,
  Chip,
  Stack,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  Tab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  TextField,
  Divider,
} from '@mui/material';
import { CheckCircle, Cancel, Payments, Preview, Refresh } from '@mui/icons-material';
import { preAtendimentoService } from '../services/api';

const STATUS_LABELS = {
  pendente_pagamento: { label: 'Pendente pagamento', color: 'warning' },
  liberado: { label: 'Liberado', color: 'success' },
  rejeitado: { label: 'Rejeitado', color: 'error' },
};

const PreAtendimentoConferenciaPage = () => {
  const [tab, setTab] = useState(0);
  const [itens, setItens] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [detail, setDetail] = useState(null);
  const [rejectDialog, setRejectDialog] = useState(null);
  const [motivo, setMotivo] = useState('');
  const [liberando, setLiberando] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const status = tab === 0 ? 'pendente_pagamento' : tab === 1 ? 'liberado' : 'rejeitado';
      const data = await preAtendimentoService.listarPendentes({ status, todos: 1 });
      setItens(data.pre_atendimentos || []);
    } catch (e) {
      setError(e?.error || 'Erro ao carregar pré-atendimentos');
    } finally {
      setLoading(false);
    }
  }, [tab]);

  useEffect(() => {
    load();
  }, [load]);

  const conferirLiberar = async (item, dispensar = false) => {
    setLiberando(true);
    setError('');
    try {
      const r = await preAtendimentoService.conferir(item.id, {
        acao: 'liberar',
        pagamento_confirmado: !dispensar,
        dispensar_pagamento: dispensar,
      });
      if (r.resultado?.erro) {
        setError(r.resultado.erro);
      } else {
        setDetail(null);
        load();
      }
    } catch (e) {
      setError(e?.error || 'Erro ao liberar');
    } finally {
      setLiberando(false);
    }
  };

  const rejeitar = async () => {
    if (!rejectDialog) return;
    setLiberando(true);
    setError('');
    try {
      await preAtendimentoService.conferir(rejectDialog.id, {
        acao: 'rejeitar',
        motivo: motivo,
      });
      setRejectDialog(null);
      setMotivo('');
      load();
    } catch (e) {
      setError(e?.error || 'Erro ao rejeitar');
    } finally {
      setLiberando(false);
    }
  };

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        🧾 Pré-atendimentos
      </Typography>
      <Typography color="text.secondary" gutterBottom>
        Confira os pré-atendimentos recebidos, confirme o pagamento e libere o paciente.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label="Pendentes de pagamento" />
        <Tab label="Liberados" />
        <Tab label="Rejeitados" />
      </Tabs>

      <Box sx={{ mb: 2 }}>
        <Button variant="outlined" startIcon={<Refresh />} onClick={load} disabled={loading}>
          Atualizar
        </Button>
      </Box>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 5 }}>
          <CircularProgress />
        </Box>
      ) : itens.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography color="text.secondary">Nenhum pré-atendimento nesta lista.</Typography>
        </Paper>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Nome</TableCell>
                <TableCell>Telefone</TableCell>
                <TableCell>Queixa</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Pagamento</TableCell>
                <TableCell align="right">Ações</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {itens.map((item) => {
                const dados = item.dados_solicitacao || {};
                const st = STATUS_LABELS[item.status] || { label: item.status, color: 'default' };
                return (
                  <TableRow key={item.id}>
                    <TableCell>{dados.nome || '—'}</TableCell>
                    <TableCell>{dados.telefone || '—'}</TableCell>
                    <TableCell>{item.queixa_principal || '—'}</TableCell>
                    <TableCell>
                      <Chip size="small" label={st.label} color={st.color} />
                    </TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        label={item.status_pagamento === 'pago' ? 'Pago' : item.status_pagamento}
                        color={item.status_pagamento === 'pago' ? 'success' : 'default'}
                      />
                    </TableCell>
                    <TableCell align="right">
                      <Stack direction="row" spacing={1} justifyContent="flex-end">
                        <Button
                          size="small"
                          startIcon={<Preview />}
                          onClick={() => setDetail(item)}
                        >
                          Ver
                        </Button>
                        {item.status === 'pendente_pagamento' && (
                          <>
                            <Button
                              size="small"
                              variant="contained"
                              color="primary"
                              startIcon={<Payments />}
                              onClick={() => conferirLiberar(item)}
                              disabled={liberando}
                            >
                              Pagamento recebido
                            </Button>
                            <Button
                              size="small"
                              color="error"
                              startIcon={<Cancel />}
                              onClick={() => setRejectDialog(item)}
                            >
                              Rejeitar
                            </Button>
                          </>
                        )}
                      </Stack>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Dialog de detalhe */}
      <Dialog open={Boolean(detail)} onClose={() => setDetail(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Detalhes do pré-atendimento</DialogTitle>
        <DialogContent dividers>
          {detail && (
            <Box>
              <Grid container spacing={1}>
                {Object.entries(detail.dados_solicitacao || {}).map(([k, v]) => {
                  if (k === 'slug' || k === 'profissional_id') return null;
                  if (!v) return null;
                  return (
                    <Grid item xs={12} key={k}>
                      <Typography variant="caption" color="text.secondary">
                        {k.replace(/_/g, ' ')}
                      </Typography>
                      <Typography variant="body2">{String(v)}</Typography>
                      <Divider sx={{ my: 0.5 }} />
                    </Grid>
                  );
                })}
                {detail.rejeitado_motivo && (
                  <Grid item xs={12}>
                    <Typography variant="caption" color="error">
                      Motivo da rejeição
                    </Typography>
                    <Typography variant="body2">{detail.rejeitado_motivo}</Typography>
                  </Grid>
                )}
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetail(null)} color="inherit">
            Fechar
          </Button>
          {detail?.status === 'pendente_pagamento' && (
            <>
              <Button
                color="success"
                startIcon={<CheckCircle />}
                onClick={() => {
                  const d = detail;
                  setDetail(null);
                  conferirLiberar(d, true);
                }}
                disabled={liberando}
              >
                Liberar sem pagamento (dispensar)
              </Button>
              <Button
                variant="contained"
                color="primary"
                startIcon={<Payments />}
                onClick={() => {
                  const d = detail;
                  setDetail(null);
                  conferirLiberar(d);
                }}
                disabled={liberando}
              >
                Confirmar pagamento e liberar
              </Button>
            </>
          )}
        </DialogActions>
      </Dialog>

      {/* Dialog de rejeição */}
      <Dialog
        open={Boolean(rejectDialog)}
        onClose={() => setRejectDialog(null)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Rejeitar pré-atendimento</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Informe o motivo da rejeição do pré-atendimento de{' '}
            <strong>{(rejectDialog?.dados_solicitacao || {}).nome || '—'}</strong>.
          </DialogContentText>
          <TextField
            label="Motivo"
            fullWidth
            multiline
            rows={3}
            value={motivo}
            onChange={(e) => setMotivo(e.target.value)}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRejectDialog(null)} color="inherit">
            Cancelar
          </Button>
          <Button color="error" variant="contained" onClick={rejeitar} disabled={liberando}>
            Rejeitar
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default PreAtendimentoConferenciaPage;
