import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Paper,
  Card,
  CardContent,
  TextField,
  Button,
  Stack,
  Alert,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Divider,
  Tabs,
  Tab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import { AutoAwesome, PersonAdd, PendingActions, Check, Delete, Merge } from '@mui/icons-material';
import { onboardingService } from '../services/api';
import EmptyState from '../components/EmptyState';

function OnboardingPacientesPage() {
  const [tab, setTab] = useState(0);
  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        🧩 Cadastro de pacientes
      </Typography>
      <Typography color="text.secondary" gutterBottom>
        Cadastro rápido com assistência de IA e fila de pendências/duplicados.
      </Typography>
      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab icon={<PersonAdd />} iconPosition="start" label="Cadastrar" />
        <Tab icon={<PendingActions />} iconPosition="start" label="Pendências" />
      </Tabs>
      {tab === 0 && <CadastroTab />}
      {tab === 1 && <PendenciasTab />}
    </Box>
  );
}

function CadastroTab() {
  const [form, setForm] = useState({
    nome: '',
    telefone: '',
    cpf: '',
    email: '',
    data_nascimento: '',
    genero: '',
    queixa: '',
  });
  const [textoIA, setTextoIA] = useState('');
  const [sugerindo, setSugerindo] = useState(false);
  const [salvando, setSalvando] = useState(false);
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState('');

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const sugerir = async () => {
    setSugerindo(true);
    setError('');
    try {
      const s = await onboardingService.sugerir(textoIA);
      setForm((f) => ({ ...f, ...s, nome: s.nome || f.nome }));
    } catch (e) {
      setError(e?.error || 'Erro ao sugerir');
    } finally {
      setSugerindo(false);
    }
  };

  const salvar = async () => {
    setSalvando(true);
    setError('');
    setResultado(null);
    try {
      const r = await onboardingService.cadastrar(form);
      setResultado(r);
    } catch (e) {
      setError(e?.error || 'Erro ao cadastrar');
    } finally {
      setSalvando(false);
    }
  };

  return (
    <Grid container spacing={2}>
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Stack direction="row" spacing={1} alignItems="center" mb={1}>
              <AutoAwesome color="primary" />
              <Typography variant="h6">Cadastro rápido</Typography>
            </Stack>
            <TextField
              size="small"
              fullWidth
              label="Cole o texto do paciente (IA preenche)"
              multiline
              rows={2}
              value={textoIA}
              onChange={(e) => setTextoIA(e.target.value)}
              sx={{ mb: 1 }}
            />
            <Button
              startIcon={<AutoAwesome />}
              onClick={sugerir}
              disabled={sugerindo || !textoIA.trim()}
              sx={{ mb: 2 }}
            >
              {sugerindo ? 'Sugerindo…' : 'Sugerir com IA'}
            </Button>
            <Divider sx={{ mb: 2 }} />
            <Stack spacing={1.5}>
              <TextField
                size="small"
                label="Nome completo *"
                value={form.nome}
                onChange={set('nome')}
              />
              <Stack direction="row" spacing={1}>
                <TextField
                  size="small"
                  label="Telefone"
                  value={form.telefone}
                  onChange={set('telefone')}
                  sx={{ flex: 1 }}
                />
                <TextField
                  size="small"
                  label="CPF"
                  value={form.cpf}
                  onChange={set('cpf')}
                  sx={{ flex: 1 }}
                />
              </Stack>
              <Stack direction="row" spacing={1}>
                <TextField
                  size="small"
                  label="E-mail"
                  value={form.email}
                  onChange={set('email')}
                  sx={{ flex: 1 }}
                />
                <TextField
                  size="small"
                  label="Nascimento"
                  type="date"
                  value={form.data_nascimento}
                  onChange={set('data_nascimento')}
                  sx={{ flex: 1 }}
                  InputLabelProps={{ shrink: true }}
                />
              </Stack>
              <TextField
                size="small"
                label="Queixa principal"
                multiline
                rows={2}
                value={form.queixa}
                onChange={set('queixa')}
              />
              {error && <Alert severity="error">{error}</Alert>}
              {resultado && resultado.status === 'criado' && (
                <Alert severity="success">Paciente cadastrado (id {resultado.paciente_id}).</Alert>
              )}
              {resultado && resultado.status === 'pendente' && (
                <Alert severity="warning">
                  {resultado.motivo === 'duplicado'
                    ? `Possível duplicado: ${(resultado.duplicados || []).map((d) => d.nome).join(', ')}. Foi enviado para pendências.`
                    : 'Dados incompletos — enviado para pendências.'}
                </Alert>
              )}
              <Button
                variant="contained"
                startIcon={<PersonAdd />}
                onClick={salvar}
                disabled={salvando || !form.nome}
              >
                {salvando ? 'Salvando…' : 'Cadastrar paciente'}
              </Button>
            </Stack>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Como funciona
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Cole uma mensagem do paciente (ex.: "Maria, 11 99999-0000, dor nas costas") e clique
              em
              <b> Sugerir com IA</b>. Os campos são preenchidos automaticamente.
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Ao salvar, o sistema verifica <b>duplicados</b> (CPF/telefone/nome). Se encontrar ou
              faltar dados, o item vai para a aba <b>Pendências</b> — o administrativo confirma ou
              descarta.
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Pacientes que fazem a pré-consulta pelo Ara Intake são cadastrados automaticamente.
            </Typography>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
}

function PendenciasTab() {
  const [pendentes, setPendentes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [dialog, setDialog] = useState(null);

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      setPendentes(await onboardingService.listarPendentes());
    } catch (e) {
      setError(e?.error || 'Erro ao carregar pendências');
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    load();
  }, []);

  const confirmar = async (acao) => {
    try {
      await onboardingService.confirmar(dialog.id, acao);
      setDialog(null);
      load();
    } catch (e) {
      setError(e?.error || 'Erro ao confirmar');
    }
  };

  const descartar = async (item) => {
    if (!window.confirm('Descartar este item?')) return;
    try {
      await onboardingService.descartar(item.id);
      load();
    } catch (e) {
      setError(e?.error || 'Erro ao descartar');
    }
  };

  return (
    <Box>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      {loading && <CircularProgress />}
      {!loading && pendentes.length === 0 && !error && (
        <EmptyState
          title="Nenhuma pendência"
          description="Cadastros com duplicado ou dados incompletos aparecem aqui."
        />
      )}
      {!loading && pendentes.length > 0 && (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Paciente</TableCell>
                <TableCell>Contato</TableCell>
                <TableCell>Queixa</TableCell>
                <TableCell>Motivo</TableCell>
                <TableCell>Ações</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {pendentes.map((p) => (
                <TableRow key={p.id}>
                  <TableCell>
                    <b>{p.nome || '—'}</b>
                  </TableCell>
                  <TableCell>
                    {p.telefone || '—'} {p.cpf ? `· ${p.cpf}` : ''}
                  </TableCell>
                  <TableCell>{p.queixa || '—'}</TableCell>
                  <TableCell>
                    <Chip
                      size="small"
                      color={p.motivo === 'duplicado' ? 'warning' : 'info'}
                      label={
                        p.motivo === 'duplicado'
                          ? `Duplicado${p.duplicado_nome ? `: ${p.duplicado_nome}` : ''}`
                          : 'Incompleto'
                      }
                    />
                  </TableCell>
                  <TableCell>
                    <Stack direction="row" spacing={0.5}>
                      <Button
                        size="small"
                        variant="contained"
                        startIcon={<Check />}
                        onClick={() => setDialog(p)}
                      >
                        Resolver
                      </Button>
                      <Button
                        size="small"
                        color="error"
                        startIcon={<Delete />}
                        onClick={() => descartar(p)}
                      >
                        Descartar
                      </Button>
                    </Stack>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog open={!!dialog} onClose={() => setDialog(null)}>
        <DialogTitle>Resolver pendência</DialogTitle>
        <DialogContent>
          {dialog && (
            <Stack spacing={2} sx={{ mt: 1, minWidth: 360 }}>
              <Typography variant="body2" color="text.secondary">
                {dialog.nome || 'Paciente sem nome'} · {dialog.telefone || 'sem telefone'}{' '}
                {dialog.cpf ? `· ${dialog.cpf}` : ''}
              </Typography>
              {dialog.motivo === 'duplicado' && dialog.duplicado_nome && (
                <Alert severity="info">
                  Já existe paciente: <b>{dialog.duplicado_nome}</b>
                </Alert>
              )}
              <Button
                variant="contained"
                startIcon={<Merge />}
                onClick={() => confirmar('usar_existente')}
              >
                Usar paciente existente
              </Button>
              <Button
                variant="outlined"
                startIcon={<PersonAdd />}
                onClick={() => confirmar('criar')}
              >
                Cadastrar mesmo assim
              </Button>
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialog(null)}>Cancelar</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default OnboardingPacientesPage;
