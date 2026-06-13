/**
 * Dashboard de Agentes SDR
 *
 * Permite que profissionais criem e gerenciem seus próprios
 * agentes SDR (Sales Development Representative) via interface.
 *
 * Funcionalidades:
 * - Criar novo agente
 * - Editar configuração (nome, valor, perguntas, regras)
 * - Testar agente em tempo real
 * - Ver estatísticas de conversão
 * - Ativar/desativar agente
 *
 * Migrado de antd → MUI em 2026-06-11.
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Grid,
  Button,
  TextField,
  MenuItem,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Snackbar,
  Chip,
  Typography,
  Divider,
  Alert,
  Tabs,
  Tab,
  Checkbox,
  FormControlLabel,
  Tooltip,
  Stack,
  IconButton,
} from '@mui/material';
import {
  SmartToy as RobotIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  PlayCircle as PlayCircleIcon,
  Save as SaveIcon,
  Close as CloseIcon,
  Check as CheckIcon,
  BarChart as BarChartIcon,
  ChatBubble as MessageIcon,
  Settings as SettingIcon,
  ContentCopy as CopyIcon,
} from '@mui/icons-material';
import api from '../../services/api';

// Perguntas padrão de anamnese
const PERGUNTAS_DEFAULT = [
  { id: 'nome_completo', texto: 'Qual é o seu nome completo?', obrigatoria: true, tipo: 'texto' },
  { id: 'data_nascimento', texto: 'Qual é a sua data de nascimento?', obrigatoria: true, tipo: 'data' },
  { id: 'email', texto: 'Qual é o seu melhor e-mail?', obrigatoria: true, tipo: 'texto' },
  { id: 'condicao_principal', texto: 'Qual é a condição de saúde principal que deseja tratar?', obrigatoria: true, tipo: 'texto' },
  { id: 'sintomas_atuais', texto: 'Quais sintomas está sentindo no momento?', obrigatoria: true, tipo: 'texto' },
  { id: 'medicamentos_uso', texto: 'Quais medicamentos está tomando atualmente?', obrigatoria: true, tipo: 'texto' },
  { id: 'historico', texto: 'Já fez tratamento com Cannabis Medicinal antes?', obrigatoria: true, tipo: 'opcoes', opcoes: ['Sim', 'Não'] },
  { id: 'alergias', texto: 'Tem alguma alergia medicamentosa?', obrigatoria: true, tipo: 'texto' },
  { id: 'peso_altura', texto: 'Qual é seu peso e altura?', obrigatoria: true, tipo: 'texto' },
];

const REGRAS_DEFAULT = {
  pode_dar_diagnostico: false,
  pode_prescrever: false,
  pode_coletar_anamnese: true,
  pode_agendar: true,
  pode_receber_documentos: true,
  pode_receber_selfie: false,
  respostas_curtas: true,
  tom_empatico: true,
};

const DIAS_SEMANA = [
  { key: 'segunda', label: 'Seg' },
  { key: 'terca', label: 'Ter' },
  { key: 'quarta', label: 'Qua' },
  { key: 'quinta', label: 'Qui' },
  { key: 'sexta', label: 'Sex' },
  { key: 'sabado', label: 'Sáb' },
];

const TONS = [
  'Empático e profissional',
  'Formal e médico',
  'Amigável e descontraído',
  'Técnico e detalhista',
];

const TIPOS_PERGUNTA = [
  { value: 'texto', label: 'Texto' },
  { value: 'numero', label: 'Número' },
  { value: 'data', label: 'Data' },
  { value: 'opcoes', label: 'Opções' },
];

const TabPanel = ({ children, value, index }) => (
  <Box hidden={value !== index} sx={{ pt: 2 }}>
    {value === index && children}
  </Box>
);

const AgentesSDRPage = () => {
  const [agentes, setAgentes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [testModalVisible, setTestModalVisible] = useState(false);
  const [editingAgente, setEditingAgente] = useState(null);
  const [aba, setAba] = useState(0);

  // Form state (substitui antd Form)
  const [form, setForm] = useState({
    nome: '',
    tom: TONS[0],
    valor: '',
    instance_name: '',
  });
  const [formError, setFormError] = useState({});

  // Estado do agente em edição
  const [perguntas, setPerguntas] = useState(PERGUNTAS_DEFAULT);
  const [regras, setRegras] = useState(REGRAS_DEFAULT);
  const [horarios, setHorarios] = useState({
    dias: ['terca', 'quarta', 'quinta', 'sexta'],
    inicio: '09:00',
    fim: '18:00',
  });

  // Estado do teste
  const [testMensagem, setTestMensagem] = useState('');
  const [testResposta, setTestResposta] = useState('');
  const [testLoading, setTestLoading] = useState(false);
  const [agenteTestando, setAgenteTestando] = useState(null);

  // Snackbar (substitui antd message)
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const notify = (message, severity = 'success') =>
    setSnackbar({ open: true, message, severity });

  useEffect(() => {
    carregarAgentes();
  }, []);

  const carregarAgentes = async () => {
    setLoading(true);
    try {
      const response = await api.get('/agentes');
      setAgentes(response.data.agentes || []);
    } catch (error) {
      notify('Erro ao carregar agentes', 'error');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const abrirModalCriar = () => {
    setEditingAgente(null);
    setPerguntas(PERGUNTAS_DEFAULT);
    setRegras(REGRAS_DEFAULT);
    setHorarios({
      dias: ['terca', 'quarta', 'quinta', 'sexta'],
      inicio: '09:00',
      fim: '18:00',
    });
    setForm({
      nome: 'Assistente Virtual',
      tom: 'Empático e profissional',
      valor: 'R$ 650,00',
      instance_name: '',
    });
    setFormError({});
    setAba(0);
    setModalVisible(true);
  };

  const abrirModalEditar = (agente) => {
    setEditingAgente(agente);
    setForm({
      nome: agente.nome || '',
      tom: agente.tom || TONS[0],
      valor: agente.valor || '',
      instance_name: agente.instance || '',
    });
    setFormError({});

    // Carregar regras extras do agente
    api.get(`/agentes/${agente.id}`).then((response) => {
      const data = response.data;
      setPerguntas(data.perguntas || PERGUNTAS_DEFAULT);
      setRegras(data.regras || REGRAS_DEFAULT);
      setHorarios(data.horarios || horarios);
    }).catch(console.error);

    setAba(0);
    setModalVisible(true);
  };

  const salvarAgente = async () => {
    // Validação manual (substitui Form.Item rules)
    const erros = {};
    if (!form.nome?.trim()) erros.nome = 'Informe o nome do agente';
    if (!form.valor?.trim()) erros.valor = 'Informe o valor';
    if (Object.keys(erros).length > 0) {
      setFormError(erros);
      return;
    }
    setFormError({});

    const payload = {
      nome: form.nome,
      tom: form.tom,
      valor: form.valor,
      instance_name: form.instance_name,
      perguntas,
      regras,
      horarios,
    };

    try {
      if (editingAgente) {
        await api.put(`/agentes/${editingAgente.id}`, payload);
        notify('Agente atualizado com sucesso!');
      } else {
        await api.post('/agentes', payload);
        notify('Agente criado com sucesso!');
      }
      setModalVisible(false);
      carregarAgentes();
    } catch (error) {
      notify('Erro ao salvar agente', 'error');
    }
  };

  const ativarDesativarAgente = async (agente) => {
    try {
      if (agente.ativo) {
        await api.delete(`/agentes/${agente.id}`);
        notify('Agente desativado');
      } else {
        await api.post(`/agentes/${agente.id}/ativar`);
        notify('Agente ativado');
      }
      carregarAgentes();
    } catch (error) {
      notify('Erro ao atualizar agente', 'error');
    }
  };

  const testarAgente = (agente) => {
    setAgenteTestando(agente);
    setTestMensagem('');
    setTestResposta('');
    setTestModalVisible(true);
  };

  const enviarTeste = async () => {
    if (!testMensagem.trim()) {
      notify('Digite uma mensagem para testar', 'warning');
      return;
    }

    setTestLoading(true);
    try {
      const response = await api.post(`/agentes/${agenteTestando.id}/testar`, {
        mensagem: testMensagem,
      });
      setTestResposta(response.data.resposta);
    } catch (error) {
      notify('Erro ao testar agente', 'error');
      console.error(error);
    } finally {
      setTestLoading(false);
    }
  };

  // Handlers de perguntas
  const adicionarPergunta = () => {
    const novaPergunta = {
      id: `pergunta_${perguntas.length + 1}`,
      texto: '',
      obrigatoria: true,
      tipo: 'texto',
      opcoes: [],
    };
    setPerguntas([...perguntas, novaPergunta]);
  };

  const removerPergunta = (index) => {
    setPerguntas(perguntas.filter((_, i) => i !== index));
  };

  const atualizarPergunta = (index, campo, valor) => {
    const novasPerguntas = [...perguntas];
    novasPerguntas[index][campo] = valor;
    setPerguntas(novasPerguntas);
  };

  // Handlers de regras
  const atualizarRegra = (regra, valor) => {
    setRegras({ ...regras, [regra]: valor });
  };

  // Handlers de horários
  const toggleDia = (dia) => {
    const novosDias = horarios.dias.includes(dia)
      ? horarios.dias.filter((d) => d !== dia)
      : [...horarios.dias, dia];
    setHorarios({ ...horarios, dias: novosDias });
  };

  return (
    <Box sx={{ p: 3 }}>
      <Grid container justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
        <Grid item>
          <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <RobotIcon fontSize="large" />
            Agentes SDR
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Configure e gerencie assistentes virtuais para capturar leads e agendar consultas
          </Typography>
        </Grid>
        <Grid item>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={abrirModalCriar}
            size="large"
          >
            Novo Agente
          </Button>
        </Grid>
      </Grid>

      <Card>
        <TableContainer component={Paper} variant="outlined">
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Nome</TableCell>
                <TableCell>Valor</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Ações</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={4} align="center">Carregando...</TableCell>
                </TableRow>
              ) : agentes.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} align="center">Nenhum agente configurado ainda</TableCell>
                </TableRow>
              ) : (
                agentes.map((agente) => (
                  <TableRow key={agente.id}>
                    <TableCell>
                      <Stack direction="row" spacing={1} alignItems="center">
                        <RobotIcon sx={{ color: agente.ativo ? 'success.main' : 'text.disabled' }} />
                        <Typography variant="body2" fontWeight={agente.ativo ? 'bold' : 'normal'}>
                          {agente.nome}
                        </Typography>
                      </Stack>
                    </TableCell>
                    <TableCell>
                      <Chip size="small" color="primary" label={agente.valor || 'R$ 350,00'} />
                    </TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        color={agente.ativo ? 'success' : 'default'}
                        label={agente.ativo ? 'Ativo' : 'Inativo'}
                      />
                    </TableCell>
                    <TableCell align="right">
                      <Stack direction="row" spacing={0.5} justifyContent="flex-end">
                        <Tooltip title="Testar">
                          <span>
                            <IconButton
                              size="small"
                              color="primary"
                              onClick={() => testarAgente(agente)}
                              disabled={!agente.ativo}
                            >
                              <PlayCircleIcon />
                            </IconButton>
                          </span>
                        </Tooltip>
                        <Tooltip title="Editar">
                          <IconButton size="small" color="primary" onClick={() => abrirModalEditar(agente)}>
                            <EditIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title={agente.ativo ? 'Desativar' : 'Ativar'}>
                          <IconButton
                            size="small"
                            color={agente.ativo ? 'error' : 'success'}
                            onClick={() => ativarDesativarAgente(agente)}
                          >
                            {agente.ativo ? <DeleteIcon /> : <CheckIcon />}
                          </IconButton>
                        </Tooltip>
                      </Stack>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Card>

      {/* Modal de Criar/Editar Agente */}
      <Dialog
        open={modalVisible}
        onClose={() => setModalVisible(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Stack direction="row" alignItems="center" justifyContent="space-between">
            <span>{editingAgente ? 'Editar Agente' : 'Criar Novo Agente'}</span>
            <IconButton onClick={() => setModalVisible(false)}>
              <CloseIcon />
            </IconButton>
          </Stack>
        </DialogTitle>
        <DialogContent dividers>
          <Tabs value={aba} onChange={(_, v) => setAba(v)} sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tab icon={<SettingIcon />} iconPosition="start" label="Básico" />
            <Tab icon={<MessageIcon />} iconPosition="start" label="Anamnese" />
            <Tab icon={<SettingIcon />} iconPosition="start" label="Regras" />
            <Tab icon={<BarChartIcon />} iconPosition="start" label="Horários" />
          </Tabs>

          {/* Aba: Básico */}
          <TabPanel value={aba} index={0}>
            <Stack spacing={2} sx={{ pt: 2 }}>
              <TextField
                label="Nome do Agente"
                fullWidth
                value={form.nome}
                onChange={(e) => setForm({ ...form, nome: e.target.value })}
                error={!!formError.nome}
                helperText={formError.nome}
                required
                placeholder="Ex: LIA, Assistente Virtual, SDR Dr. João"
              />
              <TextField
                label="Tom de Voz"
                select
                fullWidth
                value={form.tom}
                onChange={(e) => setForm({ ...form, tom: e.target.value })}
              >
                {TONS.map((tom) => (
                  <MenuItem key={tom} value={tom}>{tom}</MenuItem>
                ))}
              </TextField>
              <TextField
                label="Valor da Consulta"
                fullWidth
                value={form.valor}
                onChange={(e) => setForm({ ...form, valor: e.target.value })}
                error={!!formError.valor}
                helperText={formError.valor}
                required
                placeholder="R$ 650,00"
              />
              <TextField
                label="Instance do WhatsApp (opcional)"
                fullWidth
                value={form.instance_name}
                onChange={(e) => setForm({ ...form, instance_name: e.target.value })}
                placeholder="Nome da instância Evolution API"
              />
            </Stack>
          </TabPanel>

          {/* Aba: Anamnese */}
          <TabPanel value={aba} index={1}>
            <Alert severity="info" sx={{ mb: 2 }}>
              <strong>Perguntas da Anamnese.</strong> Estas perguntas serão feitas ao paciente APÓS a confirmação do pagamento.
            </Alert>

            <Stack spacing={1.5}>
              {perguntas.map((pergunta, index) => (
                <Card key={pergunta.id} variant="outlined">
                  <CardContent sx={{ pb: 1.5 }}>
                    <Grid container spacing={1.5} alignItems="center">
                      <Grid item xs={12} md={7}>
                        <TextField
                          fullWidth
                          size="small"
                          value={pergunta.texto}
                          onChange={(e) => atualizarPergunta(index, 'texto', e.target.value)}
                          placeholder="Texto da pergunta"
                        />
                      </Grid>
                      <Grid item xs={6} md={2}>
                        <TextField
                          select
                          fullWidth
                          size="small"
                          value={pergunta.tipo}
                          onChange={(e) => atualizarPergunta(index, 'tipo', e.target.value)}
                        >
                          {TIPOS_PERGUNTA.map((t) => (
                            <MenuItem key={t.value} value={t.value}>{t.label}</MenuItem>
                          ))}
                        </TextField>
                      </Grid>
                      <Grid item xs={4} md={2}>
                        <FormControlLabel
                          control={
                            <Checkbox
                              size="small"
                              checked={pergunta.obrigatoria}
                              onChange={(e) => atualizarPergunta(index, 'obrigatoria', e.target.checked)}
                            />
                          }
                          label="Obrig."
                        />
                      </Grid>
                      <Grid item xs={2} md={1} sx={{ textAlign: 'right' }}>
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => removerPergunta(index)}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Grid>
                      {pergunta.tipo === 'opcoes' && (
                        <Grid item xs={12}>
                          <TextField
                            fullWidth
                            size="small"
                            value={(pergunta.opcoes || []).join(', ')}
                            onChange={(e) =>
                              atualizarPergunta(
                                index,
                                'opcoes',
                                e.target.value.split(',').map((s) => s.trim())
                              )
                            }
                            placeholder="Opções separadas por vírgula (ex: Sim, Não, Talvez)"
                          />
                        </Grid>
                      )}
                    </Grid>
                  </CardContent>
                </Card>
              ))}
            </Stack>

            <Button
              variant="outlined"
              startIcon={<AddIcon />}
              onClick={adicionarPergunta}
              fullWidth
              sx={{ mt: 2 }}
            >
              Adicionar Pergunta
            </Button>
          </TabPanel>

          {/* Aba: Regras */}
          <TabPanel value={aba} index={2}>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardHeader title="Permissões" titleTypographyProps={{ variant: 'subtitle2' }} />
                  <CardContent>
                    <Stack spacing={1}>
                      {[
                        ['pode_agendar', 'Pode agendar consultas'],
                        ['pode_coletar_anamnese', 'Pode coletar anamnese (após pagamento)'],
                        ['pode_receber_documentos', 'Pode receber documentos'],
                        ['pode_receber_selfie', 'Pode receber selfie (reconhecimento facial)'],
                      ].map(([key, label]) => (
                        <FormControlLabel
                          key={key}
                          control={
                            <Checkbox
                              checked={!!regras[key]}
                              onChange={(e) => atualizarRegra(key, e.target.checked)}
                            />
                          }
                          label={label}
                        />
                      ))}
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardHeader title="Restrições" titleTypographyProps={{ variant: 'subtitle2' }} />
                  <CardContent>
                    <Stack spacing={1}>
                      {[
                        ['pode_dar_diagnostico', 'Pode dar diagnósticos'],
                        ['pode_prescrever', 'Pode prescrever medicamentos'],
                      ].map(([key, label]) => (
                        <FormControlLabel
                          key={key}
                          control={
                            <Checkbox
                              checked={!!regras[key]}
                              onChange={(e) => atualizarRegra(key, e.target.checked)}
                            />
                          }
                          label={label}
                        />
                      ))}
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>

            <Divider sx={{ my: 2 }} />

            <Card variant="outlined">
              <CardHeader title="Estilo de Resposta" titleTypographyProps={{ variant: 'subtitle2' }} />
              <CardContent>
                <Stack spacing={1}>
                  {[
                    ['respostas_curtas', 'Respostas curtas (máx 3 frases)'],
                    ['tom_empatico', 'Tom empático e acolhedor'],
                  ].map(([key, label]) => (
                    <FormControlLabel
                      key={key}
                      control={
                        <Checkbox
                          checked={!!regras[key]}
                          onChange={(e) => atualizarRegra(key, e.target.checked)}
                        />
                      }
                      label={label}
                    />
                  ))}
                </Stack>
              </CardContent>
            </Card>
          </TabPanel>

          {/* Aba: Horários */}
          <TabPanel value={aba} index={3}>
            <Alert severity="info" sx={{ mb: 2 }}>
              <strong>Horários de Atendimento.</strong> Defina quando o agente pode iniciar conversas e agendar consultas.
            </Alert>

            <Stack direction="row" spacing={1} sx={{ mb: 3, flexWrap: 'wrap' }}>
              {DIAS_SEMANA.map((dia) => (
                <Button
                  key={dia.key}
                  variant={horarios.dias.includes(dia.key) ? 'contained' : 'outlined'}
                  onClick={() => toggleDia(dia.key)}
                  size="small"
                >
                  {dia.label}
                </Button>
              ))}
            </Stack>

            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>Horário de Início</Typography>
                <TextField
                  type="time"
                  fullWidth
                  value={horarios.inicio}
                  onChange={(e) => setHorarios({ ...horarios, inicio: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>Horário de Término</Typography>
                <TextField
                  type="time"
                  fullWidth
                  value={horarios.fim}
                  onChange={(e) => setHorarios({ ...horarios, fim: e.target.value })}
                />
              </Grid>
            </Grid>
          </TabPanel>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setModalVisible(false)}>Cancelar</Button>
          <Button variant="contained" startIcon={<SaveIcon />} onClick={salvarAgente}>
            {editingAgente ? 'Salvar Alterações' : 'Criar Agente'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Modal de Teste */}
      <Dialog
        open={testModalVisible}
        onClose={() => setTestModalVisible(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Testar Agente: {agenteTestando?.nome}
          <IconButton
            onClick={() => setTestModalVisible(false)}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            <strong>Teste de Agente.</strong> Digite uma mensagem como se fosse um paciente para testar a resposta do agente.
          </Alert>

          <TextField
            multiline
            rows={3}
            fullWidth
            value={testMensagem}
            onChange={(e) => setTestMensagem(e.target.value)}
            placeholder="Digite a mensagem do paciente aqui..."
            sx={{ mb: 2 }}
          />

          <Button
            variant="contained"
            startIcon={<PlayCircleIcon />}
            onClick={enviarTeste}
            disabled={testLoading}
            fullWidth
          >
            {testLoading ? 'Enviando...' : 'Enviar Teste'}
          </Button>

          {testResposta && (
            <>
              <Divider sx={{ my: 2 }} />
              <Card variant="outlined" sx={{ bgcolor: 'grey.100' }}>
                <CardContent>
                  <Typography variant="subtitle2">Resposta do Agente:</Typography>
                  <Box sx={{ mt: 1, whiteSpace: 'pre-wrap' }}>{testResposta}</Box>
                </CardContent>
              </Card>
            </>
          )}
        </DialogContent>
      </Dialog>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          variant="filled"
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default AgentesSDRPage;
