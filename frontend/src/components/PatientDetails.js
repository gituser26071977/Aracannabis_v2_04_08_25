import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Paper, Typography, Grid, Box, Divider, Button } from '@mui/material';
import {
  Person as PersonIcon,
  Phone as PhoneIcon,
  MedicalServices as MedicalIcon,
  Note as NoteIcon,
  Edit as EditIcon,
} from '@mui/icons-material';

const PatientDetails = ({
  patient,
  onEdit,
  onTabChange,
  showActions = true,
  habilitarCannabis = false,
}) => {
  const navigate = useNavigate();

  const goToTab = (index) => {
    if (typeof onTabChange === 'function') {
      onTabChange(index);
    } else {
      navigate(`/pacientes/detail/${patient.id}`, {
        state: { initialTab: index },
        replace: true,
      });
    }
  };
  if (!patient) {
    return (
      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="h6" color="text.secondary" align="center">
          Selecione um paciente para visualizar os detalhes
        </Typography>
      </Paper>
    );
  }

  // Formatar data
  const formatDate = (dateString) => {
    if (!dateString) return 'Não informado';
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR');
  };

  // Calcular idade
  const calculateAge = (birthDateString) => {
    if (!birthDateString) return 'N/A';

    const birthDate = new Date(birthDateString);
    const today = new Date();

    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();

    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }

    return age;
  };

  // Formatar gênero
  const formatGender = (gender) => {
    const genders = {
      masculino: 'Masculino',
      feminino: 'Feminino',
      outro: 'Outro',
      nao_informado: 'Não informado',
    };

    return genders[gender] || 'Não informado';
  };

  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Box
        sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}
      >
        <Typography variant="h5" gutterBottom>
          {patient.nome}
        </Typography>

        <Button
          variant="outlined"
          color="secondary"
          startIcon={<EditIcon />}
          onClick={() => onEdit(patient)}
        >
          Editar
        </Button>
      </Box>

      <Divider sx={{ mb: 3 }} />

      <Grid container spacing={3}>
        {/* Informações pessoais */}
        <Grid item xs={12} md={6}>
          <Paper elevation={1} sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
              <PersonIcon sx={{ mr: 1 }} /> Informações Pessoais
            </Typography>

            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  Data de Nascimento
                </Typography>
                <Typography variant="body1">{formatDate(patient.data_nascimento)}</Typography>
              </Grid>

              <Grid item xs={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  Idade
                </Typography>
                <Typography variant="body1">
                  {calculateAge(patient.data_nascimento)} anos
                </Typography>
              </Grid>

              <Grid item xs={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  CPF
                </Typography>
                <Typography variant="body1">{patient.cpf || 'Não informado'}</Typography>
              </Grid>

              <Grid item xs={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  Gênero
                </Typography>
                <Typography variant="body1">{formatGender(patient.genero)}</Typography>
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        {/* Informações de contato */}
        <Grid item xs={12} md={6}>
          <Paper elevation={1} sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
              <PhoneIcon sx={{ mr: 1 }} /> Contato
            </Typography>

            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12}>
                <Typography variant="subtitle2" color="text.secondary">
                  Telefone
                </Typography>
                <Typography variant="body1">{patient.telefone || 'Não informado'}</Typography>
              </Grid>

              <Grid item xs={12}>
                <Typography variant="subtitle2" color="text.secondary">
                  E-mail
                </Typography>
                <Typography variant="body1">{patient.email || 'Não informado'}</Typography>
              </Grid>

              <Grid item xs={12}>
                <Typography variant="subtitle2" color="text.secondary">
                  Endereço
                </Typography>
                <Typography variant="body1">{patient.endereco || 'Não informado'}</Typography>
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        {/* Informações médicas */}
        <Grid item xs={12}>
          <Paper elevation={1} sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
              <MedicalIcon sx={{ mr: 1 }} /> Informações Médicas
            </Typography>

            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12}>
                <Typography variant="subtitle2" color="text.secondary">
                  Diagnóstico
                </Typography>
                <Typography variant="body1">{patient.diagnostico || 'Não informado'}</Typography>
              </Grid>

              <Grid item xs={12}>
                <Typography variant="subtitle2" color="text.secondary">
                  Observações
                </Typography>
                <Typography variant="body1">{patient.observacoes || 'Não informado'}</Typography>
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        {/* Histórico */}
        <Grid item xs={12}>
          <Paper elevation={1} sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
              <NoteIcon sx={{ mr: 1 }} /> Histórico
            </Typography>

            {showActions && patient.id && (
              <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                <Grid container spacing={2} sx={{ maxWidth: '85%' }}>
                  <Grid item xs={12} sm={6} md={3}>
                    <Button
                      fullWidth
                      variant="contained"
                      color="primary"
                      onClick={() => goToTab(1)}
                      sx={{ py: 1.275, fontSize: '0.85rem', borderRadius: '20px' }}
                    >
                      Sintomas
                    </Button>
                  </Grid>

                  {habilitarCannabis && (
                    <Grid item xs={12} sm={6} md={3}>
                      <Button
                        fullWidth
                        variant="contained"
                        color="secondary"
                        onClick={() => goToTab(4)}
                        sx={{ py: 1.275, fontSize: '0.85rem', borderRadius: '20px' }}
                      >
                        Dosagens
                      </Button>
                    </Grid>
                  )}

                  <Grid item xs={12} sm={6} md={3}>
                    <Button
                      fullWidth
                      variant="contained"
                      color="success"
                      onClick={() => goToTab(1)}
                      sx={{ py: 1.275, fontSize: '0.85rem', borderRadius: '20px' }}
                    >
                      Evoluções
                    </Button>
                  </Grid>

                  <Grid item xs={12} sm={6} md={3}>
                    <Button
                      fullWidth
                      variant="contained"
                      color="info"
                      onClick={() => goToTab(1)}
                      sx={{ py: 1.275, fontSize: '0.85rem', borderRadius: '20px' }}
                    >
                      📊 Gráficos
                    </Button>
                  </Grid>
                </Grid>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Paper>
  );
};

export default PatientDetails;
