import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  RadioGroup,
  FormControlLabel,
  Radio,
  Stepper,
  Step,
  StepLabel,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  LinearProgress
} from '@mui/material';
import api, { evolucoesService } from '../services/api';

const PHQ9Test = ({ patientId, open, onClose, onTestCompleted }) => {
  const [activeStep, setActiveStep] = useState(0);
  const [responses, setResponses] = useState({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // Definição das perguntas do PHQ-9
  const questions = [
    "1. Pouco interesse ou pouco prazer em fazer as coisas",
    "2. Sentir-se para baixo, deprimido ou sem esperanças",
    "3. Dificuldade para pegar no sono ou permanecer dormindo, ou dormir demais",
    "4. Sentir-se cansado ou com pouca energia",
    "5. Falta de apetite ou comer demais",
    "6. Sentir-se mal consigo mesmo – ou achar que é um fracasso ou que decepcionou a família ou você mesmo",
    "7. Dificuldade de concentração nas atividades (ex.: ler jornal, ver TV)",
    "8. Lentidão para se movimentar ou falar, a ponto de outras pessoas perceberem; ou o oposto, agitação ou inquietação excessiva",
    "9. Pensamentos de que seria melhor estar morto ou de se ferir de alguma maneira"
  ];

  const steps = ['Questionário', 'Resultado'];

  const handleResponseChange = (questionIndex, value) => {
    const key = `q${questionIndex + 1}`;
    setResponses(prev => ({
      ...prev,
      [key]: parseInt(value)
    }));
  };

  const handleNext = () => {
    if (activeStep < steps.length - 1) {
      setActiveStep(prev => prev + 1);
    }
  };

  const handleBack = () => {
    setActiveStep(prev => prev - 1);
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.post(`/phq9/paciente/${patientId}`, responses);
      setResult(response.data.teste.resultados);
      setActiveStep(1); // Ir para resultado

      // Criar entrada de evolução automaticamente
      const { pontuacao_total, nivel_depressao, depressao_positiva, risco_suicida } = response.data.teste.resultados;

      let conclusao = '';
      if (depressao_positiva) {
        conclusao = `Resultado sugere sintomas depressivos (${getNivelDescription(nivel_depressao)}).`;
      } else {
        conclusao = 'Resultado não sugere sintomas depressivos significativos.';
      }

      if (risco_suicida) {
        conclusao += ' ATENÇÃO: Risco suicida identificado - avaliação imediata recomendada.';
      }

      const evolucaoData = {
        paciente_id: patientId,
        nota_evolucao: `Resultado Teste PHQ-9 - Avaliação de Depressão\n\nPontuação total: ${pontuacao_total}/27\nNível: ${getNivelDescription(nivel_depressao)}\n\nConclusão: ${conclusao}\n\nEste é um resultado de triagem e não substitui diagnóstico clínico.`,
        data_evolucao: new Date().toISOString().split('T')[0]
      };

      try {
        await evolucoesService.criar(evolucaoData);
        console.log('Evolução criada automaticamente para resultado do PHQ-9');
      } catch (evolucaoError) {
        console.error('Erro ao criar evolução automaticamente:', evolucaoError);
        // Não falhar o teste se a evolução não puder ser criada
      }

      if (onTestCompleted) {
        onTestCompleted(response.data.teste);
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Erro ao salvar teste');
    } finally {
      setLoading(false);
    }
  };

  const canProceed = () => {
    // Verificar se todas as 9 perguntas foram respondidas
    for (let i = 1; i <= 9; i++) {
      const key = `q${i}`;
      if (responses[key] === undefined) {
        return false;
      }
    }
    return true;
  };

  const getNivelDescription = (nivel) => {
    switch (nivel) {
      case 'minima': return 'Mínima (0-4 pontos)';
      case 'leve': return 'Leve (5-9 pontos)';
      case 'moderada': return 'Moderada (10-14 pontos)';
      case 'moderadamente_grave': return 'Moderadamente Grave (15-19 pontos)';
      case 'grave': return 'Grave (20-27 pontos)';
      default: return nivel;
    }
  };

  const renderQuestionStep = () => {
    return (
      <Box>
        <Typography variant="h6" gutterBottom>
          Questionário de Saúde do Paciente (PHQ-9)
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Nas últimas duas semanas, com que frequência você foi incomodado por:
        </Typography>

        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2, px: 2 }}>
          <Typography variant="caption" sx={{ minWidth: 60 }}>Nunca</Typography>
          <Typography variant="caption" sx={{ minWidth: 60 }}>Vários dias</Typography>
          <Typography variant="caption" sx={{ minWidth: 60 }}>Mais da metade</Typography>
          <Typography variant="caption" sx={{ minWidth: 60 }}>Quase todos</Typography>
        </Box>

        {questions.map((question, index) => (
          <Card key={index} sx={{ mb: 2 }}>
            <CardContent sx={{ pb: 2 }}>
              <Typography variant="body1" sx={{ mb: 1 }}>
                {question}
              </Typography>
              <RadioGroup
                row
                value={responses[`q${index + 1}`] ?? ''}
                onChange={(e) => handleResponseChange(index, e.target.value)}
                sx={{ justifyContent: 'space-between', px: 2 }}
              >
                <FormControlLabel value={0} control={<Radio />} label="0" />
                <FormControlLabel value={1} control={<Radio />} label="1" />
                <FormControlLabel value={2} control={<Radio />} label="2" />
                <FormControlLabel value={3} control={<Radio />} label="3" />
              </RadioGroup>
            </CardContent>
          </Card>
        ))}
      </Box>
    );
  };

  const renderResult = () => {
    if (!result) return null;

    const { pontuacao_total, nivel_depressao, depressao_positiva, risco_suicida } = result;

    return (
      <Box>
        <Typography variant="h6" gutterBottom>
          Resultado do Teste PHQ-9
        </Typography>

        <Box sx={{ mb: 3 }}>
          <Typography variant="body1" sx={{ mb: 2 }}>
            <strong>Pontuação Total:</strong> {pontuacao_total} de 27 pontos
          </Typography>
          <Typography variant="body1" sx={{ mb: 2 }}>
            <strong>Classificação:</strong> {getNivelDescription(nivel_depressao)}
          </Typography>
        </Box>

        <Box sx={{ mb: 3 }}>
          <Typography variant="body1" sx={{ mb: 2 }}>
            <strong>Interpretação:</strong>
          </Typography>

          {depressao_positiva ? (
            <Alert severity="warning" sx={{ mb: 2 }}>
              <Typography variant="body2">
                O resultado sugere a presença de sintomas depressivos ({getNivelDescription(nivel_depressao)}).
                Recomenda-se avaliação mais aprofundada por um profissional de saúde mental.
              </Typography>
            </Alert>
          ) : (
            <Alert severity="success" sx={{ mb: 2 }}>
              <Typography variant="body2">
                O resultado não sugere sintomas depressivos significativos neste momento.
              </Typography>
            </Alert>
          )}

          {risco_suicida && (
            <Alert severity="error" sx={{ mb: 2 }}>
              <Typography variant="body2">
                <strong>ATENÇÃO:</strong> Risco suicida identificado. 
                É recomendada avaliação imediata por profissional de saúde mental.
                Se necessário, entre em contato com o CVV (188) ou procure atendimento de urgência.
              </Typography>
            </Alert>
          )}
        </Box>

        <Alert severity="info">
          <Typography variant="body2">
            <strong>IMPORTANTE:</strong> O PHQ-9 é uma ferramenta de TRIAGEM e NÃO SUBSTITUI um diagnóstico clínico.
            Os resultados são apenas indicativos e devem ser interpretados por um profissional de saúde qualificado.
            Este teste avalia sintomas nas últimas duas semanas e pode não refletir o quadro completo.
          </Typography>
        </Alert>
      </Box>
    );
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        Teste PHQ-9 - Questionário de Saúde do Paciente
        <Chip
          label={`Passo ${activeStep + 1} de ${steps.length}`}
          size="small"
          sx={{ ml: 2 }}
        />
      </DialogTitle>

      <DialogContent>
        <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
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

        {activeStep === 0 && renderQuestionStep()}
        {activeStep === 1 && renderResult()}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>
          {activeStep === 1 ? 'Fechar' : 'Cancelar'}
        </Button>

        {activeStep > 0 && activeStep < 1 && (
          <Button onClick={handleBack}>
            Voltar
          </Button>
        )}

        {activeStep === 0 && (
          <Button
            variant="contained"
            onClick={handleNext}
            disabled={!canProceed()}
          >
            Ver Resultado
          </Button>
        )}

        {activeStep === 0 && canProceed() && (
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={!canProceed() || loading}
            sx={{ ml: 1 }}
          >
            {loading ? 'Salvando...' : 'Finalizar Teste'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default PHQ9Test;
