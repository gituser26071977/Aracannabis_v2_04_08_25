import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  TextField,
  Button,
  Divider,
  Alert,
  CircularProgress,
  MenuItem,
  IconButton,
  Card,
  CardContent,
  Stack,
  Chip,
  Tabs,
  Tab,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Business as BusinessIcon,
  MeetingRoom as MeetingRoomIcon,
  Send as SendIcon,
  SmartToy,
} from '@mui/icons-material';
import api from '../services/api';

const TIPOS_UNIDADE = ['clinica', 'consultorio', 'hospital', 'home_care'];
const TIPOS_ANDAR = ['andar', 'ala', 'setor', 'uti', 'centro_cirurgico', 'recepcao', 'outro'];
const TIPOS_ESPACO = [
  'consultorio',
  'sala_espera',
  'infusao',
  'procedimento',
  'banheiro',
  'terapia',
  'pre_atendimento',
  'recepcao',
  'triagem',
  'outro',
];

const LABEL_TIPO = {
  clinica: 'Clínica',
  consultorio: 'Consultório',
  hospital: 'Hospital',
  home_care: 'Home Care',
  andar: 'Andar',
  ala: 'Ala',
  setor: 'Setor',
  uti: 'UTI',
  centro_cirurgico: 'Centro Cirúrgico',
  recepcao: 'Recepção',
  sala_espera: 'Sala de Espera',
  infusao: 'Sala de Infusão',
  procedimento: 'Procedimento/Exames',
  banheiro: 'Banheiro',
  terapia: 'Terapia',
  pre_atendimento: 'Pré-atendimento',
  triagem: 'Triagem',
  outro: 'Outro',
};

const ConfigurarUnidadePage = () => {
  const [abaAtiva, setAbaAtiva] = useState(0);

  return (
    <Box sx={{ p: 3, maxWidth: 1100, mx: 'auto' }}>
      <Typography variant="h5" gutterBottom sx={{ fontWeight: 600 }}>
        🏬 Configuração da Unidade
      </Typography>
      <Tabs
        value={abaAtiva}
        onChange={(_, v) => setAbaAtiva(v)}
        sx={{ mb: 3, borderBottom: 1, borderColor: 'divider' }}
      >
        <Tab label="🤖 Configurar com IA (recomendado)" icon={<SmartToy />} iconPosition="start" />
        <Tab label="⚙️ Configuração Manual" icon={<BusinessIcon />} iconPosition="start" />
      </Tabs>
      {abaAtiva === 0 && <UnidadeChat />}
      {abaAtiva === 1 && <UnidadeManual />}
    </Box>
  );
};

// ── Chat com IA ──────────────────────────────

const UnidadeChat = () => {
  const [sessionId, setSessionId] = useState(null);
  const [mensagens, setMensagens] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [concluido, setConcluido] = useState(false);
  const [msgErro, setMsgErro] = useState('');
  const chatRef = React.useRef(null);

  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [mensagens]);

  const iniciar = async () => {
    setLoading(true);
    setMensagens([{ role: 'bot', text: 'Olá! Vou ajudar você a configurar sua clínica. 🤖' }]);
    setSessionId(`unidade-${Date.now()}`);
    setConcluido(false);
    setMsgErro('');
    setLoading(false);
  };

  const enviar = async () => {
    const msg = input.trim();
    if (!msg || loading) return;
    setInput('');
    setMensagens((prev) => [...prev, { role: 'user', text: msg }]);
    setLoading(true);
    try {
      const resp = await api.post('/unidade/chat', {
        mensagem: msg,
        session_id: sessionId,
      });
      setSessionId(resp.data.session_id);
      setMensagens((prev) => [...prev, { role: 'bot', text: resp.data.resposta }]);
      if (resp.data.concluido) setConcluido(true);
      setMsgErro('');
    } catch (err) {
      setMsgErro(err.response?.data?.error || 'Erro ao comunicar com o agente.');
    } finally {
      setLoading(false);
    }
  };

  if (!sessionId) {
    return (
      <Paper sx={{ p: 6, textAlign: 'center' }}>
        <SmartToy sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
        <Typography variant="h6" gutterBottom>
          Configuração Inteligente
        </Typography>
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ mb: 3, maxWidth: 500, mx: 'auto' }}
        >
          Um agente de IA vai conversar com você para entender a estrutura da sua clínica. Basta
          responder às perguntas — nome, tipo, endereço, quantidade de andares e salas.
        </Typography>
        <Button variant="contained" size="large" onClick={iniciar} startIcon={<SmartToy />}>
          Iniciar Configuração
        </Button>
      </Paper>
    );
  }

  return (
    <Paper sx={{ display: 'flex', flexDirection: 'column', minHeight: 500 }}>
      <Box ref={chatRef} sx={{ flex: 1, overflowY: 'auto', p: 3 }}>
        {mensagens.map((m, i) => (
          <Box
            key={i}
            sx={{
              display: 'flex',
              justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start',
              mb: 2,
            }}
          >
            <Paper
              sx={{
                maxWidth: '75%',
                p: 2,
                bgcolor: m.role === 'user' ? 'primary.main' : 'grey.100',
                color: m.role === 'user' ? 'white' : 'text.primary',
                borderRadius: 2,
                whiteSpace: 'pre-line',
              }}
            >
              <Typography variant="body2">{m.text}</Typography>
            </Paper>
          </Box>
        ))}
        {loading && <CircularProgress size={20} sx={{ display: 'block', mx: 'auto' }} />}
      </Box>
      {msgErro && (
        <Alert severity="error" sx={{ mx: 2, mb: 1 }}>
          {msgErro}
        </Alert>
      )}
      {concluido && (
        <Alert severity="success" sx={{ mx: 2, mb: 1 }}>
          Configuração concluída! Você pode revisar na aba "Configuração Manual".
        </Alert>
      )}
      <Divider />
      <Box sx={{ p: 2, display: 'flex', gap: 1 }}>
        <TextField
          fullWidth
          size="small"
          placeholder={concluido ? 'Configuração finalizada' : 'Digite sua resposta...'}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && enviar()}
          disabled={loading || concluido}
        />
        <Button
          variant="contained"
          onClick={enviar}
          disabled={loading || concluido || !input.trim()}
        >
          <SendIcon />
        </Button>
      </Box>
    </Paper>
  );
};

// ── Configuração Manual (código original) ─────

const UnidadeManual = () => {
  const [unidades, setUnidades] = useState([]);
  const [unidadeSel, setUnidadeSel] = useState(null);
  const [arvore, setArvore] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');
  const [err, setErr] = useState('');
  const [novaUnidade, setNovaUnidade] = useState({ nome: '', tipo: 'clinica', possui_uti: false });
  const [novoAndar, setNovoAndar] = useState({ nome: '', tipo: 'andar', parent_id: '' });
  const [novoEspaco, setNovoEspaco] = useState({
    nome: '',
    tipo: 'consultorio',
    capacidade: 1,
    unidade_id: '',
    andar_setor_id: '',
    vsf_room_key: '',
  });

  const carregarUnidades = useCallback(async () => {
    try {
      const r = await api.get('/unidade');
      setUnidades(r.data.unidades || []);
      if (r.data.unidades?.length && !unidadeSel) setUnidadeSel(r.data.unidades[0]);
    } catch (e) {
      if (process.env.NODE_ENV !== 'production') console.error(e);
    } finally {
      setLoading(false);
    }
  }, [unidadeSel]);

  const carregarArvore = useCallback(async (id) => {
    try {
      const r = await api.get(`/unidade/${id}`);
      setArvore(r.data);
      setNovoEspaco((s) => ({ ...s, unidade_id: id }));
    } catch (e) {
      setErr('Não foi possível carregar a unidade.');
    }
  }, []);

  useEffect(() => {
    carregarUnidades();
  }, [carregarUnidades]);
  useEffect(() => {
    if (unidadeSel) carregarArvore(unidadeSel.id);
  }, [unidadeSel, carregarArvore]);

  const handleCriarUnidade = async () => {
    if (!novaUnidade.nome.trim()) {
      setErr('Nome é obrigatório');
      return;
    }
    setSaving(true);
    setErr('');
    setMsg('');
    try {
      const r = await api.post('/unidade', novaUnidade);
      setMsg('Unidade criada.');
      setUnidadeSel(r.data.unidade);
      setNovaUnidade({ nome: '', tipo: 'clinica', possui_uti: false });
      await carregarUnidades();
    } catch (e) {
      setErr(e.response?.data?.error || 'Erro ao criar unidade.');
    } finally {
      setSaving(false);
    }
  };

  const handleCriarAndar = async () => {
    if (!unidadeSel) {
      setErr('Selecione uma unidade');
      return;
    }
    if (!novoAndar.nome.trim()) {
      setErr('Nome do andar é obrigatório');
      return;
    }
    setSaving(true);
    setErr('');
    setMsg('');
    try {
      await api.post(`/unidade/${unidadeSel.id}/andares`, {
        ...novoAndar,
        parent_id: novoAndar.parent_id || null,
      });
      setMsg('Andar criado.');
      setNovoAndar({ nome: '', tipo: 'andar', parent_id: '' });
      await carregarArvore(unidadeSel.id);
    } catch (e) {
      setErr(e.response?.data?.error || 'Erro ao criar andar.');
    } finally {
      setSaving(false);
    }
  };

  const handleCriarEspaco = async () => {
    if (!novoEspaco.nome.trim()) {
      setErr('Nome do espaço é obrigatório');
      return;
    }
    setSaving(true);
    setErr('');
    setMsg('');
    try {
      await api.post('/salas/ambientes', novoEspaco);
      setMsg('Espaço criado.');
      setNovoEspaco({ ...novoEspaco, nome: '', capacidade: 1, vsf_room_key: '' });
      await carregarArvore(unidadeSel.id);
    } catch (e) {
      setErr(e.response?.data?.error || 'Erro ao criar espaço.');
    } finally {
      setSaving(false);
    }
  };

  const handleDesativarEspaco = async (id) => {
    setSaving(true);
    try {
      await api.delete(`/salas/ambientes/${id}`);
      setMsg('Espaço desativado.');
      await carregarArvore(unidadeSel.id);
    } catch (e) {
      setErr('Erro ao desativar espaço.');
    } finally {
      setSaving(false);
    }
  };

  const listarAndares = () => (arvore?.andares || []).filter((a) => !a.parent_id);
  const subAndares = (id) => (arvore?.andares || []).filter((a) => a.parent_id === id);
  const espacosDoAndar = (id) => (arvore?.andares || []).find((a) => a.id === id)?.espacos || [];

  return (
    <>
      {msg && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {msg}
        </Alert>
      )}
      {err && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {err}
        </Alert>
      )}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                Instalações
              </Typography>
              {unidades.length === 0 && (
                <Typography variant="body2" color="text.secondary">
                  Nenhuma instalação.
                </Typography>
              )}
              <Stack spacing={1} sx={{ mb: 2 }}>
                {unidades.map((u) => (
                  <Card
                    key={u.id}
                    onClick={() => setUnidadeSel(u)}
                    sx={{
                      cursor: 'pointer',
                      border: unidadeSel?.id === u.id ? '2px solid #1976d2' : '1px solid #e0e0e0',
                    }}
                  >
                    <CardContent sx={{ py: 1 }}>
                      <Stack direction="row" alignItems="center" spacing={1}>
                        <BusinessIcon color="primary" />
                        <Box>
                          <Typography variant="body2" fontWeight={600}>
                            {u.nome}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {LABEL_TIPO[u.tipo] || u.tipo}
                          </Typography>
                        </Box>
                      </Stack>
                    </CardContent>
                  </Card>
                ))}
              </Stack>
              <Divider sx={{ my: 2 }} />
              <Typography variant="subtitle2" gutterBottom>
                Nova instalação
              </Typography>
              <Stack spacing={1}>
                <TextField
                  label="Nome"
                  size="small"
                  value={novaUnidade.nome}
                  onChange={(e) => setNovaUnidade({ ...novaUnidade, nome: e.target.value })}
                />
                <TextField
                  select
                  label="Tipo"
                  size="small"
                  value={novaUnidade.tipo}
                  onChange={(e) => setNovaUnidade({ ...novaUnidade, tipo: e.target.value })}
                >
                  {TIPOS_UNIDADE.map((t) => (
                    <MenuItem key={t} value={t}>
                      {LABEL_TIPO[t]}
                    </MenuItem>
                  ))}
                </TextField>
                <Button variant="contained" onClick={handleCriarUnidade} disabled={saving}>
                  <AddIcon /> Criar
                </Button>
              </Stack>
            </Paper>
          </Grid>
          <Grid item xs={12} md={8}>
            {!unidadeSel ? (
              <Paper sx={{ p: 3, textAlign: 'center' }}>
                <Typography color="text.secondary">Selecione uma instalação.</Typography>
              </Paper>
            ) : (
              <>
                <Paper sx={{ p: 2, mb: 2 }}>
                  <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                    {arvore?.unidade?.nome}
                  </Typography>
                  {listarAndares().map((andar) => (
                    <Box key={andar.id} sx={{ mb: 2, pl: 1, borderLeft: '3px solid #1976d2' }}>
                      <Stack direction="row" alignItems="center" spacing={1}>
                        <MeetingRoomIcon color="primary" fontSize="small" />
                        <Typography variant="body2" fontWeight={600}>
                          {andar.nome} ({LABEL_TIPO[andar.tipo] || andar.tipo})
                        </Typography>
                      </Stack>
                      <Box sx={{ pl: 3, mt: 0.5 }}>
                        {espacosDoAndar(andar.id).map((esp) => (
                          <Stack
                            key={esp.id}
                            direction="row"
                            alignItems="center"
                            spacing={1}
                            sx={{ mb: 0.5 }}
                          >
                            <Chip
                              size="small"
                              label={`${esp.nome} · ${esp.capacidade} lugar(es)`}
                              variant="outlined"
                            />
                            <IconButton size="small" onClick={() => handleDesativarEspaco(esp.id)}>
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </Stack>
                        ))}
                      </Box>
                      {subAndares(andar.id).map((sub) => (
                        <Box key={sub.id} sx={{ pl: 3, mt: 1 }}>
                          <Typography variant="body2" color="primary" fontWeight={600}>
                            ↳ {sub.nome}
                          </Typography>
                          <Box sx={{ pl: 3 }}>
                            {sub.espacos?.map((esp) => (
                              <Stack
                                key={esp.id}
                                direction="row"
                                alignItems="center"
                                spacing={1}
                                sx={{ mb: 0.5 }}
                              >
                                <Chip
                                  size="small"
                                  label={`${esp.nome} · ${esp.capacidade} lugar(es)`}
                                  variant="outlined"
                                />
                                <IconButton
                                  size="small"
                                  onClick={() => handleDesativarEspaco(esp.id)}
                                >
                                  <DeleteIcon fontSize="small" />
                                </IconButton>
                              </Stack>
                            ))}
                          </Box>
                        </Box>
                      ))}
                    </Box>
                  ))}
                  {listarAndares().length === 0 && (
                    <Typography variant="body2" color="text.secondary">
                      Nenhum andar ainda.
                    </Typography>
                  )}
                </Paper>
                <Paper sx={{ p: 2, mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Adicionar andar/setor
                  </Typography>
                  <Stack direction="row" spacing={1} alignItems="center">
                    <TextField
                      label="Nome"
                      size="small"
                      value={novoAndar.nome}
                      onChange={(e) => setNovoAndar({ ...novoAndar, nome: e.target.value })}
                    />
                    <TextField
                      select
                      label="Tipo"
                      size="small"
                      value={novoAndar.tipo}
                      onChange={(e) => setNovoAndar({ ...novoAndar, tipo: e.target.value })}
                    >
                      {TIPOS_ANDAR.map((t) => (
                        <MenuItem key={t} value={t}>
                          {LABEL_TIPO[t] || t}
                        </MenuItem>
                      ))}
                    </TextField>
                    <TextField
                      select
                      label="Dentro de"
                      size="small"
                      value={novoAndar.parent_id}
                      onChange={(e) => setNovoAndar({ ...novoAndar, parent_id: e.target.value })}
                      sx={{ minWidth: 160 }}
                    >
                      <MenuItem value="">— nenhum —</MenuItem>
                      {listarAndares().map((a) => (
                        <MenuItem key={a.id} value={a.id}>
                          {a.nome}
                        </MenuItem>
                      ))}
                    </TextField>
                    <Button variant="contained" onClick={handleCriarAndar} disabled={saving}>
                      <AddIcon />
                    </Button>
                  </Stack>
                </Paper>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Adicionar espaço
                  </Typography>
                  <Grid container spacing={1}>
                    <Grid item xs={3}>
                      <TextField
                        label="Nome"
                        size="small"
                        fullWidth
                        value={novoEspaco.nome}
                        onChange={(e) => setNovoEspaco({ ...novoEspaco, nome: e.target.value })}
                      />
                    </Grid>
                    <Grid item xs={2}>
                      <TextField
                        select
                        label="Tipo"
                        size="small"
                        fullWidth
                        value={novoEspaco.tipo}
                        onChange={(e) => setNovoEspaco({ ...novoEspaco, tipo: e.target.value })}
                      >
                        {TIPOS_ESPACO.map((t) => (
                          <MenuItem key={t} value={t}>
                            {LABEL_TIPO[t] || t}
                          </MenuItem>
                        ))}
                      </TextField>
                    </Grid>
                    <Grid item xs={2}>
                      <TextField
                        label="Lugares"
                        type="number"
                        size="small"
                        fullWidth
                        value={novoEspaco.capacidade}
                        onChange={(e) =>
                          setNovoEspaco({ ...novoEspaco, capacidade: Number(e.target.value) })
                        }
                      />
                    </Grid>
                    <Grid item xs={3}>
                      <TextField
                        select
                        label="Andar"
                        size="small"
                        fullWidth
                        value={novoEspaco.andar_setor_id}
                        onChange={(e) =>
                          setNovoEspaco({ ...novoEspaco, andar_setor_id: e.target.value })
                        }
                      >
                        <MenuItem value="">— sem andar —</MenuItem>
                        {listarAndares().map((a) => (
                          <MenuItem key={a.id} value={a.id}>
                            {a.nome}
                          </MenuItem>
                        ))}
                        {listarAndares()
                          .flatMap((a) => subAndares(a.id))
                          .map((s) => (
                            <MenuItem key={s.id} value={s.id}>
                              ↳ {s.nome}
                            </MenuItem>
                          ))}
                      </TextField>
                    </Grid>
                    <Grid item xs={12}>
                      <Button variant="contained" onClick={handleCriarEspaco} disabled={saving}>
                        <AddIcon /> Adicionar
                      </Button>
                    </Grid>
                  </Grid>
                </Paper>
              </>
            )}
          </Grid>
        </Grid>
      )}
    </>
  );
};

export default ConfigurarUnidadePage;
