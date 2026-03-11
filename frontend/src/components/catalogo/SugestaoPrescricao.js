/**
 * Componente de Sugestão de Produtos para Prescrição
 * Integra com o agente farmacêutico
 */
import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  Grid,
  Chip,
  Alert,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
  Paper,
  Divider,
} from '@mui/material';
import {
  LocalPharmacy as PharmacyIcon,
  CheckCircle as CheckCircleIcon,
  Lightbulb as LightbulbIcon,
} from '@mui/icons-material';
import { sugerirProdutos } from '../../services/catalogoService';

const SugestaoPrescricao = ({ pacienteId, pacienteNome, onProdutoSelecionado }) => {
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [resultado, setResultado] = useState(null);
  
  const [condicao, setCondicao] = useState('');
  const [sintomas, setSintomas] = useState('');
  const [preferencias, setPreferencias] = useState({
    evitar_thc: false,
    preferencia_cbd: true,
    via_preferida: '',
  });

  const steps = ['Dados Clinicos', 'Preferencias', 'Sugestoes'];

  const handleNext = () => {
    if (activeStep === 0 && (!condicao || !sintomas)) {
      setError('Preencha a condicao e os sintomas do paciente');
      return;
    }
    setError(null);
    setActiveStep((prev) => prev + 1);
  };

  const handleBack = () => {
    setActiveStep((prev) => prev - 1);
  };

  const handleBuscarSugestoes = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await sugerirProdutos(
        pacienteId,
        condicao,
        sintomas,
        preferencias
      );
      
      if (response.success) {
        setResultado(response);
        setActiveStep(2);
      } else {
        setError(response.message || 'Erro ao obter sugestoes');
      }
    } catch (err) {
      setError(err.message || 'Erro ao buscar sugestoes');
    } finally {
      setLoading(false);
    }
  };

  const handleSelecionarProduto = (produto) => {
    if (onProdutoSelecionado) {
      onProdutoSelecionado(produto, {
        condicao,
        sintomas,
        preferencias,
        justificativa: produto.justificativa,
        posologia_sugerida: produto.posologia_sugerida,
      });
    }
  };

  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return (
          <Box sx={{ mt: 2 }}>
            <Typography variant="h6" gutterBottom>
              Dados do Paciente: {pacienteNome}
            </Typography>
            
            <TextField
              fullWidth
              label="Condicao Medica Principal"
              value={condicao}
              onChange={(e) => setCondicao(e.target.value)}
              placeholder="Ex: Ansiedade Generalizada, Dor Cronica, Insonia..."
              sx={{ mb: 2 }}
              required
            />
            
            <TextField
              fullWidth
              label="Sintomas Principais"
              value={sintomas}
              onChange={(e) => setSintomas(e.target.value)}
              placeholder="Descreva os sintomas que o paciente apresenta..."
              multiline
              rows={3}
              required
            />
          </Box>
        );
        
      case 1:
        return (
          <Box sx={{ mt: 2 }}>
            <Typography variant="h6" gutterBottom>
              Preferencias de Tratamento
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferencias.evitar_thc}
                      onChange={(e) => setPreferencias(prev => ({
                        ...prev,
                        evitar_thc: e.target.checked
                      }))}
                    />
                  }
                  label="Evitar produtos com THC"
                />
                <Typography variant="caption" color="text.secondary" display="block">
                  Recomendado para pacientes sensiveis aos efeitos psicoativos
                </Typography>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferencias.preferencia_cbd}
                      onChange={(e) => setPreferencias(prev => ({
                        ...prev,
                        preferencia_cbd: e.target.checked
                      }))}
                    />
                  }
                  label="Preferencia por produtos ricos em CBD"
                />
                <Typography variant="caption" color="text.secondary" display="block">
                  Foca em produtos com maior concentracao de CBD
                </Typography>
              </Grid>
              
              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Via de Administracao Preferida</InputLabel>
                  <Select
                    value={preferencias.via_preferida}
                    onChange={(e) => setPreferencias(prev => ({
                      ...prev,
                      via_preferida: e.target.value
                    }))}
                    label="Via de Administracao Preferida"
                  >
                    <MenuItem value="">Sem preferencia</MenuItem>
                    <MenuItem value="Sublingual">Sublingual (Oleos)</MenuItem>
                    <MenuItem value="Oral">Oral (Capsulas)</MenuItem>
                    <MenuItem value="Topica">Topica (Cremes)</MenuItem>
                    <MenuItem value="Inalatoria">Inalatoria (Vaporizadores)</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
            
            <Box sx={{ mt: 3 }}>
              <Button
                variant="contained"
                fullWidth
                size="large"
                onClick={handleBuscarSugestoes}
                disabled={loading}
                startIcon={loading ? <CircularProgress size={20} /> : <PharmacyIcon />}
              >
                {loading ? 'Consultando Farmaceutico...' : 'Obter Sugestoes do Farmaceutico'}
              </Button>
            </Box>
          </Box>
        );
        
      case 2:
        if (!resultado) return null;
        
        return (
          <Box sx={{ mt: 2 }}>
            <Typography variant="h6" gutterBottom>
              Sugestoes do Agente Farmaceutico
            </Typography>
            
            {resultado.consideracoes_gerais && (
              <Alert severity="info" sx={{ mb: 2 }}>
                <Typography variant="subtitle2">Consideracoes Gerais:</Typography>
                <Typography variant="body2">{resultado.consideracoes_gerais}</Typography>
              </Alert>
            )}
            
            <Grid container spacing={2}>
              {resultado.sugestoes.map((sugestao, index) => (
                <Grid item xs={12} key={index}>
                  <Card variant="outlined" sx={{ mb: 2 }}>
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                        <Typography variant="h6">
                          {index + 1}. {sugestao.nome}
                        </Typography>
                        <Chip
                          icon={<PharmacyIcon />}
                          label={sugestao.marca}
                          color="primary"
                          size="small"
                        />
                      </Box>
                      
                      <Typography variant="body2" sx={{ mb: 2 }}>
                        <strong>Justificativa Clinica:</strong>
                        <br />
                        {sugestao.justificativa}
                      </Typography>
                      
                      <Divider sx={{ my: 1 }} />
                      
                      <Grid container spacing={2}>
                        <Grid item xs={12} md={6}>
                          <Typography variant="body2">
                            <strong>Posologia Sugerida:</strong>
                            <br />
                            {sugestao.posologia_sugerida || 'Nao especificada'}
                          </Typography>
                        </Grid>
                        <Grid item xs={12} md={6}>
                          <Typography variant="body2">
                            <strong>Precaucoes:</strong>
                            <br />
                            {sugestao.precaucoes || 'Nenhuma especifica'}
                          </Typography>
                        </Grid>
                      </Grid>
                      
                      <Box sx={{ mt: 2 }}>
                        <Button
                          variant="contained"
                          fullWidth
                          color="success"
                          startIcon={<CheckCircleIcon />}
                          onClick={() => handleSelecionarProduto(sugestao)}
                        >
                          Selecionar para Prescricao
                        </Button>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
            
            {resultado.recomendacao_farmaceutica && (
              <Paper sx={{ p: 2, mt: 2, bgcolor: 'grey.50' }}>
                <Typography variant="subtitle2" gutterBottom>
                  <LightbulbIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Recomendacao Farmaceutica
                </Typography>
                <Typography variant="body2">
                  {resultado.recomendacao_farmaceutica}
                </Typography>
              </Paper>
            )}
          </Box>
        );
        
      default:
        return null;
    }
  };

  return (
    <Box>
      <Stepper activeStep={activeStep} sx={{ mb: 3 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      <Paper sx={{ p: 3 }}>
        {renderStepContent()}
        
        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
          <Button
            disabled={activeStep === 0}
            onClick={handleBack}
            variant="outlined"
          >
            Voltar
          </Button>
          {activeStep < 1 && (
            <Button
              variant="contained"
              onClick={handleNext}
            >
              Proximo
            </Button>
          )}
        </Box>
      </Paper>
    </Box>
  );
};

export default SugestaoPrescricao;