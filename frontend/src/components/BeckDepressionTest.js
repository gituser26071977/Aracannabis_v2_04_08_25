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

const BeckDepressionTest = ({ patientId, open, onClose, onTestCompleted }) => {
  const [activeStep, setActiveStep] = useState(0);
  const [responses, setResponses] = useState({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // Definição das perguntas do BDI-II
  const questions = [
    "1. Tristeza: Sinto-me triste.",
    "2. Pessimismo: Sinto-me tão desanimado(a) com o futuro que não espero que as coisas melhorem.",
    "3. Fracasso passado: Sinto que sou um fracasso.",
    "4. Perda de prazer: Não tenho prazer nas coisas que antes me davam prazer.",
    "5. Sentimentos de culpa: Sinto-me culpado(a) a maior parte do tempo.",
    "6. Sentimentos de punição: Sinto que estou sendo punido(a).",
    "7. Autoaversão: Sinto aversão por mim mesmo(a).",
    "8. Autocrítica: Critico-me a mim mesmo(a) por minhas fraquezas ou erros.",
    "9. Pensamentos suicidas: Tenho pensamentos de me matar, mas não os executaria.",
    "10. Choro: Choro mais do que o habitual.",
    "11. Agitação: Sinto-me mais irritado(a) do que o habitual.",
    "12. Perda de interesse: Perdi o interesse pelas outras pessoas.",
    "13. Indecisão: Tenho dificuldade em tomar decisões.",
    "14. Desvalia: Sinto-me sem valor.",
    "15. Perda de energia: Não tenho energia suficiente para fazer as coisas.",
    "16. Mudanças no sono: Meu padrão de sono mudou (durmo mais ou durmo menos do que o habitual).",
    "17. Irritabilidade: Sinto-me irritado(a) facilmente.",
    "18. Mudanças no apetite: Meu apetite mudou (como mais ou como menos do que o habitual).",
    "19. Dificuldade de concentração: Tenho dificuldade em me concentrar.",
    "20. Cansaço/fadiga: Sinto-me cansado(a) o tempo todo.",
    "21. Perda de interesse sexual: Perdi o interesse pelo sexo."
  ];

  const steps = ['Questionário', 'Resultado'];

  const handleResponseChange = (questionIndex, value) => {
    const key = `item_${questionIndex + 1}`;
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
      const response = await api.post(`/beck-depression/paciente/${patientId}`, responses);
      setResult(response.data.teste.resultados);
      setActiveStep(1); // Ir para resultado

      // Criar entrada de evolução automaticamente
      const { pontuacao_total, nivel_depressao, depressao_positiva } = response.data.teste.resultados;

      let conclusao = '';
      if (depressao_positiva) {
        conclusao = `Resultado sugere sintomas depressivos (${nivel_depressao}).`;
      } else {
        conclusao = 'Resultado não sugere sintomas depressivos significativos.';
      }

      const evolucaoData = {
        paciente_id: patientId,
        nota_evolucao: `Resultado Teste BDI-II - Avaliação de Depressão\n\nPontuação total: ${pontuacao_total}/63\nNível: ${nivel_depressao.charAt(0).toUpperCase() + nivel_depressao.slice(1)}\n\nConclusão: ${conclusao}\n\nEste é um resultado de triagem e não substitui diagnóstico clínico.`,
        data_evolucao: new Date().toISOString().split('T')[0]
      };

      try {
        await evolucoesService.criar(evolucaoData);
        if(process.env.NODE_ENV!=='production')console.log('Evolução criada automaticamente para resultado do BDI-II');
      } catch (evolucaoError) {
        if(process.env.NODE_ENV!=='production')console.error('Erro ao criar evolução automaticamente:', evolucaoError);
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
    // Verificar se todas as 21 perguntas foram respondidas
    for (let i = 1; i <= 21; i++) {
      const key = `item_${i}`;
      if (responses[key] === undefined) {
        return false;
      }
    }
    return true;
  };

  const renderQuestionStep = () => {
    return (
      <Box>
        <Typography variant="h6" gutterBottom>
          Inventário de Depressão de Beck (BDI-II)
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Avalie cada afirmação de acordo com como você se sentiu na última semana, incluindo hoje.
        </Typography>

        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2, px: 2 }}>
          <Typography variant="caption" sx={{ minWidth: 80 }}>Não</Typography>
          <Typography variant="caption" sx={{ minWidth: 80 }}>Levemente</Typography>
          <Typography variant="caption" sx={{ minWidth: 80 }}>Moderadamente</Typography>
          <Typography variant="caption" sx={{ minWidth: 80 }}>Gravemente</Typography>
        </Box>

        {questions.map((question, index) => (
          <Card key={index} sx={{ mb: 2 }}>
            <CardContent sx={{ pb: 2 }}>
              <Typography variant="body1" sx={{ mb: 1 }}>
                {question}
              </Typography>
              <RadioGroup
                row
                value={responses[`item_${index + 1}`] ?? ''}
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

    const { pontuacao_total, nivel_depressao, depressao_positiva } = result;

    const getNivelDescription = (nivel) => {
      switch (nivel) {
        case 'minima': return 'Depressão Mínima (0-13 pontos)';
        case 'leve': return 'Depressão Leve (14-19 pontos)';
        case 'moderada': return 'Depressão Moderada (20-28 pontos)';
        case 'grave': return 'Depressão Grave (29-63 pontos)';
        default: return nivel;
      }
    };

    return (
      <Box>
        <Typography variant="h6" gutterBottom>
          Resultado do Teste BDI-II
        </Typography>

        <Box sx={{ mb: 3 }}>
          <Typography variant="body1" sx={{ mb: 2 }}>
            <strong>Pontuação Total:</strong> {pontuacao_total} de 63 pontos
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
                O resultado sugere a presença de sintomas depressivos ({nivel_depressao}).
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
        </Box>

        <Alert severity="info">
          <Typography variant="body2">
            <strong>IMPORTANTE:</strong> O BDI-II é uma ferramenta de TRIAGEM e NÃO SUBSTITUI um diagnóstico clínico.
            Os resultados são apenas indicativos e devem ser interpretados por um profissional de saúde qualificado.
            Este teste avalia sintomas na última semana e pode não refletir o quadro completo.
          </Typography>
        </Alert>
      </Box>
    );
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        Teste BDI-II - Inventário de Depressão de Beck
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

export default BeckDepressionTest;
