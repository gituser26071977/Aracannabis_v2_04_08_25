import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Button,
  Alert,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  FormControlLabel,
  Switch,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
  Stack
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Psychology as PsychologyIcon,
  Speed as SpeedIcon,
  Security as SecurityIcon,
  Cloud as CloudIcon,
  Computer as ComputerIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Settings as SettingsIcon,
  Add as AddIcon,
  Edit as EditIcon
} from '@mui/icons-material';
import { aiConfigService, aiManagementService } from '../services/api';

function AIConfigPage() {
  const [providers, setProviders] = useState({});
  const [currentConfig, setCurrentConfig] = useState({});
  const [selectedProvider, setSelectedProvider] = useState('');
  const [selectedModel, setSelectedModel] = useState('');
  const [customModel, setCustomModel] = useState('');
  const [useCustomModel, setUseCustomModel] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [baseUrl, setBaseUrl] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('info');
  const [testResult, setTestResult] = useState(null);
  const [agents, setAgents] = useState([]);
  const [llmConfigs, setLLMConfigs] = useState([]);
  const [agentDialogOpen, setAgentDialogOpen] = useState(false);
  const [agentForm, setAgentForm] = useState({
    nome: '',
    role: '',
    goal: '',
    backstory: '',
    llm_config_id: ''
  });
  const [editingAgent, setEditingAgent] = useState(null);
  const [agentSaving, setAgentSaving] = useState(false);

  // Estados para Visão e Multimodal (OCR)
  const [visionProvider, setVisionProvider] = useState('');
  const [visionModel, setVisionModel] = useState('');
  const [visionApiKey, setVisionApiKey] = useState('');
  const [visionBaseUrl, setVisionBaseUrl] = useState('');
  const [visionUseCustomModel, setVisionUseCustomModel] = useState(false);
  const [multimodalProvider, setMultimodalProvider] = useState('');
  const [multimodalModel, setMultimodalModel] = useState('');
  const [multimodalApiKey, setMultimodalApiKey] = useState('');
  const [multimodalBaseUrl, setMultimodalBaseUrl] = useState('');
  const [multimodalUseCustomModel, setMultimodalUseCustomModel] = useState(false);
  const [savingVision, setSavingVision] = useState(false);
  const [savingMultimodal, setSavingMultimodal] = useState(false);
  const [testingVision, setTestingVision] = useState(false);
  const [testResultVision, setTestResultVision] = useState(null);
  const [testingMultimodal, setTestingMultimodal] = useState(false);
  const [testResultMultimodal, setTestResultMultimodal] = useState(null);

  useEffect(() => {
    loadProviders();
    loadAgentManagement();
  }, []);

  const loadProviders = async () => {
    try {
      setLoading(true);
      const data = await aiConfigService.obterProvedores();
      setProviders(data.providers || {});

      // Garantir que current_config existe com valores padrão
      const config = data.current_config || {
        provider: 'groq',
        model: '',
        base_url: '',
        has_openai_key: false,
        has_anthropic_key: false,
        has_google_key: false,
        has_groq_key: false,
        has_xai_key: false,
        has_xai_key: false,
        has_deepseek_key: false,
        has_zhipu_key: false
      };
      setCurrentConfig(config);

      // Definir valores atuais com fallback seguro
      setSelectedProvider(config.provider || 'groq');
      setSelectedModel(config.model || '');
      setBaseUrl(config.base_url || '');

      // Configurações de Visão e Multimodal
      setVisionProvider(data.default_vision_provider || '');
      setVisionModel(data.default_vision_model || '');
      setMultimodalProvider(data.default_multimodal_provider || '');
      setMultimodalModel(data.default_multimodal_model || '');

      // Verificar se o modelo atual é customizado
      if (config.provider && data.providers && data.providers[config.provider]) {
        const providerModels = data.providers[config.provider].models || [];
        const isCustom = config.model && !providerModels.includes(config.model);
        if (isCustom) {
          setUseCustomModel(true);
          setCustomModel(config.model);
        }
      }

    } catch (error) {
      setMessage(`Erro ao carregar provedores: ${error.error || error.message}`);
      setMessageType('error');
    } finally {
      setLoading(false);
    }
  };

  const loadAgentManagement = async () => {
    try {
      const [agentData, llmData] = await Promise.all([
        aiManagementService.getAgents(),
        aiManagementService.getLLMConfigs()
      ]);
      setAgents(agentData.agents || []);
      setLLMConfigs(llmData.llm_configs || []);
    } catch (error) {
      setMessage(`Erro ao carregar agentes/LLMs: ${error.error || error.message}`);
      setMessageType('error');
    }
  };

  const handleProviderChange = (event) => {
    const provider = event.target.value;
    setSelectedProvider(provider);

    if (providers[provider]) {
      setSelectedModel(providers[provider].default_model);
      setBaseUrl(providers[provider].base_url);
    }

    setApiKey('');
    setTestResult(null);
    setUseCustomModel(false);
    setCustomModel('');
  };

  const handleModelChange = (event) => {
    setSelectedModel(event.target.value);
    setUseCustomModel(false);
    setCustomModel('');
  };

  const handleCustomModelToggle = (event) => {
    const isCustom = event.target.checked;
    setUseCustomModel(isCustom);

    if (isCustom) {
      setSelectedModel('');
    } else {
      setCustomModel('');
      if (providers[selectedProvider]) {
        setSelectedModel(providers[selectedProvider].default_model);
      }
    }
  };

  const openAgentDialog = (agent) => {
    setEditingAgent(agent);
    setAgentForm({
      nome: agent.nome,
      role: agent.role,
      goal: agent.goal,
      backstory: agent.backstory || '',
      llm_config_id: agent.llm_config_id ?? ''
    });
    setAgentDialogOpen(true);
  };

  const handleAgentFormChange = (field, value) => {
    setAgentForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleAgentSave = async () => {
    if (!editingAgent) return;
    setAgentSaving(true);
    try {
      const payload = {
        nome: agentForm.nome,
        role: agentForm.role,
        goal: agentForm.goal,
        backstory: agentForm.backstory,
        llm_config_id: agentForm.llm_config_id || null
      };
      await aiManagementService.updateAgent(editingAgent.id, payload);
      setMessage('Agente atualizado com sucesso');
      setMessageType('success');
      await loadAgentManagement();
      setAgentDialogOpen(false);
    } catch (error) {
      setMessage(`Erro ao atualizar agente: ${error.error || error.message}`);
      setMessageType('error');
    } finally {
      setAgentSaving(false);
    }
  };

  const handleSaveVision = async () => {
    setSavingVision(true);
    try {
      const payload = {
        provider: visionProvider,
        model: visionModel  // Sempre usar o valor atual de visionModel
      };

      // Adicionar API key se fornecida
      if (visionApiKey) {
        payload.api_key = visionApiKey;
      }

      // Adicionar base_url se fornecida
      if (visionBaseUrl) {
        payload.base_url = visionBaseUrl;
      }

      await aiConfigService.atualizarConfiguracaoVision(payload);
      setMessage('Configuração de Visão salva com sucesso!');
      setMessageType('success');
      // Limpar API key após salvar (segurança)
      setVisionApiKey('');
      loadProviders();
    } catch (error) {
      setMessage(`Erro ao salvar visão: ${error.error || error.message}`);
      setMessageType('error');
    } finally {
      setSavingVision(false);
    }
  };

  const handleSaveMultimodal = async () => {
    setSavingMultimodal(true);
    try {
      const payload = {
        provider: multimodalProvider,
        model: multimodalModel  // Sempre usar o valor atual de multimodalModel
      };

      // Adicionar API key se fornecida
      if (multimodalApiKey) {
        payload.api_key = multimodalApiKey;
      }

      // Adicionar base_url se fornecida
      if (multimodalBaseUrl) {
        payload.base_url = multimodalBaseUrl;
      }

      await aiConfigService.atualizarConfiguracaoMultimodal(payload);
      setMessage('Configuração Multimodal (OCR) salva com sucesso!');
      setMessageType('success');
      // Limpar API key após salvar (segurança)
      setMultimodalApiKey('');
      loadProviders();
    } catch (error) {
      setMessage(`Erro ao salvar multimodal: ${error.error || error.message}`);
      setMessageType('error');
    } finally {
      setSavingMultimodal(false);
    }
  };

  const getEffectiveModel = () => {
    return useCustomModel ? customModel : selectedModel;
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setMessage('');

      const effectiveModel = getEffectiveModel();

      if (!effectiveModel) {
        setMessage('Por favor, selecione ou digite um modelo');
        setMessageType('error');
        return;
      }

      const config = {
        provider: selectedProvider,
        model: effectiveModel,
        api_key: apiKey,
        base_url: baseUrl
      };

      const result = await aiConfigService.atualizarConfiguracao(config);
      setMessage(result.message);
      setMessageType('success');

      // Recarregar configuração atual
      await loadProviders();

    } catch (error) {
      setMessage(`Erro ao salvar configuração: ${error.error || error.message}`);
      setMessageType('error');
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    try {
      setTesting(true);
      setTestResult(null);

      const effectiveModel = getEffectiveModel();

      if (!effectiveModel) {
        setTestResult({
          success: false,
          error: 'Por favor, selecione ou digite um modelo para testar'
        });
        return;
      }

      const config = {
        provider: selectedProvider,
        model: effectiveModel,
        api_key: apiKey,
        base_url: baseUrl
      };

      const result = await aiConfigService.testarConfiguracao(config);
      setTestResult(result);

    } catch (error) {
      setTestResult({
        success: false,
        error: error.error || error.message
      });
    } finally {
      setTesting(false);
    }
  };

  const handleTestVision = async () => {
    try {
      setTestingVision(true);
      setTestResultVision(null);

      if (!visionModel) {
        setTestResultVision({
          success: false,
          error: 'Por favor, selecione ou digite um modelo para testar'
        });
        return;
      }

      const config = {
        provider: visionProvider,
        model: visionModel,
        api_key: visionApiKey,
        base_url: visionBaseUrl
      };

      const result = await aiConfigService.testarConfiguracao(config);
      setTestResultVision(result);

    } catch (error) {
      setTestResultVision({
        success: false,
        error: error.error || error.message
      });
    } finally {
      setTestingVision(false);
    }
  };

  const handleTestMultimodal = async () => {
    try {
      setTestingMultimodal(true);
      setTestResultMultimodal(null);

      if (!multimodalModel) {
        setTestResultMultimodal({
          success: false,
          error: 'Por favor, selecione ou digite um modelo para testar'
        });
        return;
      }

      const config = {
        provider: multimodalProvider,
        model: multimodalModel,
        api_key: multimodalApiKey,
        base_url: multimodalBaseUrl
      };

      const result = await aiConfigService.testarConfiguracao(config);
      setTestResultMultimodal(result);

    } catch (error) {
      setTestResultMultimodal({
        success: false,
        error: error.error || error.message
      });
    } finally {
      setTestingMultimodal(false);
    }
  };

  const getProviderIcon = (provider) => {
    switch (provider) {
      case 'openai':
        return <PsychologyIcon />;
      case 'anthropic':
        return <PsychologyIcon />;
      case 'google':
        return <CloudIcon />;
      case 'groq':
        return <SpeedIcon />;
      case 'xai':
        return <PsychologyIcon />;
      case 'ollama':
        return <ComputerIcon />;
      case 'zhipu':
        return <PsychologyIcon />;
      default:
        return <SettingsIcon />;
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        🤖 Configuração de IA
      </Typography>

      <Typography variant="body1" color="text.secondary" paragraph>
        Configure os provedores de IA para análise de evoluções, chat inteligente e processamento de documentos.
      </Typography>

      {message && (
        <Alert severity={messageType} sx={{ mb: 3 }}>
          {message}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Configuração Principal */}
        <Grid item xs={12} md={8}>
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Configuração Principal
            </Typography>

            <Grid container spacing={3}>
              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Provedor de IA</InputLabel>
                  <Select
                    value={selectedProvider}
                    onChange={handleProviderChange}
                    label="Provedor de IA"
                  >
                    {Object.entries(providers).map(([key, provider]) => (
                      <MenuItem key={key} value={key}>
                        <Box display="flex" alignItems="center" gap={1}>
                          {getProviderIcon(key)}
                          <Typography>{provider.name}</Typography>
                          <Chip
                            size="small"
                            label={provider.requires_api_key ? 'API Key' : 'Local'}
                            color={provider.requires_api_key ? 'primary' : 'success'}
                          />
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              {selectedProvider && providers[selectedProvider] && (
                <>
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={useCustomModel}
                          onChange={handleCustomModelToggle}
                          color="primary"
                        />
                      }
                      label={
                        <Box display="flex" alignItems="center" gap={1}>
                          <AddIcon fontSize="small" />
                          <Typography>Usar modelo customizado</Typography>
                        </Box>
                      }
                    />
                  </Grid>

                  {useCustomModel ? (
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="Modelo Customizado"
                        value={customModel}
                        onChange={(e) => setCustomModel(e.target.value)}
                        placeholder="Digite o nome do modelo (ex: llama-3.2-90b-text-preview)"
                        helperText="Digite o nome exato do modelo conforme a documentação do provedor"
                      />
                    </Grid>
                  ) : (
                    <Grid item xs={12}>
                      <FormControl fullWidth>
                        <InputLabel>Modelo</InputLabel>
                        <Select
                          value={selectedModel}
                          onChange={handleModelChange}
                          label="Modelo"
                        >
                          {providers[selectedProvider].models.map((model) => (
                            <MenuItem key={model} value={model}>
                              {model}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                  )}

                  {providers[selectedProvider].requires_api_key && (
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="API Key"
                        type="password"
                        value={apiKey}
                        onChange={(e) => setApiKey(e.target.value)}
                        placeholder="Insira sua API key..."
                        helperText="Sua API key será armazenada de forma segura"
                      />
                    </Grid>
                  )}

                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Base URL"
                      value={baseUrl}
                      onChange={(e) => setBaseUrl(e.target.value)}
                      placeholder="URL base da API..."
                      helperText="URL personalizada (opcional)"
                    />
                  </Grid>
                </>
              )}

              <Grid item xs={12}>
                <Box display="flex" gap={2}>
                  <Button
                    variant="contained"
                    onClick={handleSave}
                    disabled={saving || !selectedProvider || !getEffectiveModel()}
                    startIcon={saving ? <CircularProgress size={20} /> : <SettingsIcon />}
                  >
                    {saving ? 'Salvando...' : 'Salvar Configuração'}
                  </Button>

                  <Button
                    variant="outlined"
                    onClick={handleTest}
                    disabled={testing || !selectedProvider || !getEffectiveModel()}
                    startIcon={testing ? <CircularProgress size={20} /> : <SpeedIcon />}
                  >
                    {testing ? 'Testando...' : 'Testar Conexão'}
                  </Button>
                </Box>
              </Grid>

              {testResult && (
                <Grid item xs={12}>
                  <Alert
                    severity={testResult.success ? 'success' : 'error'}
                    icon={testResult.success ? <CheckCircleIcon /> : <ErrorIcon />}
                  >
                    <Typography variant="subtitle2">
                      {testResult.success ? 'Teste bem-sucedido!' : 'Teste falhou'}
                    </Typography>
                    <Typography variant="body2">
                      {testResult.message || testResult.error}
                    </Typography>
                    {testResult.response && (
                      <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                        Resposta: {testResult.response}
                      </Typography>
                    )}
                  </Alert>
                </Grid>
              )}
            </Grid>
          </Paper>
        </Grid>

        {/* Configurações de Visão e OCR */}
        <Grid item xs={12} md={8}>
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Configuração de Visão e OCR
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Configure os modelos responsáveis por analisar fotos de documentos e extrair dados automaticamente.
            </Typography>

            <Grid container spacing={3}>
              {/* Visão Padrão */}
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>Visão (Análise Geral)</Typography>
                <FormControl fullWidth size="small" sx={{ mb: 1 }}>
                  <InputLabel>Provedor</InputLabel>
                  <Select
                    value={visionProvider}
                    onChange={(e) => {
                      setVisionProvider(e.target.value);
                      // Só atualizar o modelo automaticamente se NÃO estiver usando modelo customizado
                      if (!visionUseCustomModel && providers[e.target.value]) {
                        setVisionModel(providers[e.target.value].default_model);
                      }
                    }}
                    label="Provedor"
                  >
                    {['openai', 'google', 'ollama_local', 'zhipu'].map(p => (
                      <MenuItem key={p} value={p}>{providers[p]?.name || p}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
                {visionProvider && (
                  <>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={visionUseCustomModel}
                          onChange={(e) => setVisionUseCustomModel(e.target.checked)}
                        />
                      }
                      label={
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography>Usar modelo customizado</Typography>
                        </Box>
                      }
                      sx={{ mb: 1 }}
                    />
                    {visionUseCustomModel ? (
                      <TextField
                        fullWidth
                        size="small"
                        label="Modelo Customizado"
                        value={visionModel}
                        onChange={(e) => setVisionModel(e.target.value)}
                        placeholder="Digite o nome do modelo (ex: gpt-4-vision-preview)"
                        helperText="Digite o nome exato do modelo conforme a documentação do provedor"
                        sx={{ mb: 1 }}
                      />
                    ) : (
                      <FormControl fullWidth size="small" sx={{ mb: 1 }}>
                        <InputLabel>Modelo</InputLabel>
                        <Select
                          value={visionModel}
                          onChange={(e) => setVisionModel(e.target.value)}
                          label="Modelo"
                        >
                          {providers[visionProvider]?.models?.map(m => (
                            <MenuItem key={m} value={m}>{m}</MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    )}
                    <TextField
                      fullWidth
                      size="small"
                      label="API Key (opcional)"
                      type="password"
                      value={visionApiKey}
                      onChange={(e) => setVisionApiKey(e.target.value)}
                      placeholder="Deixe em branco para usar a chave salva"
                      sx={{ mb: 1 }}
                    />
                    <TextField
                      fullWidth
                      size="small"
                      label="Base URL (opcional)"
                      value={visionBaseUrl}
                      onChange={(e) => setVisionBaseUrl(e.target.value)}
                      placeholder="URL personalizada"
                      sx={{ mb: 1 }}
                    />
                  </>
                )}
                <Button
                  size="small"
                  variant="contained"
                  onClick={handleSaveVision}
                  disabled={savingVision || !visionProvider}
                >
                  {savingVision ? <CircularProgress size={20} /> : 'Salvar Visão'}
                </Button>
                <Button
                  size="small"
                  variant="outlined"
                  onClick={handleTestVision}
                  disabled={testingVision || !visionProvider}
                  startIcon={testingVision ? <CircularProgress size={20} /> : <SpeedIcon />}
                  sx={{ ml: 1 }}
                >
                  {testingVision ? 'Testando...' : 'Testar Conexão'}
                </Button>

                {testResultVision && (
                  <Box sx={{ mt: 2 }}>
                    <Alert
                      severity={testResultVision.success ? 'success' : 'error'}
                      icon={testResultVision.success ? <CheckCircleIcon /> : <ErrorIcon />}
                    >
                      <Typography variant="subtitle2">
                        {testResultVision.success ? 'Teste bem-sucedido!' : 'Teste falhou'}
                      </Typography>
                      <Typography variant="body2">
                        {testResultVision.message || testResultVision.error}
                      </Typography>
                    </Alert>
                  </Box>
                )}
              </Grid>

              {/* Multimodal / OCR */}
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>Multimodal (OCR / Extração Complexa)</Typography>
                <FormControl fullWidth size="small" sx={{ mb: 1 }}>
                  <InputLabel>Provedor</InputLabel>
                  <Select
                    value={multimodalProvider}
                    onChange={(e) => {
                      setMultimodalProvider(e.target.value);
                      // Só atualizar o modelo automaticamente se NÃO estiver usando modelo customizado
                      if (!multimodalUseCustomModel && providers[e.target.value]) {
                        setMultimodalModel(providers[e.target.value].default_model);
                      }
                    }}
                    label="Provedor"
                  >
                    {['openai', 'google', 'ollama_local', 'zhipu'].map(p => (
                      <MenuItem key={p} value={p}>{providers[p]?.name || p}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
                {multimodalProvider && (
                  <>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={multimodalUseCustomModel}
                          onChange={(e) => setMultimodalUseCustomModel(e.target.checked)}
                        />
                      }
                      label={
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography>Usar modelo customizado</Typography>
                        </Box>
                      }
                      sx={{ mb: 1 }}
                    />
                    {multimodalUseCustomModel ? (
                      <TextField
                        fullWidth
                        size="small"
                        label="Modelo Customizado"
                        value={multimodalModel}
                        onChange={(e) => setMultimodalModel(e.target.value)}
                        placeholder="Digite o nome do modelo (ex: gpt-4o)"
                        helperText="Digite o nome exato do modelo conforme a documentação do provedor"
                        sx={{ mb: 1 }}
                      />
                    ) : (
                      <FormControl fullWidth size="small" sx={{ mb: 1 }}>
                        <InputLabel>Modelo</InputLabel>
                        <Select
                          value={multimodalModel}
                          onChange={(e) => setMultimodalModel(e.target.value)}
                          label="Modelo"
                        >
                          {providers[multimodalProvider]?.models?.map(m => (
                            <MenuItem key={m} value={m}>{m}</MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    )}
                    <TextField
                      fullWidth
                      size="small"
                      label="API Key (opcional)"
                      type="password"
                      value={multimodalApiKey}
                      onChange={(e) => setMultimodalApiKey(e.target.value)}
                      placeholder="Deixe em branco para usar a chave salva"
                      sx={{ mb: 1 }}
                    />
                    <TextField
                      fullWidth
                      size="small"
                      label="Base URL (opcional)"
                      value={multimodalBaseUrl}
                      onChange={(e) => setMultimodalBaseUrl(e.target.value)}
                      placeholder="URL personalizada"
                      sx={{ mb: 1 }}
                    />
                  </>
                )}
                <Button
                  size="small"
                  variant="contained"
                  onClick={handleSaveMultimodal}
                  disabled={savingMultimodal || !multimodalProvider}
                >
                  {savingMultimodal ? <CircularProgress size={20} /> : 'Salvar Multimodal'}
                </Button>
                <Button
                  size="small"
                  variant="outlined"
                  onClick={handleTestMultimodal}
                  disabled={testingMultimodal || !multimodalProvider}
                  startIcon={testingMultimodal ? <CircularProgress size={20} /> : <SpeedIcon />}
                  sx={{ ml: 1 }}
                >
                  {testingMultimodal ? 'Testando...' : 'Testar Conexão'}
                </Button>

                {testResultMultimodal && (
                  <Box sx={{ mt: 2 }}>
                    <Alert
                      severity={testResultMultimodal.success ? 'success' : 'error'}
                      icon={testResultMultimodal.success ? <CheckCircleIcon /> : <ErrorIcon />}
                    >
                      <Typography variant="subtitle2">
                        {testResultMultimodal.success ? 'Teste bem-sucedido!' : 'Teste falhou'}
                      </Typography>
                      <Typography variant="body2">
                        {testResultMultimodal.message || testResultMultimodal.error}
                      </Typography>
                    </Alert>
                  </Box>
                )}
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        {/* Status Atual */}
        <Grid item xs={12} md={4}>
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Status Atual
            </Typography>

            <List>
              <ListItem>
                <ListItemIcon>
                  {currentConfig?.provider ? getProviderIcon(currentConfig.provider) : <SettingsIcon />}
                </ListItemIcon>
                <ListItemText
                  primary="Provedor Ativo"
                  secondary={currentConfig?.provider ? (providers[currentConfig.provider]?.name || currentConfig.provider) : 'Nenhum configurado'}
                />
              </ListItem>

              <ListItem>
                <ListItemIcon>
                  <SettingsIcon />
                </ListItemIcon>
                <ListItemText
                  primary="Modelo"
                  secondaryTypographyProps={{ component: 'div' }}
                  secondary={
                    <Box component="div">
                      <Typography variant="body2" component="p">{currentConfig?.model || 'Não configurado'}</Typography>
                      {currentConfig?.provider && providers[currentConfig?.provider] &&
                        currentConfig?.model &&
                        !providers[currentConfig.provider].models?.includes(currentConfig.model) && (
                          <Chip size="small" label="Customizado" color="secondary" sx={{ mt: 0.5 }} />
                        )}
                    </Box>
                  }
                />
              </ListItem>

              <ListItem>
                <ListItemIcon>
                  <SecurityIcon />
                </ListItemIcon>
                <ListItemText
                  primary="API Keys Configuradas"
                  secondaryTypographyProps={{ component: 'div' }}
                  secondary={
                    <Box component="div">
                      {currentConfig?.has_openai_key && <Chip size="small" label="OpenAI" sx={{ mr: 0.5, mb: 0.5 }} />}
                      {currentConfig?.has_anthropic_key && <Chip size="small" label="Anthropic" sx={{ mr: 0.5, mb: 0.5 }} />}
                      {currentConfig?.has_google_key && <Chip size="small" label="Google" sx={{ mr: 0.5, mb: 0.5 }} />}
                      {currentConfig?.has_groq_key && <Chip size="small" label="Groq" sx={{ mr: 0.5, mb: 0.5 }} />}
                      {currentConfig?.has_xai_key && <Chip size="small" label="xAI" sx={{ mr: 0.5, mb: 0.5 }} />}
                      {currentConfig?.has_deepseek_key && <Chip size="small" label="DeepSeek" sx={{ mr: 0.5, mb: 0.5 }} />}
                      {currentConfig?.has_zhipu_key && <Chip size="small" label="Zhipu AI" sx={{ mr: 0.5, mb: 0.5 }} />}
                    </Box>
                  }
                />
              </ListItem>
            </List>
          </Paper>
        </Grid>

        {/* Informações dos Provedores */}
        <Grid item xs={12}>
          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
            Provedores Disponíveis
          </Typography>

          {Object.entries(providers).map(([key, provider]) => (
            <Accordion key={key} sx={{ mb: 1 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box display="flex" alignItems="center" gap={2}>
                  {getProviderIcon(key)}
                  <Typography variant="h6">{provider.name}</Typography>
                  <Chip
                    size="small"
                    label={provider.requires_api_key ? 'Requer API Key' : 'Local'}
                    color={provider.requires_api_key ? 'primary' : 'success'}
                  />
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={8}>
                    <Typography variant="body2" paragraph>
                      {provider.description}
                    </Typography>

                    <Typography variant="subtitle2" gutterBottom>
                      Modelos Pré-configurados:
                    </Typography>
                    <Box display="flex" flexWrap="wrap" gap={1} mb={2}>
                      {provider.models.map((model) => (
                        <Chip
                          key={model}
                          label={model}
                          size="small"
                          variant={model === provider.default_model ? 'filled' : 'outlined'}
                          color={model === provider.default_model ? 'primary' : 'default'}
                        />
                      ))}
                    </Box>

                    <Alert severity="info" sx={{ mt: 2 }}>
                      <Typography variant="body2">
                        💡 <strong>Dica:</strong> Você pode usar modelos customizados além dos listados acima.
                        Ative a opção "Usar modelo customizado" e digite o nome exato do modelo conforme a documentação do provedor.
                      </Typography>
                    </Alert>
                  </Grid>

                  <Grid item xs={12} md={4}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="subtitle2" gutterBottom>
                          Configurações
                        </Typography>
                        <Typography variant="body2">
                          <strong>URL Base:</strong><br />
                          {provider.base_url}
                        </Typography>
                        <Typography variant="body2" sx={{ mt: 1 }}>
                          <strong>Modelo Padrão:</strong><br />
                          {provider.default_model}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>
          ))}
        </Grid>

        {/* Agentes e seleções de LLM */}
        <Grid item xs={12}>
          <Paper elevation={3} sx={{ p: 3, mt: 2 }}>
            <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Agentes registrados</Typography>
              <Typography variant="body2" color="text.secondary">
                {agents.length} agente(s) visível(eis)
              </Typography>
            </Stack>

            {agents.length === 0 ? (
              <Alert severity="info" sx={{ mb: 2 }}>
                Nenhum agente cadastrado. Crie um agente para começar a delegar tarefas ao Crew.
              </Alert>
            ) : (
              <Stack spacing={2}>
                {agents.map((agent) => (
                  <Paper key={agent.id} variant="outlined" sx={{ p: 2 }}>
                    <Stack direction="row" justifyContent="space-between" alignItems="center">
                      <Box>
                        <Typography variant="subtitle1">{agent.nome}</Typography>
                        <Typography variant="body2" color="text.secondary">
                          Papel: {agent.role} • LLM atual: {agent.llm_config?.nome || 'Sem configuração específica'}
                        </Typography>
                      </Box>
                      <Button
                        variant="outlined"
                        startIcon={<EditIcon />}
                        onClick={() => openAgentDialog(agent)}
                      >
                        Editar
                      </Button>
                    </Stack>
                  </Paper>
                ))}
              </Stack>
            )}

            <Divider sx={{ my: 3 }} />

            <Typography variant="subtitle1" gutterBottom>
              LLMs disponíveis ({llmConfigs.length})
            </Typography>
            <Stack direction="row" flexWrap="wrap" gap={1}>
              {llmConfigs.map((config) => (
                <Chip
                  key={config.id}
                  label={`${config.nome} (${config.provider}/${config.model})`}
                  variant={config.is_default ? 'filled' : 'outlined'}
                  color={config.is_active ? 'success' : 'default'}
                />
              ))}
            </Stack>
          </Paper>
        </Grid>
      </Grid>

      <Dialog open={agentDialogOpen} onClose={() => setAgentDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Editar Agente</DialogTitle>
        <DialogContent dividers>
          <Stack spacing={2}>
            <TextField
              label="Nome"
              value={agentForm.nome}
              onChange={(e) => handleAgentFormChange('nome', e.target.value)}
              fullWidth
            />
            <TextField
              label="Papel"
              value={agentForm.role}
              onChange={(e) => handleAgentFormChange('role', e.target.value)}
              fullWidth
            />
            <TextField
              label="Objetivo (goal)"
              value={agentForm.goal}
              onChange={(e) => handleAgentFormChange('goal', e.target.value)}
              fullWidth
              multiline
              minRows={3}
            />
            <TextField
              label="Histórico (backstory)"
              value={agentForm.backstory}
              onChange={(e) => handleAgentFormChange('backstory', e.target.value)}
              fullWidth
              multiline
              minRows={2}
            />
            <FormControl fullWidth>
              <InputLabel>LLM dedicado (opcional)</InputLabel>
              <Select
                value={agentForm.llm_config_id || ''}
                label="LLM dedicado (opcional)"
                onChange={(e) => handleAgentFormChange('llm_config_id', e.target.value)}
              >
                <MenuItem value="">Usa LLM padrão</MenuItem>
                {llmConfigs.map((config) => (
                  <MenuItem key={config.id} value={config.id}>
                    {config.nome} ({config.provider} / {config.model})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAgentDialogOpen(false)}>Cancelar</Button>
          <Button onClick={handleAgentSave} variant="contained" disabled={agentSaving}>
            {agentSaving ? 'Salvando...' : 'Salvar agente'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}

export default AIConfigPage;
