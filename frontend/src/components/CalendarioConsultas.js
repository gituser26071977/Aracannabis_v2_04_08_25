import React, { useState, useEffect } from 'react';
import useRemember from '../hooks/useRemember';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import {
  Paper,
  Typography,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Alert,
  Chip,
  Tooltip,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Email as EmailIcon,
  EventAvailable as EventAvailableIcon,
} from '@mui/icons-material';
import { consultasService, pacientesService } from '../services/api';
import EmptyState from './EmptyState';

import useNotifier from '../hooks/useNotifier';
const CalendarioConsultas = () => {
  const { notify, NotifierElement } = useNotifier();
  const [eventos, setEventos] = useState([]);
  const [pacientes, setPacientes] = useState([]);
  const [loading, setLoading] = useState(true);
  // rc.16: separar erros de pacientes vs consultas para nao mostrar
  // "erro tecnico" quando apenas o resultado esta vazio (empty state).
  const [pacientesError, setPacientesError] = useState('');
  const [consultasError, setConsultasError] = useState('');
  // rc.16: erros de dialog (salvar/cancelar/enviar lembretes) migraram
  // para useNotifier.notify() — o Alert global antigo foi removido para
  // nao confundir empty-state com erro tecnico.
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingConsulta, setEditingConsulta] = useState(null);

  // Estado do formulário
  const [rememberedTipo, setRememberedTipo] = useRemember('tipo_consulta_padrao', 'presencial');
  const [rememberedDuracao, setRememberedDuracao] = useRemember('duracao_consulta_padrao', 60);
  const [formData, setFormData] = useState({
    paciente_id: '',
    data_hora: '',
    duracao_minutos: 60,
    tipo_consulta: 'presencial',
    observacoes: '',
  });

  // Pré-preencher com valores lembrados do médico
  useEffect(() => {
    setFormData((prev) => ({
      ...prev,
      tipo_consulta: rememberedTipo,
      duracao_minutos: rememberedDuracao,
    }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Carregar dados iniciais
  // rc.16: separa erros de pacientes vs consultas. Antes, qualquer falha
  // de pacientes mascarava o calendario (mostrava "nao foi possivel
  // carregar dados do calendario") mesmo quando as consultas estavam OK.
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);

      // Carregar pacientes para o select (independente)
      try {
        const pacientesData = await pacientesService.listar();
        setPacientes(pacientesData.pacientes || []);
        setPacientesError('');
      } catch (err) {
        if (process.env.NODE_ENV !== 'production')
          console.error('Erro ao carregar pacientes:', err);
        setPacientesError('Não foi possível carregar a lista de pacientes.');
      }

      // Carregar consultas do mês atual (independente)
      await carregarConsultas();

      setLoading(false);
    };

    fetchData();
  }, []);

  // Carregar consultas
  // rc.16: usa consultasError (separado) em vez de error global.
  // Retorno bem-sucedido com lista vazia nao dispara mais alerta de erro.
  const carregarConsultas = async (ano = null, mes = null) => {
    try {
      const agora = new Date();
      const anoAtual = ano || agora.getFullYear();
      const mesAtual = mes || agora.getMonth() + 1;

      const data = await consultasService.obterCalendario(anoAtual, mesAtual);
      setEventos(data.eventos || []);
      setConsultasError('');
    } catch (err) {
      if (process.env.NODE_ENV !== 'production') console.error('Erro ao carregar consultas:', err);
      setConsultasError('Não foi possível carregar as consultas. Tente recarregar a página.');
      // Mantem eventos anteriores em tela (nao limpa) para o usuario
      // nao perder o que ja estava vendo ao navegar entre meses.
    }
  };

  // Manipular clique em data
  const handleDateClick = (arg) => {
    setEditingConsulta(null);
    setFormData({
      paciente_id: '',
      data_hora: arg.dateStr + 'T09:00',
      duracao_minutos: 60,
      tipo_consulta: 'presencial',
      observacoes: '',
    });
    setDialogOpen(true);
  };

  // Manipular clique em evento
  const handleEventClick = (clickInfo) => {
    const evento = clickInfo.event;
    const props = evento.extendedProps;

    setEditingConsulta({
      id: evento.id,
      paciente_id: props.paciente_id,
      data_hora: evento.start.toISOString().slice(0, 16),
      duracao_minutos: Math.round((evento.end - evento.start) / (1000 * 60)),
      tipo_consulta: props.tipo_consulta,
      observacoes: props.observacoes || '',
      status: props.status,
    });

    setFormData({
      paciente_id: props.paciente_id,
      data_hora: evento.start.toISOString().slice(0, 16),
      duracao_minutos: Math.round((evento.end - evento.start) / (1000 * 60)),
      tipo_consulta: props.tipo_consulta,
      observacoes: props.observacoes || '',
    });

    setDialogOpen(true);
  };

  // Manipular mudança de mês/ano
  const handleDatesSet = (dateInfo) => {
    const data = new Date(dateInfo.start);
    carregarConsultas(data.getFullYear(), data.getMonth() + 1);
  };

  // Manipular mudança no formulário
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  // Salvar consulta
  const handleSalvarConsulta = async () => {
    try {
      if (editingConsulta) {
        // Atualizar consulta existente
        await consultasService.atualizar(editingConsulta.id, formData);
      } else {
        // Criar nova consulta
        await consultasService.criar(formData);
      }

      // Persistir tipo/duração como novos padrões (aprende com o médico)
      setRememberedTipo(formData.tipo_consulta);
      setRememberedDuracao(formData.duracao_minutos);

      // Recarregar eventos
      await carregarConsultas();

      // Fechar diálogo
      setDialogOpen(false);
      setEditingConsulta(null);
    } catch (err) {
      if (process.env.NODE_ENV !== 'production') console.error('Erro ao salvar consulta:', err);
      notify(err.error || 'Não foi possível salvar a consulta', 'error');
    }
  };

  // Cancelar consulta
  const handleCancelarConsulta = async () => {
    if (!editingConsulta) return;

    try {
      await consultasService.cancelar(editingConsulta.id);
      await carregarConsultas();
      setDialogOpen(false);
      setEditingConsulta(null);
    } catch (err) {
      if (process.env.NODE_ENV !== 'production') console.error('Erro ao cancelar consulta:', err);
      notify('Não foi possível cancelar a consulta', 'error');
    }
  };

  // Enviar lembretes
  const handleEnviarLembretes = async () => {
    try {
      const response = await consultasService.enviarLembretes();
      notify(response.message, 'info');
    } catch (err) {
      if (process.env.NODE_ENV !== 'production') console.error('Erro ao enviar lembretes:', err);
      notify('Não foi possível enviar os lembretes', 'error');
    }
  };

  // Fechar diálogo
  const handleFecharDialog = () => {
    setDialogOpen(false);
    setEditingConsulta(null);
  };

  // Obter cor do status
  const getStatusColor = (status) => {
    const colors = {
      agendada: 'primary',
      confirmada: 'success',
      realizada: 'default',
      cancelada: 'error',
    };
    return colors[status] || 'primary';
  };

  // Configurações do FullCalendar
  const calendarOptions = {
    plugins: [dayGridPlugin, timeGridPlugin, interactionPlugin],
    initialView: 'dayGridMonth',
    headerToolbar: {
      left: 'prev,next today',
      center: 'title',
      right: 'dayGridMonth,timeGridWeek,timeGridDay',
    },
    locale: 'pt-br',
    buttonText: {
      today: 'Hoje',
      month: 'Mês',
      week: 'Semana',
      day: 'Dia',
    },
    height: 'auto',
    selectable: true,
    selectMirror: true,
    dayMaxEvents: true,
    weekends: true,
    dateClick: handleDateClick,
    eventClick: handleEventClick,
    datesSet: handleDatesSet,
    events: eventos,
    eventDisplay: 'block',
    displayEventTime: true,
    eventTimeFormat: {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    },
  };

  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <NotifierElement />{' '}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6">📅 Calendário de Consultas</Typography>

        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Enviar lembretes das próximas 24h">
            <Button
              variant="outlined"
              color="info"
              startIcon={<EmailIcon />}
              onClick={handleEnviarLembretes}
              size="small"
            >
              Lembretes
            </Button>
          </Tooltip>

          <Button
            variant="contained"
            color="primary"
            startIcon={<AddIcon />}
            onClick={() => {
              setEditingConsulta(null);
              setFormData({
                paciente_id: '',
                data_hora: new Date().toISOString().slice(0, 16),
                duracao_minutos: 60,
                tipo_consulta: 'presencial',
                observacoes: '',
              });
              setDialogOpen(true);
            }}
          >
            Nova Consulta
          </Button>
        </Box>
      </Box>
      {pacientesError && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          {pacientesError}
        </Alert>
      )}
      {consultasError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {consultasError}
        </Alert>
      )}
      {/*
        rc.16: alertas antigos de `error` para o calendario foram
        removidos. Erros de salvar/cancelar consulta continuam
        aparecendo inline no Dialog (via `setError` no escopo do form).
      */}
      {/* Legenda de cores */}
      <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
        <Chip label="Agendada" color="primary" size="small" />
        <Chip label="Confirmada" color="success" size="small" />
        <Chip label="Realizada" color="default" size="small" />
        <Chip label="Cancelada" color="error" size="small" />
      </Box>
      {/* Calendário */}
      <Box sx={{ '& .fc': { fontSize: '0.875rem' } }}>
        <FullCalendar {...calendarOptions} />
      </Box>
      {/* rc.16: empty state amigavel para profissionais sem consultas.
          Mantemos o calendario visivel acima para o usuario ainda poder
          clicar em datas e criar a primeira consulta. */}
      {!loading && !consultasError && eventos.length === 0 && (
        <Box sx={{ mt: 2 }}>
          <EmptyState
            icon={<EventAvailableIcon sx={{ fontSize: 72 }} />}
            title="Nenhuma consulta agendada"
            description="Você ainda não tem consultas neste período. Clique em uma data no calendário ou use o botão 'Nova Consulta' acima para começar."
            minHeight={200}
          />
        </Box>
      )}
      {/* Diálogo de consulta */}
      <Dialog open={dialogOpen} onClose={handleFecharDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingConsulta ? 'Editar Consulta' : 'Nova Consulta'}
          {editingConsulta && (
            <Chip
              label={editingConsulta.status}
              color={getStatusColor(editingConsulta.status)}
              size="small"
              sx={{ ml: 2 }}
            />
          )}
        </DialogTitle>

        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth required>
                <InputLabel>Paciente</InputLabel>
                <Select
                  name="paciente_id"
                  value={formData.paciente_id}
                  onChange={handleInputChange}
                  label="Paciente"
                >
                  {pacientes.map((paciente) => (
                    <MenuItem key={paciente.id} value={paciente.id}>
                      {paciente.nome}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                name="data_hora"
                label="Data e Hora"
                type="datetime-local"
                value={formData.data_hora}
                onChange={handleInputChange}
                fullWidth
                required
                InputLabelProps={{ shrink: true }}
              />
            </Grid>

            <Grid item xs={12} sm={4}>
              <TextField
                name="duracao_minutos"
                label="Duração (minutos)"
                type="number"
                value={formData.duracao_minutos}
                onChange={handleInputChange}
                fullWidth
                inputProps={{ min: 15, max: 240, step: 15 }}
              />
            </Grid>

            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Tipo</InputLabel>
                <Select
                  name="tipo_consulta"
                  value={formData.tipo_consulta}
                  onChange={handleInputChange}
                  label="Tipo"
                >
                  <MenuItem value="presencial">Presencial</MenuItem>
                  <MenuItem value="telemedicina">Telemedicina</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            {editingConsulta && (
              <Grid item xs={12} sm={4}>
                <FormControl fullWidth>
                  <InputLabel>Status</InputLabel>
                  <Select
                    name="status"
                    value={editingConsulta.status}
                    onChange={(e) =>
                      setEditingConsulta({
                        ...editingConsulta,
                        status: e.target.value,
                      })
                    }
                    label="Status"
                  >
                    <MenuItem value="agendada">Agendada</MenuItem>
                    <MenuItem value="confirmada">Confirmada</MenuItem>
                    <MenuItem value="realizada">Realizada</MenuItem>
                    <MenuItem value="cancelada">Cancelada</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            )}

            <Grid item xs={12}>
              <TextField
                name="observacoes"
                label="Observações"
                value={formData.observacoes}
                onChange={handleInputChange}
                fullWidth
                multiline
                rows={3}
                placeholder="Observações sobre a consulta..."
              />
            </Grid>
          </Grid>
        </DialogContent>

        <DialogActions>
          {editingConsulta && editingConsulta.status !== 'cancelada' && (
            <Button onClick={handleCancelarConsulta} color="error" startIcon={<DeleteIcon />}>
              Cancelar Consulta
            </Button>
          )}

          <Button onClick={handleFecharDialog} color="primary">
            Fechar
          </Button>

          <Button
            onClick={handleSalvarConsulta}
            variant="contained"
            color="primary"
            disabled={!formData.paciente_id || !formData.data_hora}
          >
            {editingConsulta ? 'Atualizar' : 'Agendar'}
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
};

export default CalendarioConsultas;
