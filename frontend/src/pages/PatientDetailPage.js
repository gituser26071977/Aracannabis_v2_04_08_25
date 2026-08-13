import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Paper,
  Tabs,
  Tab,
  Typography,
  Button,
  CircularProgress,
  Alert,
  IconButton,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Edit as EditIcon,
  Event as EventIcon,
  Description as DescriptionIcon,
  NoteAdd as NoteAddIcon,
  AddPhotoAlternate as AddPhotoIcon,
} from '@mui/icons-material';
import QuickActionsBar from '../components/QuickActionsBar';
import { pacientesService } from '../services/api';
import PatientDetails from '../components/PatientDetails';
import SymptomsManager from '../components/SymptomsManager';
import EvolutionManager from '../components/EvolutionManager';
import CombinedChartView from '../components/CombinedChartView';
import ExameManager from '../components/ExameManager';
import FollowupPanel from '../components/FollowupPanel';
import AnamneseViewer from '../components/AnamneseViewer';
import ReceituarioBase from '../components/ReceituarioBase';
import HCReportPanel from '../components/HCReportPanel';
import DosageManager from '../components/DosageManager';
import CannabisProfilePanel from '../components/CannabisProfilePanel';
import DigitalTwinPanel from '../components/DigitalTwinPanel';
import { useModulos } from '../contexts/ModulosContext';

// Componente TabPanel para exibir o conteúdo da aba selecionada
function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`patient-detail-tabpanel-${index}`}
      aria-labelledby={`patient-detail-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

// Função para criar propriedades de acessibilidade para as abas
function a11yProps(index) {
  return {
    id: `patient-detail-tab-${index}`,
    'aria-controls': `patient-detail-tabpanel-${index}`,
  };
}

const PatientDetailPage = () => {
  const { patientId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { hasModulo } = useModulos();
  const [patient, setPatient] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [tabValue, setTabValue] = useState(0);

  // Set initial tab based on location state
  useEffect(() => {
    if (location.state?.initialTab !== undefined) {
      setTabValue(location.state.initialTab);
    }

    // Adicionar listener para evento personalizado de navegação entre abas
    const handleNavigateToTab = (event) => {
      if (event.detail && typeof event.detail.tabIndex === 'number') {
        setTabValue(event.detail.tabIndex);
      }
    };

    window.addEventListener('navigateToTab', handleNavigateToTab);

    return () => {
      window.removeEventListener('navigateToTab', handleNavigateToTab);
    };
  }, [location.state]);

  // Carregar dados do paciente
  useEffect(() => {
    const fetchPatient = async () => {
      setLoading(true);
      try {
        const response = await pacientesService.obter(patientId);
        setPatient(response.paciente);
        setError('');
      } catch (err) {
        if (process.env.NODE_ENV !== 'production') console.error('Erro ao carregar paciente:', err);
        setError('Não foi possível carregar os dados do paciente');
      } finally {
        setLoading(false);
      }
    };

    if (patientId) {
      fetchPatient();
    }
  }, [patientId]);

  // Manipulador de mudança de aba
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  // Voltar para a lista de pacientes
  const handleBack = () => {
    navigate('/pacientes');
  };

  // Editar paciente
  const handleEdit = () => {
    navigate(`/pacientes/edit/${patientId}`);
  };

  // Apenas profissionais com o módulo cannabis-medicinal ativo veem as
  // funcionalidades específicas de cannabis (dosagens, produtos, perfil
  // canabinoide, laudo HC, checklist ANVISA).
  const habilitarCannabis = hasModulo('cannabis-medicinal');

  // Garantir que a aba ativa nunca ultrapasse o número de abas disponíveis
  // (quando o módulo cannabis não está ativo, a aba 4 não existe).
  useEffect(() => {
    if (!habilitarCannabis && tabValue >= 4) {
      setTabValue(0);
    }
  }, [habilitarCannabis, tabValue]);

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
        <Typography variant="h5" component="h1" sx={{ flexGrow: 1 }}>
          {patient.nome}
        </Typography>
        <Button variant="outlined" startIcon={<EditIcon />} onClick={handleEdit}>
          Editar
        </Button>
      </Box>

      {/* Quick Actions */}
      <QuickActionsBar
        title="Ações Rápidas"
        compact
        actions={[
          { label: 'Nova Consulta', icon: <EventIcon />, onClick: () => navigate('/consultas') },
          { label: 'Nova Prescrição', icon: <DescriptionIcon />, onClick: () => setTabValue(2) },
          { label: 'Nova Evolução', icon: <NoteAddIcon />, onClick: () => setTabValue(1) },
          { label: 'Adicionar Exame', icon: <AddPhotoIcon />, onClick: () => setTabValue(3) },
        ]}
      />

      {/* Abas */}
      <Paper elevation={3} sx={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          aria-label="Abas de detalhes do paciente"
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab label="📋 Informações" {...a11yProps(0)} />
          <Tab label="🩺 Prontuário" {...a11yProps(1)} />
          <Tab label="📋 Receituário" {...a11yProps(2)} />
          <Tab label="📄 Documentos" {...a11yProps(3)} />
          {habilitarCannabis && <Tab label="💊 Cannabis Medicinal" {...a11yProps(4)} />}
        </Tabs>
      </Paper>

      {/* Conteúdo das abas */}
      <TabPanel value={tabValue} index={0}>
        <PatientDetails
          patient={patient}
          onEdit={handleEdit}
          onTabChange={setTabValue}
          habilitarCannabis={habilitarCannabis}
        />
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          <AnamneseViewer patientId={patientId} habilitarCannabis={habilitarCannabis} />
          <EvolutionManager patientId={patientId} habilitarCannabis={habilitarCannabis} />
          <SymptomsManager patientId={patientId} />
          <CombinedChartView patientId={patientId} habilitarCannabis={habilitarCannabis} />
        </Box>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <ReceituarioBase patientId={patientId} />
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          <ExameManager patientId={patientId} habilitarCannabis={habilitarCannabis} />
          <FollowupPanel patientId={patientId} habilitarCannabis={habilitarCannabis} />
          {habilitarCannabis && <CannabisExtras patientId={patientId} />}
        </Box>
      </TabPanel>

      {habilitarCannabis && (
        <TabPanel value={tabValue} index={4}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <DosageManager patientId={patientId} />
            <CannabisProfilePanel patientId={patientId} />
            <DigitalTwinPanel patientId={patientId} />
          </Box>
        </TabPanel>
      )}
    </Box>
  );
};

// Laudo para Habeas Corpus — exclusivo do fluxo canabinoide. Mantido em
// componente separado para facilitar o gate por módulo.
const CannabisExtras = ({ patientId }) => <HCReportPanel patientId={patientId} />;

export default PatientDetailPage;
