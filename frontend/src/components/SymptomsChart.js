import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  CircularProgress, 
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import { sintomasService } from '../services/api';

const SymptomsChart = ({ patientId }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [sintomasData, setSintomasData] = useState([]);
  const [selectedSintoma, setSelectedSintoma] = useState('');
  const [sintomasList, setSintomasList] = useState([]);
  
  // Carregar dados
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        console.log(`🔍 Buscando sintomas para paciente ${patientId}`);
        
        // Carregar sintomas do paciente
        const sintomasResponse = await sintomasService.listar(patientId);
        console.log('📊 Resposta da API de sintomas:', sintomasResponse);
        
        const sintomasArray = sintomasResponse?.sintomas || [];
        
        if (Array.isArray(sintomasArray) && sintomasArray.length > 0) {
          console.log('✅ Dados recebidos:', sintomasArray.length, 'itens');
          
          // Extrair nomes únicos de sintomas
          const uniqueSintomas = [...new Set(sintomasArray.map(s => s.sintoma))];
          console.log('🏷️ Sintomas únicos encontrados:', uniqueSintomas);
          
          setSintomasList(uniqueSintomas);
          
          // Selecionar o primeiro sintoma por padrão
          const sintomaParaUsar = selectedSintoma || (uniqueSintomas.length > 0 ? uniqueSintomas[0] : '');
          if (sintomaParaUsar && !selectedSintoma) {
            setSelectedSintoma(sintomaParaUsar);
            console.log('🎯 Primeiro sintoma selecionado:', sintomaParaUsar);
          }
          
          // Processar dados para o gráfico
          if (sintomaParaUsar) {
            const sintomasFiltrados = sintomasArray
              .filter(s => s.sintoma === sintomaParaUsar)
              .map(s => ({
                date: s.data,
                intensidade: s.intensidade,
                sintoma: s.sintoma
              }))
              .sort((a, b) => new Date(a.date + 'T12:00:00') - new Date(b.date + 'T12:00:00'));
            
            console.log('📈 Sintomas filtrados para gráfico:', sintomasFiltrados);
            setSintomasData(sintomasFiltrados);
          }
        } else {
          console.warn('⚠️ Nenhum sintoma encontrado:', sintomasResponse);
        }
        
        setError('');
      } catch (err) {
        console.error('❌ Erro ao carregar sintomas:', err);
        setError(`Erro ao carregar sintomas: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };
    
    if (patientId) {
      fetchData();
    }
  }, [patientId, selectedSintoma]);

  const handleSintomaChange = (event) => {
    console.log('🔄 Sintoma alterado para:', event.target.value);
    setSelectedSintoma(event.target.value);
  };
  
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }
  
  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }
  
  if (sintomasList.length === 0) {
    return (
      <Alert severity="info">
        Não há sintomas registrados para este paciente.
      </Alert>
    );
  }
  
  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="h6" gutterBottom>
        Gráfico de Sintomas - Debug
      </Typography>
      
      <FormControl fullWidth sx={{ mb: 3 }}>
        <InputLabel id="sintoma-select-label">Sintoma</InputLabel>
        <Select
          labelId="sintoma-select-label"
          id="sintoma-select"
          value={selectedSintoma}
          label="Sintoma"
          onChange={handleSintomaChange}
        >
          {sintomasList.map((sintoma) => (
            <MenuItem key={sintoma} value={sintoma}>
              {sintoma}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
      
      {/* Debug: Mostrar dados brutos */}
      <Paper elevation={2} sx={{ p: 2, mb: 2, backgroundColor: '#f8f9fa' }}>
        <Typography variant="subtitle2" gutterBottom color="primary">
          🔍 DEBUG - Dados Recebidos da API:
        </Typography>
        <Typography variant="body2" component="pre" sx={{ fontSize: '0.75rem', overflow: 'auto' }}>
          Sintoma selecionado: {selectedSintoma}
        </Typography>
        <Typography variant="body2" component="pre" sx={{ fontSize: '0.75rem', overflow: 'auto', mt: 1 }}>
          Total de sintomas: {sintomasData.length}
        </Typography>
        <Typography variant="body2" component="pre" sx={{ fontSize: '0.75rem', overflow: 'auto', mt: 1 }}>
          Dados brutos: {JSON.stringify(sintomasData, null, 2)}
        </Typography>
      </Paper>
      
      {/* Gráfico simples */}
      {sintomasData.length > 0 && (
        <Paper elevation={2} sx={{ p: 2, backgroundColor: '#e8f5e8' }}>
          <Typography variant="subtitle2" gutterBottom color="success.main">
            📊 Gráfico Simples (Teste):
          </Typography>
          <Box sx={{ height: 200, width: '100%', border: '1px solid #ccc', p: 2 }}>
            {sintomasData.map((item, index) => (
              <Box key={index} sx={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                mb: 1,
                p: 1,
                backgroundColor: '#fff',
                borderRadius: 1
              }}>
                <Typography variant="body2">
                  {new Date(item.date + 'T12:00:00').toLocaleDateString('pt-BR')}
                </Typography>
                <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                  {item.intensidade}
                </Typography>
              </Box>
            ))}
          </Box>
        </Paper>
      )}
      
      {sintomasData.length === 0 && selectedSintoma && (
        <Alert severity="warning">
          Nenhum dado encontrado para o sintoma "{selectedSintoma}"
        </Alert>
      )}
    </Box>
  );
};

export default SymptomsChart;
