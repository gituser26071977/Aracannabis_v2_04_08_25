import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Box, 
  Paper, 
  Typography, 
  Button,
  CircularProgress,
  Alert,
  IconButton
} from '@mui/material';
import { 
  ArrowBack as ArrowBackIcon
} from '@mui/icons-material';
import { pacientesService } from '../services/api';
import PatientForm from '../components/PatientForm';

const PatientEditPage = () => {
  const { patientId } = useParams();
  const navigate = useNavigate();
  const [patient, setPatient] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Carregar dados do paciente
  useEffect(() => {
    const fetchPatient = async () => {
      setLoading(true);
      try {
        const response = await pacientesService.obter(patientId);
        setPatient(response.paciente);
        setError('');
      } catch (err) {
        if(process.env.NODE_ENV!=='production')console.error('Erro ao carregar paciente:', err);
        setError('Não foi possível carregar os dados do paciente');
      } finally {
        setLoading(false);
      }
    };
    
    if (patientId) {
      fetchPatient();
    }
  }, [patientId]);
  
  // Voltar para a página de detalhes do paciente
  const handleBack = () => {
    navigate(`/pacientes/detail/${patientId}`);
  };
  
  // Manipulador para quando um paciente é salvo
  const handlePatientSaved = (updatedPatient) => {
    navigate(`/pacientes/detail/${patientId}`);
  };
  
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 5 }}>
        <CircularProgress />
      </Box>
    );
  }
  
  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert 
          severity="error" 
          action={
            <Button color="inherit" size="small" onClick={handleBack}>
              Voltar
            </Button>
          }
        >
          {error}
        </Alert>
      </Box>
    );
  }
  
  if (!patient) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert 
          severity="warning" 
          action={
            <Button color="inherit" size="small" onClick={handleBack}>
              Voltar
            </Button>
          }
        >
          Paciente não encontrado
        </Alert>
      </Box>
    );
  }
  
  return (
    <Box sx={{ width: '100%' }}>
      {/* Cabeçalho */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <IconButton onClick={handleBack} sx={{ mr: 2 }}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h5" component="h1">
          Editar Paciente: {patient.nome}
        </Typography>
      </Box>
      
      {/* Formulário de edição */}
      <PatientForm 
        initialData={patient} 
        onSave={handlePatientSaved}
      />
    </Box>
  );
};

export default PatientEditPage;
