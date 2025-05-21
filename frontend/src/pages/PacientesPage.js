import React, { useState } from 'react';
import { Box, Tab, Tabs, Paper } from '@mui/material';
import PatientList from '../components/PatientList';
import PatientForm from '../components/PatientForm';
import PatientDetails from '../components/PatientDetails';

// Componente TabPanel para exibir o conteúdo da aba selecionada
function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`pacientes-tabpanel-${index}`}
      aria-labelledby={`pacientes-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

// Função para criar propriedades de acessibilidade para as abas
function a11yProps(index) {
  return {
    id: `pacientes-tab-${index}`,
    'aria-controls': `pacientes-tabpanel-${index}`,
  };
}

const PacientesPage = () => {
  // Estado para controlar a aba ativa
  const [tabValue, setTabValue] = useState(0);
  
  // Estado para armazenar o paciente selecionado para edição ou visualização
  const [selectedPatient, setSelectedPatient] = useState(null);
  
  // Estado para forçar a atualização da lista de pacientes
  const [refreshList, setRefreshList] = useState(0);
  
  // Manipulador de mudança de aba
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };
  
  // Manipulador para editar um paciente
  const handleEditPatient = (patient) => {
    setSelectedPatient(patient);
    setTabValue(1); // Mudar para a aba de formulário
  };
  
  // Manipulador para visualizar um paciente
  const handleViewPatient = (patient) => {
    setSelectedPatient(patient);
    setTabValue(2); // Mudar para a aba de detalhes
  };
  
  // Manipulador para adicionar um novo paciente
  const handleAddPatient = () => {
    setSelectedPatient(null); // Limpar paciente selecionado
    setTabValue(1); // Mudar para a aba de formulário
  };
  
  // Manipulador para quando um paciente é salvo
  const handlePatientSaved = () => {
    setRefreshList(prev => prev + 1); // Incrementar para forçar atualização da lista
    setTabValue(0); // Voltar para a aba de lista
  };
  
  return (
    <Box sx={{ width: '100%' }}>
      <Paper elevation={3} sx={{ mb: 3 }}>
        <Tabs 
          value={tabValue} 
          onChange={handleTabChange} 
          aria-label="Abas de gerenciamento de pacientes"
          variant="fullWidth"
        >
          <Tab label="Lista de Pacientes" {...a11yProps(0)} />
          <Tab label={selectedPatient ? 'Editar Paciente' : 'Novo Paciente'} {...a11yProps(1)} />
          <Tab label="Detalhes do Paciente" {...a11yProps(2)} disabled={!selectedPatient} />
        </Tabs>
      </Paper>
      
      <TabPanel value={tabValue} index={0}>
        <PatientList 
          onEdit={handleEditPatient} 
          onView={handleViewPatient} 
          onAdd={handleAddPatient}
          refreshTrigger={refreshList}
        />
      </TabPanel>
      
      <TabPanel value={tabValue} index={1}>
        <PatientForm 
          initialData={selectedPatient} 
          onSave={handlePatientSaved}
        />
      </TabPanel>
      
      <TabPanel value={tabValue} index={2}>
        <PatientDetails 
          patient={selectedPatient} 
          onEdit={handleEditPatient}
        />
      </TabPanel>
    </Box>
  );
};

export default PacientesPage;
