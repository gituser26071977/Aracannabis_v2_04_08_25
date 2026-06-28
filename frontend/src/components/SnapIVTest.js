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

const SnapIVTest = ({ patientId, open, onClose, onTestCompleted }) => {
  const [activeStep, setActiveStep] = useState(0);
  const [responses, setResponses] = useState({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // Definição das perguntas SNAP-IV
  const questions = {
    desatencao: [
      "1. Não presta atenção em detalhes ou comete erros por descuido.",
      "2. Tem dificuldade de manter a atenção em tarefas ou atividades lúdicas.",
      "3. Parece não ouvir quando se fala diretamente com ele(a).",
      "4. Não segue instruções e não termina deveres ou tarefas.",
      "5. Tem dificuldade para organizar tarefas e atividades.",
      "6. Evita, não gosta ou reluta em se envolver em tarefas que exijam esforço mental prolongado.",
      "7. Perde coisas necessárias para tarefas ou atividades.",
      "8. É facilmente distraído(a) por estímulos externos.",
      "9. É esquecido(a) em atividades diárias."
    ],
    hiperatividade: [
      "10. Agita as mãos ou os pés ou se remexe na cadeira.",
      "11. Levanta-se da cadeira em situações em que se espera que permaneça sentado.",
      "12. Corre ou sobe nas coisas em situações em que isso é inapropriado.",
      "13. É incapaz de brincar ou se envolver em atividades de lazer calmamente.",
      "14. Está frequentemente 'a todo vapor', agindo como se estivesse 'ligado na tomada'.",
      "15. Fala demais.",
      "16. Deixa escapar uma resposta antes que a pergunta tenha sido concluída.",
      "17. Tem dificuldade de esperar a sua vez.",
      "18. Interrompe ou se intromete em conversas ou brincadeiras dos outros."
    ]
  };

  const steps = ['Desatenção', 'Hiperatividade/Impulsividade', 'Resultado'];

  const handleResponseChange = (questionIndex, value) => {
    const key = activeStep === 0 ? `desatencao_${questionIndex + 1}` : `hiperatividade_${questionIndex + 10}`;
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
      const response = await api.post(`/snap-iv/paciente/${patientId}`, responses);
      setResult(response.data.teste.resultados);
      setActiveStep(2); // Ir para resultado

      // Criar entrada de evolução automaticamente
      const { pontos_desatencao, pontos_hiperatividade, sugestivo_desatencao, sugestivo_hiperatividade, tdah_positivo } = response.data.teste.resultados;

      let conclusao = '';
      if (tdah_positivo) {
        if (sugestivo_desatencao && sugestivo_hiperatividade) {
          conclusao = 'Resultado sugere apresentação COMBINADA de TDAH.';
        } else if (sugestivo_desatencao) {
          conclusao = 'Resultado sugere apresentação PREDOMINANTEMENTE DESATENTA de TDAH.';
        } else {
          conclusao = 'Resultado sugere apresentação PREDOMINANTEMENTE HIPERATIVA/IMPULSIVA de TDAH.';
        }
      } else {
        conclusao = 'Resultado NÃO sugere TDAH com base nos critérios do SNAP-IV.';
      }

      const evolucaoData = {
        paciente_id: patientId,
        nota_evolucao: `Resultado Teste SNAP-IV - Triagem TDAH\n\nPontos Desatenção: ${pontos_desatencao}/9\nPontos Hiperatividade: ${pontos_hiperatividade}/9\n\nConclusão: ${conclusao}\n\nEste é um resultado de triagem e não substitui diagnóstico clínico.`,
        data_evolucao: new Date().toISOString().split('T')[0]
      };

      try {
        await evolucoesService.criar(evolucaoData);
        if(process.env.NODE_ENV!=='production')console.log('Evolução criada automaticamente para resultado do SNAP-IV');
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
    const currentQuestions = activeStep === 0 ? questions.desatencao : questions.hiperatividade;
    return currentQuestions.every((_, index) => {
      const key = activeStep === 0 ? `desatencao_${index + 1}` : `hiperatividade_${index + 10}`;
      return responses[key] !== undefined;
    });
  };

  const renderQuestionStep = () => {
    const currentQuestions = activeStep === 0 ? questions.desatencao : questions.hiperatividade;
    const sectionTitle = activeStep === 0 ? 'Sintomas de Desatenção' : 'Sintomas de Hiperatividade/Impulsividade';

    return (
      <Box>
        <Typography variant="h6" gutterBottom>
          {sectionTitle}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Avalie a frequência de cada comportamento nas últimas semanas:
        </Typography>

        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2, px: 2 }}>
          <Typography variant="caption" sx={{ minWidth: 60 }}>Nunca</Typography>
          <Typography variant="caption" sx={{ minWidth: 60 }}>Pouco</Typography>
          <Typography variant="caption" sx={{ minWidth: 60 }}>Bastante</Typography>
          <Typography variant="caption" sx={{ minWidth: 60 }}>Demais</Typography>
        </Box>

        {currentQuestions.map((question, index) => {
          const key = activeStep === 0 ? `desatencao_${index + 1}` : `hiperatividade_${index + 10}`;
          return (
            <Card key={index} sx={{ mb: 2 }}>
              <CardContent sx={{ pb: 2 }}>
                <Typography variant="body1" sx={{ mb: 1 }}>
                  {question}
                </Typography>
                <RadioGroup
                  row
                  value={responses[key] ?? ''}
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
          );
        })}
      </Box>
    );
  };

  const renderResult = () => {
    if (!result) return null;

    const { pontos_desatencao, pontos_hiperatividade, sugestivo_desatencao, sugestivo_hiperatividade, tdah_positivo } = result;

    return (
      <Box>
        <Typography variant="h6" gutterBottom>
          Resultado do Teste SNAP-IV
        </Typography>

        <Box sx={{ mb: 3 }}>
          <Typography variant="body1" sx={{ mb: 2 }}>
            <strong>Pontos significativos:</strong>
          </Typography>
          <Typography>Desatenção: {pontos_desatencao} de 9</Typography>
          <Typography>Hiperatividade/Impulsividade: {pontos_hiperatividade} de 9</Typography>
        </Box>

        <Box sx={{ mb: 3 }}>
          <Typography variant="body1" sx={{ mb: 2 }}>
            <strong>Conclusão:</strong>
          </Typography>

          {tdah_positivo ? (
            <Alert severity="warning" sx={{ mb: 2 }}>
              <Typography variant="body2">
                {sugestivo_desatencao && sugestivo_hiperatividade
                  ? "O resultado sugere uma apresentação COMBINADA de TDAH."
                  : sugestivo_desatencao
                  ? "O resultado sugere uma apresentação PREDOMINANTEMENTE DESATENTA de TDAH."
                  : "O resultado sugere uma apresentação PREDOMINANTEMENTE HIPERATIVA/IMPULSIVA de TDAH."
                }
              </Typography>
            </Alert>
          ) : (
            <Alert severity="success" sx={{ mb: 2 }}>
              <Typography variant="body2">
                O resultado NÃO SUGERE TDAH com base nos critérios do SNAP-IV.
              </Typography>
            </Alert>
          )}
        </Box>

        <Alert severity="info">
          <Typography variant="body2">
            <strong>IMPORTANTE:</strong> Este teste é uma ferramenta de TRIAGEM e NÃO SUBSTITUI um diagnóstico clínico.
            Os resultados são apenas indicativos e devem ser interpretados por um profissional de saúde qualificado.
          </Typography>
        </Alert>
      </Box>
    );
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        Teste SNAP-IV - Triagem para TDAH
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

        {activeStep < 2 && renderQuestionStep()}
        {activeStep === 2 && renderResult()}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>
          {activeStep === 2 ? 'Fechar' : 'Cancelar'}
        </Button>

        {activeStep > 0 && activeStep < 2 && (
          <Button onClick={handleBack}>
            Voltar
          </Button>
        )}

        {activeStep < 1 && (
          <Button
            variant="contained"
            onClick={handleNext}
            disabled={!canProceed()}
          >
            Próximo
          </Button>
        )}

        {activeStep === 1 && (
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={!canProceed() || loading}
          >
            {loading ? 'Salvando...' : 'Finalizar Teste'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default SnapIVTest;
