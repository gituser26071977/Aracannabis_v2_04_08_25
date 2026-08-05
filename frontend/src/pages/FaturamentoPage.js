import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Button,
  Chip,
  Stack,
  Alert,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  CircularProgress,
  Tooltip,
} from '@mui/material';
import {
  Add,
  Refresh,
  Edit,
  Delete,
  Payments,
  Cancel,
  LocalHospital,
  Percent,
  ReceiptLong,
  AttachMoney,
  SmartToy,
  Send,
} from '@mui/icons-material';
import { faturamentoService, pacientesService } from '../services/api';
import EmptyState from '../components/EmptyState';

const money = (v) =>
  v == null ? '—' : v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

const STATUS_LABEL = {
  pendente: 'Pendente',
  parcial: 'Parcial',
  pago: 'Pago',
  cancelado: 'Cancelado',
};

function FaturamentoPage() {
  const [tab, setTab] = useState(0);
  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        💳 Faturamento
      </Typography>
      <Typography color="text.secondary" gutterBottom>
        Convênios, tabela de preços, repasse dos profissionais e contas a receber.
      </Typography>
      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mt: 1, mb: 2 }}>
        <Tab icon={<LocalHospital />} iconPosition="start" label="Convênios" />
        <Tab icon={<AttachMoney />} iconPosition="start" label="Serviços & Tabela" />
        <Tab icon={<Percent />} iconPosition="start" label="Repasse" />
        <Tab icon={<ReceiptLong />} iconPosition="start" label="Contas a receber" />
        <Tab icon={<SmartToy />} iconPosition="start" label="Agente" />
      </Tabs>
      {tab === 0 && <ConveniosTab />}
      {tab === 1 && <ServicosTab />}
      {tab === 2 && <PercentuaisTab />}
      {tab === 3 && <LancamentosTab />}
      {tab === 4 && <AgenteTab />}
    </Box>
  );
}

// ===========================================================================
// CONVÊNIOS
// ===========================================================================
function ConveniosTab() {
  const [convenios, setConvenios] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [dialog, setDialog] = useState(false);
  const [edit, setEdit] = useState(null);
  const [form, setForm] = useState({ nome: '', registro_ans: '', tipo: 'operadora' });

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      setConvenios(await faturamentoService.listarConvenios());
    } catch (e) {
      setError(e?.error || 'Erro ao carregar convênios');
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    // eslint-disable-next-line react-hooks/exhaustive-deps
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const openNew = () => {
    setEdit(null);
    setForm({ nome: '', registro_ans: '', tipo: 'operadora' });
    setDialog(true);
  };
  const openEdit = (c) => {
    setEdit(c);
    setForm({ nome: c.nome, registro_ans: c.registro_ans || '', tipo: c.tipo });
    setDialog(true);
  };

  const save = async () => {
    setError('');
    try {
      if (edit) await faturamentoService.atualizarConvenio(edit.id, form);
      else await faturamentoService.criarConvenio(form);
      setDialog(false);
      load();
    } catch (e) {
      setError(e?.error || 'Erro ao salvar');
    }
  };

  const remove = async (c) => {
    if (!window.confirm(`Desativar convênio "${c.nome}"?`)) return;
    try {
      await faturamentoService.deletarConvenio(c.id);
      load();
    } catch (e) {
      setError(e?.error || 'Erro ao desativar');
    }
  };

  return (
    <Grid container spacing={2}>
      <Grid item xs={12}>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">{convenios.length} convênio(s)</Typography>
          <Stack direction="row" spacing={1}>
            <Button startIcon={<Refresh />} onClick={load}>
              Atualizar
            </Button>
            <Button variant="contained" startIcon={<Add />} onClick={openNew}>
              Novo convênio
            </Button>
          </Stack>
        </Stack>
      </Grid>
      {error && (
        <Grid item xs={12}>
          <Alert severity="error">{error}</Alert>
        </Grid>
      )}
      {loading && (
        <Grid item xs={12}>
          <CircularProgress />
        </Grid>
      )}
      {!loading && convenios.length === 0 && !error && (
        <Grid item xs={12}>
          <EmptyState
            title="Nenhum convênio"
            description="Cadastre convênios para cobrar valor fixo por serviço."
          />
        </Grid>
      )}
      {!loading && convenios.length > 0 && (
        <Grid item xs={12}>
          <TableContainer component={Paper}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Nome</TableCell>
                  <TableCell>Registro ANS</TableCell>
                  <TableCell>Tipo</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Ações</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {convenios.map((c) => (
                  <TableRow key={c.id} sx={{ opacity: c.ativo ? 1 : 0.5 }}>
                    <TableCell>
                      <b>{c.nome}</b>
                    </TableCell>
                    <TableCell>{c.registro_ans || '—'}</TableCell>
                    <TableCell>{c.tipo}</TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        color={c.ativo ? 'success' : 'default'}
                        label={c.ativo ? 'Ativo' : 'Inativo'}
                      />
                    </TableCell>
                    <TableCell>
                      <Tooltip title="Editar">
                        <IconButton onClick={() => openEdit(c)}>
                          <Edit />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Desativar">
                        <IconButton onClick={() => remove(c)}>
                          <Delete />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Grid>
      )}
      <Dialog open={dialog} onClose={() => setDialog(false)}>
        <DialogTitle>{edit ? 'Editar convênio' : 'Novo convênio'}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1, minWidth: 360 }}>
            <TextField
              label="Nome"
              value={form.nome}
              onChange={(e) => setForm({ ...form, nome: e.target.value })}
              required
            />
            <TextField
              label="Registro ANS"
              value={form.registro_ans}
              onChange={(e) => setForm({ ...form, registro_ans: e.target.value })}
            />
            <FormControl fullWidth>
              <InputLabel>Tipo</InputLabel>
              <Select
                value={form.tipo}
                label="Tipo"
                onChange={(e) => setForm({ ...form, tipo: e.target.value })}
              >
                <MenuItem value="operadora">Operadora</MenuItem>
                <MenuItem value="consultorio">Consultório</MenuItem>
                <MenuItem value="outro">Outro</MenuItem>
              </Select>
            </FormControl>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialog(false)}>Cancelar</Button>
          <Button variant="contained" onClick={save} disabled={!form.nome}>
            Salvar
          </Button>
        </DialogActions>
      </Dialog>
    </Grid>
  );
}

// ===========================================================================
// SERVIÇOS & TABELA DE PREÇOS
// ===========================================================================
function ServicosTab() {
  const [servicos, setServicos] = useState([]);
  const [convenios, setConvenios] = useState([]);
  const [tabela, setTabela] = useState([]);
  const [convenioSel, setConvenioSel] = useState('');
  const [error, setError] = useState('');
  const [dialog, setDialog] = useState(false);
  const [edit, setEdit] = useState(null);
  const [form, setForm] = useState({
    nome: '',
    tipo: 'consulta',
    valor_particular: '',
    codigo: '',
  });
  const [tabelaForm, setTabelaForm] = useState({ servico_id: '', valor: '' });

  const load = async () => {
    setError('');
    try {
      const [sv, cv] = await Promise.all([
        faturamentoService.listarServicos(),
        faturamentoService.listarConvenios(true),
      ]);
      setServicos(sv);
      setConvenios(cv);
      if (cv.length) {
        setConvenioSel(String(cv[0].id));
        await loadTabela(cv[0].id);
      }
    } catch (e) {
      setError(e?.error || 'Erro ao carregar');
    }
  };
  useEffect(() => {
    // eslint-disable-next-line react-hooks/exhaustive-deps
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadTabela = async (id) => {
    try {
      setTabela(await faturamentoService.listarTabela(id));
    } catch (e) {
      setError(e?.error || 'Erro ao carregar tabela');
    }
  };

  const onConvenioChange = async (id) => {
    setConvenioSel(id);
    await loadTabela(id);
  };

  const openNew = () => {
    setEdit(null);
    setForm({ nome: '', tipo: 'consulta', valor_particular: '', codigo: '' });
    setDialog(true);
  };
  const openEdit = (s) => {
    setEdit(s);
    setForm({
      nome: s.nome,
      tipo: s.tipo,
      valor_particular: s.valor_particular,
      codigo: s.codigo || '',
    });
    setDialog(true);
  };

  const save = async () => {
    setError('');
    try {
      if (edit) await faturamentoService.atualizarServico(edit.id, form);
      else await faturamentoService.criarServico(form);
      setDialog(false);
      load();
    } catch (e) {
      setError(e?.error || 'Erro ao salvar');
    }
  };

  const remove = async (s) => {
    if (!window.confirm(`Desativar serviço "${s.nome}"?`)) return;
    try {
      await faturamentoService.deletarServico(s.id);
      load();
    } catch (e) {
      setError(e?.error || 'Erro ao desativar');
    }
  };

  const saveTabela = async () => {
    setError('');
    try {
      await faturamentoService.upsertTabela(convenioSel, tabelaForm);
      setTabelaForm({ servico_id: '', valor: '' });
      await loadTabela(convenioSel);
    } catch (e) {
      setError(e?.error || 'Erro ao salvar tabela');
    }
  };

  const removeTabela = async (servicoId) => {
    try {
      await faturamentoService.removerTabela(convenioSel, servicoId);
      await loadTabela(convenioSel);
    } catch (e) {
      setError(e?.error || 'Erro ao remover');
    }
  };

  return (
    <Grid container spacing={2}>
      <Grid item xs={12} md={5}>
        <Stack direction="row" justifyContent="space-between" alignItems="center" mb={1}>
          <Typography variant="h6">Serviços (tabela particular)</Typography>
          <Stack direction="row" spacing={1}>
            <Button startIcon={<Refresh />} onClick={load}>
              Atualizar
            </Button>
            <Button variant="contained" startIcon={<Add />} onClick={openNew}>
              Novo serviço
            </Button>
          </Stack>
        </Stack>
        {error && (
          <Alert severity="error" sx={{ mb: 1 }}>
            {error}
          </Alert>
        )}
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Serviço</TableCell>
                <TableCell>Tipo</TableCell>
                <TableCell align="right">Particular</TableCell>
                <TableCell>Ações</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {servicos.map((s) => (
                <TableRow key={s.id} sx={{ opacity: s.ativo ? 1 : 0.5 }}>
                  <TableCell>
                    <b>{s.nome}</b>
                    {s.codigo ? ` (${s.codigo})` : ''}
                  </TableCell>
                  <TableCell>{s.tipo}</TableCell>
                  <TableCell align="right">{money(s.valor_particular)}</TableCell>
                  <TableCell>
                    <Tooltip title="Editar">
                      <IconButton onClick={() => openEdit(s)}>
                        <Edit />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Desativar">
                      <IconButton onClick={() => remove(s)}>
                        <Delete />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Grid>

      <Grid item xs={12} md={7}>
        <Typography variant="h6" mb={1}>
          Tabela do convênio (valor fixo por serviço)
        </Typography>
        {convenios.length === 0 ? (
          <Alert severity="info">Cadastre convênios para configurar valores fixos.</Alert>
        ) : (
          <>
            <FormControl fullWidth sx={{ mb: 1 }} size="small">
              <InputLabel>Convênio</InputLabel>
              <Select
                value={convenioSel}
                label="Convênio"
                onChange={(e) => onConvenioChange(e.target.value)}
              >
                {convenios.map((c) => (
                  <MenuItem key={c.id} value={String(c.id)}>
                    {c.nome}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Stack direction="row" spacing={1} mb={1}>
              <FormControl fullWidth size="small">
                <InputLabel>Serviço</InputLabel>
                <Select
                  value={tabelaForm.servico_id}
                  label="Serviço"
                  onChange={(e) => setTabelaForm({ ...tabelaForm, servico_id: e.target.value })}
                >
                  {servicos.map((s) => (
                    <MenuItem key={s.id} value={String(s.id)}>
                      {s.nome}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <TextField
                size="small"
                label="Valor fixo (R$)"
                type="number"
                value={tabelaForm.valor}
                onChange={(e) => setTabelaForm({ ...tabelaForm, valor: e.target.value })}
                sx={{ width: 150 }}
              />
              <Button
                variant="contained"
                onClick={saveTabela}
                disabled={!tabelaForm.servico_id || tabelaForm.valor === ''}
              >
                Definir
              </Button>
            </Stack>
            <TableContainer component={Paper}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Serviço</TableCell>
                    <TableCell align="right">Valor</TableCell>
                    <TableCell />
                  </TableRow>
                </TableHead>
                <TableBody>
                  {tabela.map((t) => (
                    <TableRow key={t.id}>
                      <TableCell>{t.servico_nome}</TableCell>
                      <TableCell align="right">
                        <b>{money(t.valor)}</b>
                      </TableCell>
                      <TableCell align="right">
                        <Tooltip title="Remover">
                          <IconButton onClick={() => removeTabela(t.servico_id)}>
                            <Delete />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                  {tabela.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={3}>
                        <Typography variant="body2" color="text.secondary">
                          Sem valores fixos — usar valor particular.
                        </Typography>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </>
        )}
      </Grid>

      <Dialog open={dialog} onClose={() => setDialog(false)}>
        <DialogTitle>{edit ? 'Editar serviço' : 'Novo serviço'}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1, minWidth: 360 }}>
            <TextField
              label="Nome"
              value={form.nome}
              onChange={(e) => setForm({ ...form, nome: e.target.value })}
              required
            />
            <TextField
              label="Código (opcional)"
              value={form.codigo}
              onChange={(e) => setForm({ ...form, codigo: e.target.value })}
            />
            <FormControl fullWidth>
              <InputLabel>Tipo</InputLabel>
              <Select
                value={form.tipo}
                label="Tipo"
                onChange={(e) => setForm({ ...form, tipo: e.target.value })}
              >
                <MenuItem value="consulta">Consulta</MenuItem>
                <MenuItem value="retorno">Retorno</MenuItem>
                <MenuItem value="procedimento">Procedimento</MenuItem>
                <MenuItem value="outro">Outro</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Valor particular (R$)"
              type="number"
              value={form.valor_particular}
              onChange={(e) => setForm({ ...form, valor_particular: e.target.value })}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialog(false)}>Cancelar</Button>
          <Button variant="contained" onClick={save} disabled={!form.nome}>
            Salvar
          </Button>
        </DialogActions>
      </Dialog>
    </Grid>
  );
}

// ===========================================================================
// REPASSE (percentual por profissional / por serviço)
// ===========================================================================
function PercentuaisTab() {
  const [profissionais, setProfissionais] = useState([]);
  const [servicos, setServicos] = useState([]);
  const [profSel, setProfSel] = useState('');
  const [itens, setItens] = useState([]);
  const [error, setError] = useState('');
  const [form, setForm] = useState({ servico_id: '', percentual: '' });

  const load = async () => {
    setError('');
    try {
      const [profs, servs] = await Promise.all([
        pacientesService.listarProfissionais(),
        faturamentoService.listarServicos(true),
      ]);
      const lista = Array.isArray(profs) ? profs : profs.profissionais || profs.professionals || [];
      setProfissionais(lista);
      setServicos(servs);
      if (lista.length) {
        setProfSel(String(lista[0].id));
        await loadItens(lista[0].id);
      }
    } catch (e) {
      setError(e?.error || 'Erro ao carregar');
    }
  };
  useEffect(() => {
    // eslint-disable-next-line react-hooks/exhaustive-deps
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadItens = async (id) => {
    try {
      setItens(await faturamentoService.listarPercentuais(id));
    } catch (e) {
      setError(e?.error || 'Erro ao carregar percentuais');
    }
  };

  const onProfChange = async (id) => {
    setProfSel(id);
    await loadItens(id);
  };

  const save = async () => {
    setError('');
    const payload = { percentual: parseFloat(form.percentual) };
    if (form.servico_id !== '') payload.servico_id = parseInt(form.servico_id, 10);
    try {
      await faturamentoService.upsertPercentual(profSel, payload);
      setForm({ servico_id: '', percentual: '' });
      await loadItens(profSel);
    } catch (e) {
      setError(e?.error || 'Erro ao salvar');
    }
  };

  const remove = async (item) => {
    if (!window.confirm('Remover percentual?')) return;
    try {
      await faturamentoService.removerPercentual(profSel, item.id);
      await loadItens(profSel);
    } catch (e) {
      setError(e?.error || 'Erro ao remover');
    }
  };

  const globalItem = itens.find((i) => i.servico_id === null);
  const porServico = itens.filter((i) => i.servico_id !== null);

  return (
    <Grid container spacing={2}>
      <Grid item xs={12} md={4}>
        <Typography variant="h6" mb={1}>
          Profissional
        </Typography>
        <FormControl fullWidth size="small">
          <InputLabel>Profissional</InputLabel>
          <Select
            value={profSel}
            label="Profissional"
            onChange={(e) => onProfChange(e.target.value)}
          >
            {profissionais.map((p) => (
              <MenuItem key={p.id} value={String(p.id)}>
                {p.nome}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <Card sx={{ mt: 2 }}>
          <CardContent>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              O percentual é o valor que <b>vai para o profissional</b>. O restante fica com a
              clínica.
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Sem configuração, o profissional fica com 100%.
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={8}>
        {error && (
          <Alert severity="error" sx={{ mb: 1 }}>
            {error}
          </Alert>
        )}
        <Stack direction="row" spacing={1} mb={1}>
          <FormControl fullWidth size="small">
            <InputLabel>Serviço</InputLabel>
            <Select
              value={form.servico_id}
              label="Serviço"
              onChange={(e) => setForm({ ...form, servico_id: e.target.value })}
            >
              <MenuItem value="">Todos (global)</MenuItem>
              {servicos.map((s) => (
                <MenuItem key={s.id} value={String(s.id)}>
                  {s.nome}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            size="small"
            label="Percentual (%)"
            type="number"
            value={form.percentual}
            onChange={(e) => setForm({ ...form, percentual: e.target.value })}
            sx={{ width: 160 }}
          />
          <Button variant="contained" onClick={save} disabled={form.percentual === '' || !profSel}>
            Definir
          </Button>
        </Stack>

        {globalItem && (
          <Card sx={{ mb: 1, bgcolor: 'action.hover' }}>
            <CardContent sx={{ py: 1 }}>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Typography variant="body1">
                  <b>Padrão (todos os serviços)</b>
                </Typography>
                <Stack direction="row" alignItems="center" spacing={1}>
                  <Chip color="primary" label={`${globalItem.percentual}% p/ profissional`} />
                  <IconButton onClick={() => remove(globalItem)}>
                    <Delete />
                  </IconButton>
                </Stack>
              </Stack>
            </CardContent>
          </Card>
        )}

        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Serviço</TableCell>
                <TableCell align="center">Repasse profissional</TableCell>
                <TableCell align="center">Clínica</TableCell>
                <TableCell />
              </TableRow>
            </TableHead>
            <TableBody>
              {porServico.map((i) => (
                <TableRow key={i.id}>
                  <TableCell>{i.servico_nome}</TableCell>
                  <TableCell align="center">
                    <b>{i.percentual}%</b>
                  </TableCell>
                  <TableCell align="center">{100 - i.percentual}%</TableCell>
                  <TableCell align="right">
                    <IconButton onClick={() => remove(i)}>
                      <Delete />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
              {porServico.length === 0 && (
                <TableRow>
                  <TableCell colSpan={4}>
                    <Typography variant="body2" color="text.secondary">
                      Nenhum percentual por serviço configurado.
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Grid>
    </Grid>
  );
}

// ===========================================================================
// CONTAS A RECEBER (lançamentos)
// ===========================================================================
function LancamentosTab() {
  const [lancamentos, setLancamentos] = useState([]);
  const [total, setTotal] = useState(0);
  const [privileged, setPrivileged] = useState(true);
  const [servicos, setServicos] = useState([]);
  const [convenios, setConvenios] = useState([]);
  const [filtros, setFiltros] = useState({ status: '', modalidade: '' });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [dialog, setDialog] = useState(false);
  const [form, setForm] = useState({
    servico_id: '',
    convenio_id: '',
    desconto: '',
    forma_pagamento: 'dinheiro',
    observacao: '',
  });
  const [receberDialog, setReceberDialog] = useState(null);
  const [receberForm, setReceberForm] = useState({ valor: '', forma_pagamento: 'dinheiro' });

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await faturamentoService.listarLancamentos(filtros);
      setLancamentos(res.lancamentos || []);
      setTotal(res.total || 0);
      setPrivileged(res.privileged !== false);
    } catch (e) {
      setError(e?.error || 'Erro ao carregar lançamentos');
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtros]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/exhaustive-deps
    Promise.all([faturamentoService.listarServicos(true), faturamentoService.listarConvenios(true)])
      .then(([sv, cv]) => {
        setServicos(sv);
        setConvenios(cv);
      })
      .catch(() => {});
  }, []);

  const openNew = () => {
    setForm({
      servico_id: '',
      convenio_id: '',
      desconto: '',
      forma_pagamento: 'dinheiro',
      observacao: '',
    });
    setDialog(true);
  };

  const lancar = async () => {
    setError('');
    const payload = {
      servico_id: parseInt(form.servico_id, 10),
      forma_pagamento: form.forma_pagamento,
      observacao: form.observacao || undefined,
    };
    if (form.convenio_id) payload.convenio_id = parseInt(form.convenio_id, 10);
    if (form.desconto !== '') payload.desconto = parseFloat(form.desconto);
    try {
      await faturamentoService.lancar(payload);
      setDialog(false);
      load();
    } catch (e) {
      setError(e?.error || 'Erro ao lançar');
    }
  };

  const openReceber = (l) => {
    setReceberDialog(l);
    setReceberForm({
      valor: l.valor_receber - (l.valor_recebido || 0),
      forma_pagamento: 'dinheiro',
    });
  };

  const receber = async () => {
    setError('');
    try {
      await faturamentoService.receber(receberDialog.id, receberForm);
      setReceberDialog(null);
      load();
    } catch (e) {
      setError(e?.error || 'Erro ao registrar recebimento');
    }
  };

  const estornar = async (l) => {
    if (!window.confirm('Estornar este lançamento? (fica cancelado no histórico)')) return;
    setError('');
    try {
      await faturamentoService.estornar(l.id);
      load();
    } catch (e) {
      setError(e?.error || 'Erro ao estornar');
    }
  };

  const recebidoTotal = lancamentos
    .filter((l) => l.status !== 'cancelado')
    .reduce((a, l) => a + (l.valor_receber - (l.valor_recebido || 0)), 0);

  return (
    <Grid container spacing={2}>
      <Grid item xs={12}>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Stack direction="row" spacing={1} alignItems="center">
            <FormControl size="small" sx={{ minWidth: 140 }}>
              <InputLabel>Status</InputLabel>
              <Select
                value={filtros.status}
                label="Status"
                onChange={(e) => setFiltros({ ...filtros, status: e.target.value })}
              >
                <MenuItem value="">Todos</MenuItem>
                <MenuItem value="pendente">Pendente</MenuItem>
                <MenuItem value="parcial">Parcial</MenuItem>
                <MenuItem value="pago">Pago</MenuItem>
                <MenuItem value="cancelado">Cancelado</MenuItem>
              </Select>
            </FormControl>
            <FormControl size="small" sx={{ minWidth: 140 }}>
              <InputLabel>Modalidade</InputLabel>
              <Select
                value={filtros.modalidade}
                label="Modalidade"
                onChange={(e) => setFiltros({ ...filtros, modalidade: e.target.value })}
              >
                <MenuItem value="">Todas</MenuItem>
                <MenuItem value="particular">Particular</MenuItem>
                <MenuItem value="convenio">Convênio</MenuItem>
              </Select>
            </FormControl>
            <Button startIcon={<Refresh />} onClick={load}>
              Atualizar
            </Button>
          </Stack>
          <Button variant="contained" startIcon={<Add />} onClick={openNew}>
            Lançar faturamento
          </Button>
        </Stack>
        <Typography variant="body2" color="text.secondary" mt={1}>
          {total} lançamento(s)
          {privileged ? ` · ${money(recebidoTotal)} a receber (não cancelados)` : ''}
        </Typography>
      </Grid>

      {error && (
        <Grid item xs={12}>
          <Alert severity="error">{error}</Alert>
        </Grid>
      )}
      {loading && (
        <Grid item xs={12}>
          <CircularProgress />
        </Grid>
      )}
      {!loading && lancamentos.length === 0 && !error && (
        <Grid item xs={12}>
          <EmptyState
            title="Nenhum lançamento"
            description="Lance o faturamento de uma consulta (particular ou convênio)."
          />
        </Grid>
      )}
      {!loading && lancamentos.length > 0 && (
        <Grid item xs={12}>
          <TableContainer component={Paper}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Data</TableCell>
                  <TableCell>Paciente</TableCell>
                  <TableCell>Serviço</TableCell>
                  <TableCell>Modalidade</TableCell>
                  <TableCell>Profissional</TableCell>
                  <TableCell align="right">Valor</TableCell>
                  <TableCell align="right">Repasse</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Ações</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {lancamentos.map((l) => (
                  <TableRow key={l.id} sx={{ opacity: l.status === 'cancelado' ? 0.5 : 1 }}>
                    <TableCell>
                      {l.data_lancamento
                        ? new Date(l.data_lancamento).toLocaleDateString('pt-BR')
                        : '—'}
                    </TableCell>
                    <TableCell>{l.paciente_nome || '—'}</TableCell>
                    <TableCell>{l.servico_nome}</TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        color={l.modalidade === 'particular' ? 'default' : 'info'}
                        label={l.modalidade}
                      />
                    </TableCell>
                    <TableCell>{l.profissional_nome}</TableCell>
                    <TableCell align="right">
                      <b>{money(l.valor_receber)}</b>
                    </TableCell>
                    <TableCell align="right">{money(l.valor_repasse)}</TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        color={
                          l.status === 'pago'
                            ? 'success'
                            : l.status === 'cancelado'
                              ? 'default'
                              : l.status === 'parcial'
                                ? 'warning'
                                : 'primary'
                        }
                        label={STATUS_LABEL[l.status] || l.status}
                      />
                    </TableCell>
                    <TableCell>
                      {(l.status === 'pendente' || l.status === 'parcial') && (
                        <Tooltip title="Receber">
                          <IconButton color="success" onClick={() => openReceber(l)}>
                            <Payments />
                          </IconButton>
                        </Tooltip>
                      )}
                      {l.status !== 'cancelado' && (
                        <Tooltip title="Estornar">
                          <IconButton onClick={() => estornar(l)}>
                            <Cancel />
                          </IconButton>
                        </Tooltip>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Grid>
      )}

      <Dialog open={dialog} onClose={() => setDialog(false)}>
        <DialogTitle>Lançar faturamento</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1, minWidth: 360 }}>
            <FormControl fullWidth>
              <InputLabel>Serviço</InputLabel>
              <Select
                value={form.servico_id}
                label="Serviço"
                onChange={(e) => setForm({ ...form, servico_id: e.target.value })}
              >
                {servicos.map((s) => (
                  <MenuItem key={s.id} value={String(s.id)}>
                    {s.nome} — {money(s.valor_particular)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl fullWidth>
              <InputLabel>Modalidade</InputLabel>
              <Select
                value={form.convenio_id}
                label="Modalidade"
                onChange={(e) => setForm({ ...form, convenio_id: e.target.value })}
              >
                <MenuItem value="">Particular</MenuItem>
                {convenios.map((c) => (
                  <MenuItem key={c.id} value={String(c.id)}>
                    {c.nome}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              label="Desconto (R$, opcional)"
              type="number"
              value={form.desconto}
              onChange={(e) => setForm({ ...form, desconto: e.target.value })}
            />
            <FormControl fullWidth>
              <InputLabel>Forma de pagamento</InputLabel>
              <Select
                value={form.forma_pagamento}
                label="Forma de pagamento"
                onChange={(e) => setForm({ ...form, forma_pagamento: e.target.value })}
              >
                <MenuItem value="dinheiro">Dinheiro</MenuItem>
                <MenuItem value="pix">PIX</MenuItem>
                <MenuItem value="cartao">Cartão</MenuItem>
                <MenuItem value="boleto">Boleto</MenuItem>
                <MenuItem value="outro">Outro</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Observação"
              value={form.observacao}
              onChange={(e) => setForm({ ...form, observacao: e.target.value })}
              multiline
              rows={2}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialog(false)}>Cancelar</Button>
          <Button variant="contained" onClick={lancar} disabled={!form.servico_id}>
            Lançar
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={!!receberDialog} onClose={() => setReceberDialog(null)}>
        <DialogTitle>Receber lançamento</DialogTitle>
        <DialogContent>
          {receberDialog && (
            <Stack spacing={2} sx={{ mt: 1, minWidth: 320 }}>
              <Typography variant="body2" color="text.secondary">
                {receberDialog.servico_nome} · {money(receberDialog.valor_receber)} · recebido{' '}
                {money(receberDialog.valor_recebido || 0)}
              </Typography>
              <TextField
                label="Valor a receber (R$)"
                type="number"
                value={receberForm.valor}
                onChange={(e) => setReceberForm({ ...receberForm, valor: e.target.value })}
              />
              <FormControl fullWidth>
                <InputLabel>Forma de pagamento</InputLabel>
                <Select
                  value={receberForm.forma_pagamento}
                  label="Forma de pagamento"
                  onChange={(e) =>
                    setReceberForm({ ...receberForm, forma_pagamento: e.target.value })
                  }
                >
                  <MenuItem value="dinheiro">Dinheiro</MenuItem>
                  <MenuItem value="pix">PIX</MenuItem>
                  <MenuItem value="cartao">Cartão</MenuItem>
                  <MenuItem value="boleto">Boleto</MenuItem>
                  <MenuItem value="outro">Outro</MenuItem>
                </Select>
              </FormControl>
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setReceberDialog(null)}>Cancelar</Button>
          <Button
            variant="contained"
            color="success"
            onClick={receber}
            disabled={!receberForm.valor}
          >
            Registrar
          </Button>
        </DialogActions>
      </Dialog>
    </Grid>
  );
}

export default FaturamentoPage;

// ===========================================================================
// AGENTE FINANCEIRO (linguagem natural — somente leitura)
// ===========================================================================
function AgenteTab() {
  const [mensagens, setMensagens] = useState([
    {
      role: 'agent',
      texto:
        'Olá! Sou o assistente financeiro. Pergunte, por exemplo: "quanto recebi neste mês?", "quem está inadimplente?" ou "qual o repasse do Dr. X?".',
    },
  ]);
  const [pergunta, setPergunta] = useState('');
  const [pensando, setPensando] = useState(false);
  const [error, setError] = useState('');

  const enviar = async () => {
    const texto = pergunta.trim();
    if (!texto || pensando) return;
    setMensagens((m) => [...m, { role: 'user', texto }]);
    setPergunta('');
    setPensando(true);
    setError('');
    try {
      const r = await faturamentoService.agente(texto);
      setMensagens((m) => [...m, { role: 'agent', texto: r.resposta }]);
    } catch (e) {
      setError(e?.error || 'Erro ao consultar o agente');
    } finally {
      setPensando(false);
    }
  };

  return (
    <Grid container spacing={2}>
      <Grid item xs={12}>
        {error && (
          <Alert severity="error" sx={{ mb: 1 }}>
            {error}
          </Alert>
        )}
        <Paper
          sx={{
            p: 2,
            minHeight: 320,
            maxHeight: 480,
            overflowY: 'auto',
            bgcolor: 'background.default',
          }}
        >
          <Stack spacing={1.5}>
            {mensagens.map((m, i) => (
              <Box
                key={i}
                sx={{
                  display: 'flex',
                  justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start',
                }}
              >
                <Paper
                  elevation={0}
                  sx={{
                    maxWidth: '78%',
                    p: 1.5,
                    borderRadius: 2,
                    bgcolor: m.role === 'user' ? 'primary.main' : 'background.paper',
                    color: m.role === 'user' ? 'primary.contrastText' : 'inherit',
                    border: m.role === 'agent' ? '1px solid' : 'none',
                    borderColor: 'divider',
                  }}
                >
                  <Typography variant="body2">{m.texto}</Typography>
                </Paper>
              </Box>
            ))}
            {pensando && (
              <Box sx={{ display: 'flex' }}>
                <Chip size="small" icon={<SmartToy />} label="Pensando…" variant="outlined" />
              </Box>
            )}
          </Stack>
        </Paper>
      </Grid>
      <Grid item xs={12}>
        <Stack direction="row" spacing={1}>
          <TextField
            size="small"
            fullWidth
            placeholder="Pergunte sobre seu financeiro…"
            value={pergunta}
            onChange={(e) => setPergunta(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') enviar();
            }}
          />
          <Button
            variant="contained"
            startIcon={<Send />}
            onClick={enviar}
            disabled={pensando || !pergunta.trim()}
          >
            Enviar
          </Button>
        </Stack>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
          O agente consulta os dados (somente leitura). Ações de faturamento continuam manuais pelo
          administrativo.
        </Typography>
      </Grid>
    </Grid>
  );
}
