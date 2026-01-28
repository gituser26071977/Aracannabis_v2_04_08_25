import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  IconButton,
  Chip,
  LinearProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  TablePagination,
  CircularProgress,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Switch,
  FormControl,
  FormControlLabel,
  InputLabel,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tooltip,
  Badge,
  Select,
} from '@mui/material';
import {
  People as PeopleIcon,
  Assignment as AssignmentIcon,
  Security as SecurityIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Refresh as RefreshIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Add as AddIcon,
  PlayArrow as PlayArrowIcon,
  History as HistoryIcon,
  Settings as SettingsIcon,
  ExpandMore as ExpandMoreIcon,
  Code as CodeIcon,
  Group as GroupIcon,
  Task as TaskIcon,
  Chat as ChatIcon,
  Storage as StorageIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import api, { aiManagementService } from '../services/api';

function AIDashboard() {
  const { currentUser } = useAuth();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [aiStatus, setAiStatus] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [tabValue, setTabValue] = useState(0);
  const [statsMy, setStatsMy] = useState({});
  const [agents, setAgents] = useState([]);
  const [prompts, setPrompts] = useState([]);
  const [crews, setCrews] = useState([]);
  const [llmConfigs, setLlmConfigs] = useState([]);
  const [executionLogs, setExecutionLogs] = useState([]);
  const [availableProviders, setAvailableProviders] = useState([]);
  const [agentLLMSelection, setAgentLLMSelection] = useState({});
  const [agentUpdating, setAgentUpdating] = useState(null);
  
  // Dialog states
  const [openAgentDialog, setOpenAgentDialog] = useState(false);
  const [openPromptDialog, setOpenPromptDialog] = useState(false);
  const [openCrewDialog, setOpenCrewDialog] = useState(false);
  const [openLLMDialog, setOpenLLMDialog] = useState(false);
  const [openExecutionDialog, setOpenExecutionDialog] = useState(false);
  
  // Form states
  const [agentForm, setAgentForm] = useState({
    nome: '',
    descricao: '',
    role: '',
    goal: '',
    backstory: '',
    llm_config_id: '',
    allow_delegation: true,
    max_iter: 3,
    verbose: true,
    memory: true,
    max_tokens: 1000,
    temperature: 0.7,
    tools_config: {},
    is_active: true
  });
  
  const [promptForm, setPromptForm] = useState({
    nome: '',
    descricao: '',
    template: '',
    variables: [],
    categoria: '',
    agent_id: '',
    is_system_prompt: false,
    version: '1.0.0',
    is_active: true
  });
  
  const [crewForm, setCrewForm] = useState({
    nome: '',
    descricao: '',
    process: 'sequential',
    verbose: true,
    memory: true,
    max_iter: 3,
    share_crew: false,
    is_active: true,
    agent_ids: []
  });
  
  const [llmForm, setLlmForm] = useState({
    nome: '',
    provider: 'groq',
    model: 'llama-3.3-70b-versatile',
    api_key_env_var: '',
    base_url: '',
    temperature: 0.7,
    max_tokens: 1000,
    top_p: 1.0,
    frequency_penalty: 0.0,
    presence_penalty: 0.0,
    timeout: 30,
    max_retries: 3,
    is_default: false,
    is_active: true
  });
  
  const [executionForm, setExecutionForm] = useState({
    crew_id: '',
    input_data: {},
    prompt: ''
  });

  const loadDashboardStats = async () => {
    try {
      const response = await api.get('/ai-management/dashboard-stats');
      setStats(response.data.stats);
      setStatsMy(response.data.stats_my || {});
      setAiStatus(response.data.ai_status);
    } catch (error) {
      console.error('Erro ao buscar estatísticas de IA:', error);
    }
  };

  const loadAgents = async () => {
    try {
      const response = await api.get('/ai-management/agents');
      setAgents(response.data.agents);
      setAgentLLMSelection(
        response.data.agents.reduce(
          (acc, agent) => ({
            ...acc,
            [agent.id]: agent.llm_config?.id || ''
          }),
          {}
        )
      );
    } catch (error) {
      console.error('Erro ao buscar agentes:', error);
    }
  };

  const loadPrompts = async () => {
    try {
      const response = await api.get('/ai-management/prompts');
      setPrompts(response.data.prompts);
    } catch (error) {
      console.error('Erro ao buscar prompts:', error);
    }
  };

  const loadCrews = async () => {
    try {
      const response = await api.get('/ai-management/crews');
      setCrews(response.data.crews);
    } catch (error) {
      console.error('Erro ao buscar crews:', error);
    }
  };

  const loadLLMConfigs = async () => {
    try {
      const response = await api.get('/ai-management/llm-configs');
      setLlmConfigs(response.data.llm_configs);
    } catch (error) {
      console.error('Erro ao buscar configurações de LLM:', error);
    }
  };

  const loadExecutionLogs = async () => {
    try {
      const response = await api.get('/ai-management/execution-logs');
      setExecutionLogs(response.data.logs);
    } catch (error) {
      console.error('Erro ao buscar logs de execução:', error);
    }
  };

  const loadAvailableProviders = async () => {
    try {
      const response = await api.get('/ai-management/providers/available');
      setAvailableProviders(response.data.providers);
    } catch (error) {
      console.error('Erro ao buscar provedores disponíveis:', error);
    }
  };

  const handleAssignLLM = async (agentId, llmConfigId) => {
    setAgentUpdating(agentId);
    try {
      await aiManagementService.updateAgent(agentId, { llm_config_id: llmConfigId || null });
      setSuccess('LLM aplicada com sucesso');
      await loadAgents();
    } catch (error) {
      console.error('Erro ao aplicar LLM no agente:', error);
      setError('Não foi possível aplicar LLM ao agente');
    } finally {
      setAgentUpdating(null);
    }
  };

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      await Promise.all([
        loadDashboardStats(),
        loadAgents(),
        loadPrompts(),
        loadCrews(),
        loadLLMConfigs(),
        loadExecutionLogs(),
        loadAvailableProviders()
      ]);
    } catch (error) {
      console.error('Erro ao carregar dados do dashboard de IA:', error);
      setError('Erro ao carregar dados do painel de IA');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (currentUser) {
      loadData();
    }
  }, [currentUser]);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleCreateAgent = async () => {
    try {
      await api.post('/ai-management/agents', agentForm);
      setSuccess('Agente criado com sucesso');
      setOpenAgentDialog(false);
      setAgentForm({
        nome: '',
        descricao: '',
        role: '',
        goal: '',
        backstory: '',
        llm_config_id: '',
        allow_delegation: true,
        max_iter: 3,
        verbose: true,
        memory: true,
        max_tokens: 1000,
        temperature: 0.7,
        tools_config: {},
        is_active: true
      });
      loadAgents();
      loadDashboardStats();
    } catch (error) {
      setError(`Erro ao criar agente: ${error.response?.data?.error || error.message}`);
    }
  };

  const handleCreatePrompt = async () => {
    try {
      await api.post('/ai-management/prompts', promptForm);
      setSuccess('Prompt criado com sucesso');
      setOpenPromptDialog(false);
      setPromptForm({
        nome: '',
        descricao: '',
        template: '',
        variables: [],
        categoria: '',
        agent_id: '',
        is_system_prompt: false,
        version: '1.0.0',
        is_active: true
      });
      loadPrompts();
      loadDashboardStats();
    } catch (error) {
      setError(`Erro ao criar prompt: ${error.response?.data?.error || error.message}`);
    }
  };

  const handleCreateCrew = async () => {
    try {
      await api.post('/ai-management/crews', crewForm);
      setSuccess('Crew criada com sucesso');
      setOpenCrewDialog(false);
      setCrewForm({
        nome: '',
        descricao: '',
        process: 'sequential',
        verbose: true,
        memory: true,
        max_iter: 3,
        share_crew: false,
        is_active: true,
        agent_ids: []
      });
      loadCrews();
      loadDashboardStats();
    } catch (error) {
      setError(`Erro ao criar crew: ${error.response?.data?.error || error.message}`);
    }
  };

  const handleCreateLLMConfig = async () => {
    try {
      await api.post('/ai-management/llm-configs', llmForm);
      setSuccess('Configuração de LLM criada com sucesso');
      setOpenLLMDialog(false);
      setLlmForm({
        nome: '',
        provider: 'groq',
        model: 'llama-3.3-70b-versatile',
        api_key_env_var: '',
        base_url: '',
        temperature: 0.7,
        max_tokens: 1000,
        top_p: 1.0,
        frequency_penalty: 0.0,
        presence_penalty: 0.0,
        timeout: 30,
        max_retries: 3,
        is_default: false,
        is_active: true
      });
      loadLLMConfigs();
      loadDashboardStats();
    } catch (error) {
      setError(`Erro ao criar configuração de LLM: ${error.response?.data?.error || error.message}`);
    }
  };

  const handleExecuteCrew = async (crewId) => {
    try {
      const response = await api.post(`/ai-management/execute/crew/${crewId}`, executionForm);
      setSuccess('Crew executada com sucesso');
      setOpenExecutionDialog(false);
      loadExecutionLogs();
      loadDashboardStats();
    } catch (error) {
      setError(`Erro ao executar crew: ${error.response?.data?.error || error.message}`);
    }
  };

  const handleDeleteAgent = async (agentId) => {
    if (window.confirm('Tem certeza que deseja remover este agente?')) {
      try {
        await api.delete(`/ai-management/agents/${agentId}`);
        setSuccess('Agente removido com sucesso');
        loadAgents();
        loadDashboardStats();
      } catch (error) {
        setError(`Erro ao remover agente: ${error.response?.data?.error || error.message}`);
      }
    }
  };

  const handleDeletePrompt = async (promptId) => {
    if (window.confirm('Tem certeza que deseja remover este prompt?')) {
      try {
        await api.delete(`/ai-management/prompts/${promptId}`);
        setSuccess('Prompt removido com sucesso');
        loadPrompts();
        loadDashboardStats();
      } catch (error) {
        setError(`Erro ao remover prompt: ${error.response?.data?.error || error.message}`);
      }
    }
  };

  const handleDeleteCrew = async (crewId) => {
    if (window.confirm('Tem certeza que deseja remover esta crew?')) {
      try {
        await api.delete(`/ai-management/crews/${crewId}`);
        setSuccess('Crew removida com sucesso');
        loadCrews();
        loadDashboardStats();
      } catch (error) {
        setError(`Erro ao remover crew: ${error.response?.data?.error || error.message}`);
      }
    }
  };

  const handleDeleteLLMConfig = async (configId) => {
    if (window.confirm('Tem certeza que deseja remover esta configuração de LLM?')) {
      try {
        await api.delete(`/ai-management/llm-configs/${configId}`);
        setSuccess('Configuração de LLM removida com sucesso');
        loadLLMConfigs();
        loadDashboardStats();
      } catch (error) {
        setError(`Erro ao remover configuração de LLM: ${error.response?.data?.error || error.message}`);
      }
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'success': return 'success';
      case 'error': return 'error';
      case 'partial': return 'warning';
      default: return 'default';
    }
  };

  const getProviderColor = (provider) => {
    switch (provider) {
      case 'groq': return 'primary';
      case 'openai': return 'secondary';
      case 'anthropic': return 'error';
      case 'google': return 'warning';
      case 'ollama': return 'success';
      default: return 'default';
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" gutterBottom>
          Dashboard de IA - CrewAI
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          Gerencie agentes, prompts, crews e configurações de LLM para automação com IA.
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
            {error}
          </Alert>
        )}

        {success && (
          <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
            {success}
          </Alert>
        )}

        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={loadData}
          sx={{ mb: 3 }}
        >
          Atualizar Dados
        </Button>

        {/* Estatísticas */}
        {stats && (
          <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <PeopleIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Agentes</Typography>
              </Box>
              <Typography variant="h4">{stats.agents}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {stats.agents} agentes no sistema ({statsMy?.agents || 0} criados por você)
                  </Typography>
            </CardContent>
          </Card>
        </Grid>
            <Grid item xs={12} sm={6} md={2.4}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <ChatIcon color="secondary" sx={{ mr: 1 }} />
                    <Typography variant="h6">Prompts</Typography>
                  </Box>
              <Typography variant="h4">{stats.prompts}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Prompts disponíveis ({statsMy?.prompts || 0} seus)
                  </Typography>
            </CardContent>
          </Card>
        </Grid>
            <Grid item xs={12} sm={6} md={2.4}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <GroupIcon color="action" sx={{ mr: 1 }} />
                    <Typography variant="h6">Crews</Typography>
                  </Box>
              <Typography variant="h4">{stats.crews}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Equipes cadastradas ({statsMy?.crews || 0} suas)
                  </Typography>
            </CardContent>
          </Card>
        </Grid>
            <Grid item xs={12} sm={6} md={2.4}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <StorageIcon color="success" sx={{ mr: 1 }} />
                    <Typography variant="h6">LLMs</Typography>
                  </Box>
              <Typography variant="h4">{stats.llm_configs}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Configurações de modelo ({statsMy?.llm_configs || 0} suas)
                  </Typography>
            </CardContent>
          </Card>
        </Grid>
            <Grid item xs={12} sm={6} md={2.4}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <HistoryIcon color="warning" sx={{ mr: 1 }} />
                    <Typography variant="h6">Execuções</Typography>
                  </Box>
              <Typography variant="h4">{stats.recent_executions}</Typography>
              <Typography variant="body2" color="text.secondary">
                Execuções nos últimos 7 dias
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    )}

    {/* Seção rápida para trocar LLM por agente */}
    <Grid container spacing={3} sx={{ mb: 4 }}>
      <Grid item xs={12}>
        <Paper elevation={3} sx={{ p: 3 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">Trocar LLM por agente</Typography>
            <Typography variant="body2" color="text.secondary">
              Use a lista para apontar cada agente para uma LLM específica
            </Typography>
          </Box>

          {agents.length === 0 ? (
            <Alert severity="info">Nenhum agente disponível para gerenciamento.</Alert>
          ) : (
            agents.map((agent) => (
              <Paper key={agent.id} variant="outlined" sx={{ p: 2, mb: 1 }}>
                <Grid container spacing={2} alignItems="center">
                  <Grid item xs={12} md={4}>
                    <Typography variant="subtitle1">{agent.nome}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      Papel: {agent.role} • LLM atual: {agent.llm_config?.nome || 'Usa padrão'}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <FormControl fullWidth size="small">
                      <InputLabel>LLM dedicada</InputLabel>
                      <Select
                        value={agentLLMSelection[agent.id] ?? ''}
                        label="LLM dedicada"
                        onChange={(e) => setAgentLLMSelection((prev) => ({
                          ...prev,
                          [agent.id]: e.target.value
                        }))}
                      >
                        <MenuItem value="">Usar padrão</MenuItem>
                        {llmConfigs.map((config) => (
                          <MenuItem key={config.id} value={config.id}>
                            {config.nome} ({config.provider}/{config.model})
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} md={4} sx={{ textAlign: { xs: 'left', md: 'right' } }}>
                    <Button
                      variant="contained"
                      color="primary"
                      onClick={() => handleAssignLLM(agent.id, agentLLMSelection[agent.id])}
                      disabled={agentUpdating === agent.id}
                      startIcon={agentUpdating === agent.id ? <CircularProgress size={18} /> : <SettingsIcon />}
                    >
                      {agentUpdating === agent.id ? 'Aplicando...' : 'Aplicar LLM'}
                    </Button>
                  </Grid>
                </Grid>
              </Paper>
            ))
          )}
        </Paper>
      </Grid>
    </Grid>

        {/* Status da IA */}
        {aiStatus && (
          <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
            <Typography variant="h6" gutterBottom>
              Status da IA
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    Provedores Disponíveis
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {aiStatus.available_providers.map((provider, index) => (
                      <Chip
                        key={index}
                        label={provider}
                        color={getProviderColor(provider)}
                        size="small"
                        variant="outlined"
                      />
                    ))}
                  </Box>
                </Box>
                <Box>
                  <Typography variant="subtitle1" gutterBottom>
                    Configuração Padrão
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Provedor: <strong>{aiStatus.default_provider}</strong>
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Modelo: <strong>{aiStatus.default_model}</strong>
                  </Typography>
                  <Divider sx={{ my: 1 }} />
                  <Typography variant="subtitle2" color="text.secondary">
                    LLM com visão (para imagens/áudio):
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Provedor visão: <strong>{aiStatus.default_vision_provider}</strong>
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Modelo visão: <strong>{aiStatus.default_vision_model}</strong>
                  </Typography>
                  <Alert severity="info" sx={{ mt: 1 }}>
                    Funções que exigem visão (OCR, uploads multimídia, áudio+imagem) usarão esta configuração.
                  </Alert>
                  <Divider sx={{ my: 1 }} />
                  <Typography variant="subtitle2" color="text.secondary">
                    LLM multimodal (texto+imagem+áudio):
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Provedor multimodal: <strong>{aiStatus.default_multimodal_provider}</strong>
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Modelo multimodal: <strong>{aiStatus.default_multimodal_model}</strong>
                  </Typography>
                  <Alert severity="success" sx={{ mt: 1 }}>
                    Use para cenários híbridos (ex.: combinar texto com visão e áudio).
                  </Alert>
                </Box>
              </Grid>
              <Grid item xs={12} md={6}>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    Teste de Conexão
                  </Typography>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={async () => {
                      try {
                        const response = await api.post('/ai-management/providers/test');
                        if (response.data.success) {
                          setSuccess('Conexão com IA testada com sucesso');
                        } else {
                          setError(`Erro no teste de conexão: ${response.data.error}`);
                        }
                      } catch (error) {
                        setError('Erro ao testar conexão com IA');
                      }
                    }}
                  >
                    Testar Conexão
                  </Button>
                </Box>
              </Grid>
            </Grid>
          </Paper>
        )}

        {/* Tabs */}
        <Paper elevation={2} sx={{ mb: 4 }}>
          <Tabs value={tabValue} onChange={handleTabChange} variant="scrollable" scrollButtons="auto">
            <Tab icon={<PeopleIcon />} label="Agentes" />
            <Tab icon={<ChatIcon />} label="Prompts" />
            <Tab icon={<GroupIcon />} label="Crews" />
            <Tab icon={<StorageIcon />} label="LLMs" />
            <Tab icon={<HistoryIcon />} label="Execuções" />
          </Tabs>
          
          <Box sx={{ p: 3 }}>
            {/* Tab: Agentes */}
            {tabValue === 0 && (
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
                  <Typography variant="h6">Agentes de IA</Typography>
                  <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => setOpenAgentDialog(true)}
                  >
                    Novo Agente
                  </Button>
                </Box>
                
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Nome</TableCell>
                        <TableCell>Role</TableCell>
                        <TableCell>LLM</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Criado em</TableCell>
                        <TableCell>Ações</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {agents.map((agent) => (
                        <TableRow key={agent.id}>
                          <TableCell>
                            <Typography variant="body2" fontWeight="medium">
                              {agent.nome}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {agent.descricao}
                            </Typography>
                          </TableCell>
                          <TableCell>{agent.role}</TableCell>
                          <TableCell>
                            {agent.llm_config ? (
                              <Chip
                                label={`${agent.llm_config.provider}/${agent.llm_config.model}`}
                                size="small"
                                variant="outlined"
                              />
                            ) : (
                              <Typography variant="caption" color="text.secondary">
                                Padrão
                              </Typography>
                            )}
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={agent.is_active ? 'Ativo' : 'Inativo'}
                              color={agent.is_active ? 'success' : 'default'}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>
                            {new Date(agent.created_at).toLocaleDateString()}
                          </TableCell>
                          <TableCell>
                            <Tooltip title="Executar">
                              <IconButton size="small" onClick={() => {
                                setExecutionForm({ ...executionForm, crew_id: '' });
                                setOpenExecutionDialog(true);
                              }}>
                                <PlayArrowIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Editar">
                              <IconButton size="small">
                                <EditIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Remover">
                              <IconButton size="small" color="error" onClick={() => handleDeleteAgent(agent.id)}>
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            )}
            
            {/* Tab: Prompts */}
            {tabValue === 1 && (
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
                  <Typography variant="h6">Prompts de IA</Typography>
                  <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => setOpenPromptDialog(true)}
                  >
                    Novo Prompt
                  </Button>
                </Box>
                
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Nome</TableCell>
                        <TableCell>Categoria</TableCell>
                        <TableCell>Agente</TableCell>
                        <TableCell>Versão</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Ações</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {prompts.map((prompt) => (
                        <TableRow key={prompt.id}>
                          <TableCell>
                            <Typography variant="body2" fontWeight="medium">
                              {prompt.nome}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {prompt.descricao}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={prompt.categoria || 'Geral'}
                              size="small"
                              variant="outlined"
                            />
                          </TableCell>
                          <TableCell>
                            {prompt.agent_nome || 'Todos'}
                          </TableCell>
                          <TableCell>{prompt.version}</TableCell>
                          <TableCell>
                            <Chip
                              label={prompt.is_active ? 'Ativo' : 'Inativo'}
                              color={prompt.is_active ? 'success' : 'default'}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>
                            <Tooltip title="Visualizar">
                              <IconButton size="small">
                                <CodeIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Editar">
                              <IconButton size="small">
                                <EditIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Remover">
                              <IconButton size="small" color="error" onClick={() => handleDeletePrompt(prompt.id)}>
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            )}
            
            {/* Tab: Crews */}
            {tabValue === 2 && (
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
                  <Typography variant="h6">Crews de IA</Typography>
                  <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => setOpenCrewDialog(true)}
                  >
                    Nova Crew
                  </Button>
                </Box>
                
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Nome</TableCell>
                        <TableCell>Processo</TableCell>
                        <TableCell>Agentes</TableCell>
                        <TableCell>Tarefas</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Ações</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {crews.map((crew) => (
                        <TableRow key={crew.id}>
                          <TableCell>
                            <Typography variant="body2" fontWeight="medium">
                              {crew.nome}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {crew.descricao}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={crew.process === 'sequential' ? 'Sequencial' : 'Hierárquico'}
                              size="small"
                              variant="outlined"
                            />
                          </TableCell>
                          <TableCell>
                            <Badge badgeContent={crew.agents.length} color="primary">
                              <PeopleIcon fontSize="small" />
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Badge badgeContent={crew.tasks_count} color="secondary">
                              <TaskIcon fontSize="small" />
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={crew.is_active ? 'Ativa' : 'Inativa'}
                              color={crew.is_active ? 'success' : 'default'}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>
                            <Tooltip title="Executar">
                              <IconButton size="small" onClick={() => {
                                setExecutionForm({ ...executionForm, crew_id: crew.id });
                                setOpenExecutionDialog(true);
                              }}>
                                <PlayArrowIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Editar">
                              <IconButton size="small">
                                <EditIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Remover">
                              <IconButton size="small" color="error" onClick={() => handleDeleteCrew(crew.id)}>
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            )}
            
            {/* Tab: LLMs */}
            {tabValue === 3 && (
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
                  <Typography variant="h6">Configurações de LLM</Typography>
                  <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => setOpenLLMDialog(true)}
                  >
                    Nova Configuração
                  </Button>
                </Box>
                
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Nome</TableCell>
                        <TableCell>Provedor</TableCell>
                        <TableCell>Modelo</TableCell>
                        <TableCell>Padrão</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Ações</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {llmConfigs.map((config) => (
                        <TableRow key={config.id}>
                          <TableCell>
                            <Typography variant="body2" fontWeight="medium">
                              {config.nome}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={config.provider}
                              color={getProviderColor(config.provider)}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>{config.model}</TableCell>
                          <TableCell>
                            {config.is_default ? (
                              <CheckCircleIcon color="success" fontSize="small" />
                            ) : null}
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={config.is_active ? 'Ativa' : 'Inativa'}
                              color={config.is_active ? 'success' : 'default'}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>
                            <Tooltip title="Editar">
                              <IconButton size="small">
                                <EditIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Remover">
                              <IconButton size="small" color="error" onClick={() => handleDeleteLLMConfig(config.id)}>
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            )}
            
            {/* Tab: Execuções */}
            {tabValue === 4 && (
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
                  <Typography variant="h6">Logs de Execução</Typography>
                </Box>
                
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Data/Hora</TableCell>
                        <TableCell>Tipo</TableCell>
                        <TableCell>Recurso</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Tempo</TableCell>
                        <TableCell>Tokens</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {executionLogs.slice(0, 10).map((log) => (
                        <TableRow key={log.id}>
                          <TableCell>
                            {new Date(log.created_at).toLocaleString()}
                          </TableCell>
                          <TableCell>
                            {log.crew_id ? 'Crew' : log.agent_id ? 'Agente' : 'Sistema'}
                          </TableCell>
                          <TableCell>
                            {log.crew_nome || log.agent_nome || 'Teste'}
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={log.status}
                              color={getStatusColor(log.status)}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>
                            {log.execution_time_ms}ms
                          </TableCell>
                          <TableCell>
                            {log.tokens_used || 'N/A'}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            )}
          </Box>
        </Paper>
      </Box>

      {/* Diálogo para criar agente */}
      <Dialog open={openAgentDialog} onClose={() => setOpenAgentDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Criar Novo Agente</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                label="Nome do Agente"
                value={agentForm.nome}
                onChange={(e) => setAgentForm({ ...agentForm, nome: e.target.value })}
                fullWidth
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Descrição"
                value={agentForm.descricao}
                onChange={(e) => setAgentForm({ ...agentForm, descricao: e.target.value })}
                fullWidth
                multiline
                rows={2}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Role (Papel)"
                value={agentForm.role}
                onChange={(e) => setAgentForm({ ...agentForm, role: e.target.value })}
                fullWidth
                required
                placeholder="Ex: Analista Médico, Especialista em Dados"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Goal (Objetivo)"
                value={agentForm.goal}
                onChange={(e) => setAgentForm({ ...agentForm, goal: e.target.value })}
                fullWidth
                required
                multiline
                rows={2}
                placeholder="Ex: Analisar dados médicos e fornecer insights"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Backstory (Histórico)"
                value={agentForm.backstory}
                onChange={(e) => setAgentForm({ ...agentForm, backstory: e.target.value })}
                fullWidth
                multiline
                rows={3}
                placeholder="Ex: Especialista em medicina com 10 anos de experiência..."
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                select
                label="Configuração de LLM"
                value={agentForm.llm_config_id}
                onChange={(e) => setAgentForm({ ...agentForm, llm_config_id: e.target.value })}
                fullWidth
              >
                <MenuItem value="">Usar padrão do sistema</MenuItem>
                {llmConfigs.map((config) => (
                  <MenuItem key={config.id} value={config.id}>
                    {config.nome} ({config.provider}/{config.model})
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Temperatura"
                type="number"
                value={agentForm.temperature}
                onChange={(e) => setAgentForm({ ...agentForm, temperature: parseFloat(e.target.value) })}
                fullWidth
                inputProps={{ min: 0, max: 2, step: 0.1 }}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={agentForm.is_active}
                    onChange={(e) => setAgentForm({ ...agentForm, is_active: e.target.checked })}
                  />
                }
                label="Ativo"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenAgentDialog(false)}>Cancelar</Button>
          <Button onClick={handleCreateAgent} variant="contained" color="primary">
            Criar Agente
          </Button>
        </DialogActions>
      </Dialog>

      {/* Diálogo para criar prompt */}
      <Dialog open={openPromptDialog} onClose={() => setOpenPromptDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Criar Novo Prompt</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                label="Nome do Prompt"
                value={promptForm.nome}
                onChange={(e) => setPromptForm({ ...promptForm, nome: e.target.value })}
                fullWidth
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Descrição"
                value={promptForm.descricao}
                onChange={(e) => setPromptForm({ ...promptForm, descricao: e.target.value })}
                fullWidth
                multiline
                rows={2}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Template"
                value={promptForm.template}
                onChange={(e) => setPromptForm({ ...promptForm, template: e.target.value })}
                fullWidth
                required
                multiline
                rows={6}
                placeholder="Ex: Analise os seguintes dados: {dados_paciente}"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Categoria"
                value={promptForm.categoria}
                onChange={(e) => setPromptForm({ ...promptForm, categoria: e.target.value })}
                fullWidth
                placeholder="Ex: medical, analysis, report"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                select
                label="Agente Associado"
                value={promptForm.agent_id}
                onChange={(e) => setPromptForm({ ...promptForm, agent_id: e.target.value })}
                fullWidth
              >
                <MenuItem value="">Nenhum (Geral)</MenuItem>
                {agents.map((agent) => (
                  <MenuItem key={agent.id} value={agent.id}>
                    {agent.nome}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={promptForm.is_system_prompt}
                    onChange={(e) => setPromptForm({ ...promptForm, is_system_prompt: e.target.checked })}
                  />
                }
                label="Prompt de Sistema"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={promptForm.is_active}
                    onChange={(e) => setPromptForm({ ...promptForm, is_active: e.target.checked })}
                  />
                }
                label="Ativo"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenPromptDialog(false)}>Cancelar</Button>
          <Button onClick={handleCreatePrompt} variant="contained" color="primary">
            Criar Prompt
          </Button>
        </DialogActions>
      </Dialog>

      {/* Diálogo para criar crew */}
      <Dialog open={openCrewDialog} onClose={() => setOpenCrewDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Criar Nova Crew</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                label="Nome da Crew"
                value={crewForm.nome}
                onChange={(e) => setCrewForm({ ...crewForm, nome: e.target.value })}
                fullWidth
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Descrição"
                value={crewForm.descricao}
                onChange={(e) => setCrewForm({ ...crewForm, descricao: e.target.value })}
                fullWidth
                multiline
                rows={2}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                select
                label="Processo"
                value={crewForm.process}
                onChange={(e) => setCrewForm({ ...crewForm, process: e.target.value })}
                fullWidth
              >
                <MenuItem value="sequential">Sequencial</MenuItem>
                <MenuItem value="hierarchical">Hierárquico</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Máximo de Iterações"
                type="number"
                value={crewForm.max_iter}
                onChange={(e) => setCrewForm({ ...crewForm, max_iter: parseInt(e.target.value) })}
                fullWidth
                inputProps={{ min: 1, max: 10 }}
              />
            </Grid>
            <Grid item xs={12}>
              <Typography variant="subtitle2" gutterBottom>
                Agentes da Crew
              </Typography>
              <List dense>
                {agents.map((agent) => (
                  <ListItem key={agent.id}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={crewForm.agent_ids.includes(agent.id)}
                          onChange={(e) => {
                            const newAgentIds = e.target.checked
                              ? [...crewForm.agent_ids, agent.id]
                              : crewForm.agent_ids.filter(id => id !== agent.id);
                            setCrewForm({ ...crewForm, agent_ids: newAgentIds });
                          }}
                        />
                      }
                      label={
                        <Box>
                          <Typography variant="body2">{agent.nome}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {agent.role}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={crewForm.is_active}
                    onChange={(e) => setCrewForm({ ...crewForm, is_active: e.target.checked })}
                  />
                }
                label="Ativa"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCrewDialog(false)}>Cancelar</Button>
          <Button onClick={handleCreateCrew} variant="contained" color="primary">
            Criar Crew
          </Button>
        </DialogActions>
      </Dialog>

      {/* Diálogo para criar configuração de LLM */}
      <Dialog open={openLLMDialog} onClose={() => setOpenLLMDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Criar Nova Configuração de LLM</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                label="Nome da Configuração"
                value={llmForm.nome}
                onChange={(e) => setLlmForm({ ...llmForm, nome: e.target.value })}
                fullWidth
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                select
                label="Provedor"
                value={llmForm.provider}
                onChange={(e) => setLlmForm({ ...llmForm, provider: e.target.value })}
                fullWidth
                required
              >
                {availableProviders.map((provider) => (
                  <MenuItem key={provider.name} value={provider.name}>
                    {provider.name}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                select
                label="Modelo"
                value={llmForm.model}
                onChange={(e) => setLlmForm({ ...llmForm, model: e.target.value })}
                fullWidth
                required
              >
                {availableProviders
                  .find(p => p.name === llmForm.provider)
                  ?.models.map((model) => (
                    <MenuItem key={model} value={model}>
                      {model}
                    </MenuItem>
                  ))}
              </TextField>
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Variável de Ambiente da API Key"
                value={llmForm.api_key_env_var}
                onChange={(e) => setLlmForm({ ...llmForm, api_key_env_var: e.target.value })}
                fullWidth
                placeholder="Ex: GROQ_API_KEY"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="URL Base (opcional)"
                value={llmForm.base_url}
                onChange={(e) => setLlmForm({ ...llmForm, base_url: e.target.value })}
                fullWidth
                placeholder="Ex: https://api.groq.com/v1"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Temperatura"
                type="number"
                value={llmForm.temperature}
                onChange={(e) => setLlmForm({ ...llmForm, temperature: parseFloat(e.target.value) })}
                fullWidth
                inputProps={{ min: 0, max: 2, step: 0.1 }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Máximo de Tokens"
                type="number"
                value={llmForm.max_tokens}
                onChange={(e) => setLlmForm({ ...llmForm, max_tokens: parseInt(e.target.value) })}
                fullWidth
                inputProps={{ min: 1, max: 10000 }}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={llmForm.is_default}
                    onChange={(e) => setLlmForm({ ...llmForm, is_default: e.target.checked })}
                  />
                }
                label="Configuração Padrão"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={llmForm.is_active}
                    onChange={(e) => setLlmForm({ ...llmForm, is_active: e.target.checked })}
                  />
                }
                label="Ativa"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenLLMDialog(false)}>Cancelar</Button>
          <Button onClick={handleCreateLLMConfig} variant="contained" color="primary">
            Criar Configuração
          </Button>
        </DialogActions>
      </Dialog>

      {/* Diálogo para executar crew */}
      <Dialog open={openExecutionDialog} onClose={() => setOpenExecutionDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Executar Crew</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                label="Dados de Entrada (JSON)"
                value={JSON.stringify(executionForm.input_data, null, 2)}
                onChange={(e) => {
                  try {
                    const inputData = JSON.parse(e.target.value);
                    setExecutionForm({ ...executionForm, input_data: inputData });
                  } catch (error) {
                    // Ignora erros de parsing
                  }
                }}
                fullWidth
                multiline
                rows={6}
                placeholder='{"dados": "exemplo"}'
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Prompt Personalizado (opcional)"
                value={executionForm.prompt}
                onChange={(e) => setExecutionForm({ ...executionForm, prompt: e.target.value })}
                fullWidth
                multiline
                rows={3}
                placeholder="Instruções específicas para esta execução..."
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenExecutionDialog(false)}>Cancelar</Button>
          <Button onClick={() => handleExecuteCrew(executionForm.crew_id)} variant="contained" color="primary">
            Executar
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}

export default AIDashboard;
