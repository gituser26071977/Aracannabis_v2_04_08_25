
import React, { useState } from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    Typography,
    Radio,
    RadioGroup,
    FormControlLabel,
    FormControl,
    FormLabel,
    Box,
    Stepper,
    Step,
    StepLabel,
    Divider,
    Paper
} from '@mui/material';

const QUESTIONS = [
    "Sentindo-se nervoso(a), ansioso(a) ou muito tenso(a)",
    "Não sendo capaz de impedir ou de controlar as preocupações",
    "Preocupando-se muito com diversas coisas",
    "Tendo dificuldade para relaxar",
    "Ficando tão agitado(a) que se torna difícil permanecer sentado(a)",
    "Ficando facilmente aborrecido(a) ou irritado(a)",
    "Sentindo medo como se algo horrível fosse acontecer"
];

const OPTIONS = [
    { value: 0, label: "Nenhuma vez" },
    { value: 1, label: "Vários dias" },
    { value: 2, label: "Mais da metade dos dias" },
    { value: 3, label: "Quase todos os dias" }
];

const GAD7Test = ({ open, onClose, onCompleted }) => {
    const [activeStep, setActiveStep] = useState(0);
    const [answers, setAnswers] = useState({});
    const [score, setScore] = useState(null);

    const handleAnswer = (event) => {
        const value = parseInt(event.target.value);
        setAnswers({ ...answers, [activeStep]: value });
    };

    const handleNext = () => {
        if (activeStep < QUESTIONS.length - 1) {
            setActiveStep(activeStep + 1);
        } else {
            calculateResult();
        }
    };

    const handleBack = () => {
        setActiveStep(activeStep - 1);
    };

    const calculateResult = () => {
        let totalScore = 0;
        for (let i = 0; i < QUESTIONS.length; i++) {
            totalScore += answers[i] || 0;
        }
        setScore(totalScore);
    };

    const handleFinish = async () => {
        // Prepare payload for API
        const payload = {
            q1: answers[0],
            q2: answers[1],
            q3: answers[2],
            q4: answers[3],
            q5: answers[4],
            q6: answers[5],
            q7: answers[6],
            observacoes: ""
        };

        // Pass payload back to parent component which will handle the API call
        // This keeps the component reusable and decoupled from specific API calls if needed,
        // but for this specific integration, the parent (SymptomsManager) will call the service.

        // Simple linear mapping: (score / 21) * 10
        const normalizedScore = Math.round((score / 21) * 10);

        onCompleted({
            rawScore: score,
            normalizedScore: normalizedScore,
            maxScore: 21,
            interpretation: getInterpretation(score),
            testData: payload // Send raw data to be saved
        });
        resetTest();
    };

    const getInterpretation = (score) => {
        if (score <= 4) return "Ansiedade Mínima";
        if (score <= 9) return "Ansiedade Leve";
        if (score <= 14) return "Ansiedade Moderada";
        return "Ansiedade Grave";
    };

    const resetTest = () => {
        setActiveStep(0);
        setAnswers({});
        setScore(null);
    }

    const handleCloseAndReset = () => {
        resetTest();
        onClose();
    }

    const progress = ((activeStep + 1) / QUESTIONS.length) * 100;

    return (
        <Dialog open={open} onClose={handleCloseAndReset} maxWidth="md" fullWidth>
            <DialogTitle sx={{ backgroundColor: '#f5f5f5', pb: 2 }}>
                Avaliação de Ansiedade (GAD-7)
                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                    Nas últimas 2 semanas, com que frequência você foi incomodado(a) pelos problemas abaixo?
                </Typography>
            </DialogTitle>

            <DialogContent sx={{ mt: 2 }}>
                {score === null ? (
                    <>
                        <Box sx={{ width: '100%', mb: 4 }}>
                            <Stepper activeStep={activeStep} alternativeLabel>
                                {QUESTIONS.map((label, index) => (
                                    <Step key={index}>
                                        <StepLabel></StepLabel>
                                    </Step>
                                ))}
                            </Stepper>
                        </Box>

                        <Paper elevation={0} sx={{ p: 2, bgcolor: 'background.default', borderRadius: 2 }}>
                            <FormControl component="fieldset" fullWidth>
                                <FormLabel component="legend" sx={{
                                    fontSize: '1.2rem',
                                    fontWeight: 'bold',
                                    mb: 3,
                                    color: 'text.primary'
                                }}>
                                    {activeStep + 1}. {QUESTIONS[activeStep]}
                                </FormLabel>
                                <RadioGroup
                                    value={answers[activeStep] !== undefined ? answers[activeStep] : ''}
                                    onChange={handleAnswer}
                                >
                                    {OPTIONS.map((option) => (
                                        <FormControlLabel
                                            key={option.value}
                                            value={option.value}
                                            control={<Radio />}
                                            label={
                                                <Box sx={{ py: 1 }}>
                                                    <Typography variant="body1" fontWeight={answers[activeStep] === option.value ? 'bold' : 'normal'}>
                                                        {option.label}
                                                    </Typography>
                                                    <Typography variant="caption" color="text.secondary">
                                                        (+{option.value} pontos)
                                                    </Typography>
                                                </Box>
                                            }
                                            sx={{
                                                mb: 1,
                                                border: '1px solid #e0e0e0',
                                                borderRadius: 1,
                                                px: 2,
                                                '&:hover': { bgcolor: 'action.hover' },
                                                bgcolor: answers[activeStep] === option.value ? '#e3f2fd' : 'transparent',
                                                borderColor: answers[activeStep] === option.value ? '#2196f3' : '#e0e0e0'
                                            }}
                                        />
                                    ))}
                                </RadioGroup>
                            </FormControl>
                        </Paper>
                    </>
                ) : (
                    <Box sx={{ textAlign: 'center', py: 3 }}>
                        <Typography variant="h4" color="primary" gutterBottom>
                            Pontuação: {score} / 21
                        </Typography>
                        <Typography variant="h5" sx={{ mb: 3, fontWeight: 'medium' }}>
                            {getInterpretation(score)}
                        </Typography>

                        <Divider sx={{ my: 2 }} />

                        <Typography variant="body1" paragraph>
                            Este resultado será salvo automaticamente como a intensidade do sintoma "Ansiedade" (0-10) no gráfico.
                        </Typography>
                        <Typography variant="h6">
                            Intensidade calculada: {Math.round((score / 21) * 10)}/10
                        </Typography>
                    </Box>
                )}
            </DialogContent>

            <DialogActions sx={{ p: 2, bgcolor: 'action.hover' }}>
                {score === null ? (
                    <>
                        <Button
                            disabled={activeStep === 0}
                            onClick={handleBack}
                        >
                            Voltar
                        </Button>
                        <Button
                            variant="contained"
                            onClick={handleNext}
                            disabled={answers[activeStep] === undefined}
                        >
                            {activeStep === QUESTIONS.length - 1 ? 'Calcular Resultado' : 'Próxima'}
                        </Button>
                    </>
                ) : (
                    <Button
                        variant="contained"
                        color="success"
                        onClick={handleFinish}
                        size="large"
                    >
                        Confirmar e Salvar
                    </Button>
                )}
            </DialogActions>
        </Dialog>
    );
};

export default GAD7Test;
