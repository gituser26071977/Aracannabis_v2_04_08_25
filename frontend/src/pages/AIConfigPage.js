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

  useEffect(() => {
    loadProviders();
    loadAgentManagement();
  }, []);

  const loadProviders = async () => {
    try {
      setLoading(true);
      const data = await aiConfigService.obterProvedores();
      setProviders(data.providers);
      setCurrentConfig(data.current_config);
      
      // Definir valores atuais
      setSelectedProvider(data.current_config.provider || 'groq');
      setSelectedModel(data.current_config.model || '');
      setBaseUrl(data.current_config.base_url || '');
      
      // Verificar se o modelo atual é customizado
      if (data.current_config.provider && data.providers[data.current_config.provider]) {
        const isCustom = !data.providers[data.current_config.provider].models.includes(data.current_config.model);
        if (isCustom) {
          setUseCustomModel(true);
          setCustomModel(data.current_config.model);
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

        {/* Status Atual */}
        <Grid item xs={12} md={4}>
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Status Atual
            </Typography>
            
            <List>
              <ListItem>
                <ListItemIcon>
                  {getProviderIcon(currentConfig.provider)}
                </ListItemIcon>
                <ListItemText
                  primary="Provedor Ativo"
                  secondary={providers[currentConfig.provider]?.name || currentConfig.provider}
                />
              </ListItem>
              
              <ListItem>
                <ListItemIcon>
                  <SettingsIcon />
                </ListItemIcon>
                <ListItemText
                  primary="Modelo"
                  secondary={
                    <Box>
                      <Typography variant="body2">{currentConfig.model}</Typography>
                      {currentConfig.provider && providers[currentConfig.provider] && 
                       !providers[currentConfig.provider].models.includes(currentConfig.model) && (
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
                  secondary={
                    <Box>
                      {currentConfig.has_openai_key && <Chip size="small" label="OpenAI" sx={{ mr: 0.5, mb: 0.5 }} />}
                      {currentConfig.has_anthropic_key && <Chip size="small" label="Anthropic" sx={{ mr: 0.5, mb: 0.5 }} />}
                      {currentConfig.has_google_key && <Chip size="small" label="Google" sx={{ mr: 0.5, mb: 0.5 }} />}
                      {currentConfig.has_groq_key && <Chip size="small" label="Groq" sx={{ mr: 0.5, mb: 0.5 }} />}
                      {currentConfig.has_xai_key && <Chip size="small" label="xAI" sx={{ mr: 0.5, mb: 0.5 }} />}
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
