import React, { useState, useEffect } from 'react';
import { 
  Paper, 
  Typography, 
  Box, 
  CircularProgress, 
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Button
} from '@mui/material';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts';
import { sintomasService, dosagensService } from '../services/api';

const CombinedChartView = ({ patientId }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [sintomasData, setSintomasData] = useState([]);
  const [dosagensData, setDosagensData] = useState([]);
  const [combinedData, setCombinedData] = useState([]);
  const [selectedSintoma, setSelectedSintoma] = useState('');
  const [sintomasList, setSintomasList] = useState([]);
  const [selectedPeriod, setSelectedPeriod] = useState('integral'); // '1m', '3m', '6m', '1y', 'integral'
  
  // Carregar dados
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Carregar dados de sintomas
        const sintomasResponse = await sintomasService.obterDadosGrafico(patientId, selectedPeriod);
        setSintomasData(sintomasResponse.dados_grafico || []);
        
        // Extrair lista de sintomas únicos
        const sintomas = sintomasResponse.dados_grafico || [];
        const uniqueSintomas = [...new Set(sintomas.map(item => item.label))];
        setSintomasList(uniqueSintomas);
        
        // Selecionar o primeiro sintoma por padrão
        if (uniqueSintomas.length > 0 && !selectedSintoma) {
          setSelectedSintoma(uniqueSintomas[0]);
        }
        
        // Carregar dados de dosagens
        const dosagensResponse = await dosagensService.obterDadosGrafico(patientId, selectedPeriod);
        setDosagensData(dosagensResponse.dados_grafico || []);
        
        setError('');
      } catch (err) {
        console.error('Erro ao carregar dados para o gráfico combinado:', err);
        setError('Não foi possível carregar os dados para o gráfico');
      } finally {
        setLoading(false);
      }
    };
    
    if (patientId) {
      fetchData();
    }
  }, [patientId, selectedPeriod, selectedSintoma]); // Adicionado selectedSintoma para recarregar se mudar, selectedPeriod para recarregar com período
  
  // Combinar dados quando sintoma selecionado ou dados mudam
  useEffect(() => {
    if (!selectedSintoma || sintomasData.length === 0 || !sintomasData.data) return;
    
    // Encontrar dados do sintoma selecionado
    const selectedSintomaData = sintomasData.find(s => s.label === selectedSintoma);
    if (!selectedSintomaData || !selectedSintomaData.data) return;
    
    const sintomaPoints = selectedSintomaData.data;
    const dosagemPoints = dosagensData.data || [];
    
    // Criar mapa de datas para facilitar a combinação
    const dataMap = {};
    
    // Adicionar pontos de sintoma
    sintomaPoints.forEach(point => {
      if (point.x && point.y !== null && point.y !== undefined) {
        dataMap[point.x] = {
          date: point.x,
          sintoma: point.y,
          sintoma_texto: point.sintoma_texto || `${point.y}`
        };
      }
    });
    
    // Adicionar pontos de dosagem
    dosagemPoints.forEach(point => {
      if (point.x && point.y !== null && point.y !== undefined) {
        if (dataMap[point.x]) {
          dataMap[point.x].dosagem = point.y;
          dataMap[point.x].dosagem_texto = point.dosagem_texto || `${point.y}`;
        } else {
          dataMap[point.x] = {
            date: point.x,
            dosagem: point.y,
            dosagem_texto: point.dosagem_texto || `${point.y}`
          };
        }
      }
    });
    
    // Converter mapa para array e ordenar por data
    const combined = Object.values(dataMap).sort((a, b) => {
      return new Date(a.date) - new Date(b.date);
    });
    
    setCombinedData(combined);
  }, [selectedSintoma, sintomasData, dosagensData]);
  
  // Manipulador de mudança de sintoma
  const handleSintomaChange = (event) => {
    setSelectedSintoma(event.target.value);
  };

  const handlePeriodChange = (event) => {
    setSelectedPeriod(event.target.value);
  };
  
  // Formatar data para exibição
  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR');
  };
  
  // Renderizar tooltip personalizado
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <Paper elevation={3} sx={{ p: 2, backgroundColor: 'white' }}>
          <Typography variant="subtitle2">
            {formatDate(label)}
          </Typography>
          {payload.map((entry, index) => (
            <Box key={index} sx={{ color: entry.color, mt: 1 }}>
              <Typography variant="body2">
                {entry.name === 'Sintoma' && entry.payload.sintoma_texto 
                  ? `${entry.name}: ${entry.payload.sintoma_texto}`
                  : entry.name === 'Dosagem' && entry.payload.dosagem_texto
                  ? `${entry.name}: ${entry.payload.dosagem_texto}`
                  : `${entry.name}: ${entry.value}`}
              </Typography>
            </Box>
          ))}
        </Paper>
      );
    }
    return null;
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
        Não há dados de sintomas registrados para este paciente.
      </Alert>
    );
  }
  
  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Gráfico Combinado: Sintomas e Dosagens
      </Typography>
      
      <Grid container spacing={2} alignItems="center" sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={4}>
          <FormControl fullWidth>
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
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <FormControl fullWidth>
            <InputLabel id="period-select-label">Período</InputLabel>
            <Select
              labelId="period-select-label"
              id="period-select"
              value={selectedPeriod}
              label="Período"
              onChange={handlePeriodChange}
            >
              <MenuItem value="1m">1 Mês</MenuItem>
              <MenuItem value="3m">3 Meses</MenuItem>
              <MenuItem value="6m">6 Meses</MenuItem>
              <MenuItem value="1y">1 Ano</MenuItem>
              <MenuItem value="integral">Registro Integral</MenuItem>
            </Select>
          </FormControl>
        </Grid>
      </Grid>
      
      {combinedData.length > 0 ? (
        <Box sx={{ height: 400, width: '100%' }}>
          <ResponsiveContainer>
            <LineChart
              data={combinedData}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="date" 
                tickFormatter={formatDate}
                label={{ value: 'Data', position: 'insideBottomRight', offset: -10 }}
              />
              <YAxis 
                yAxisId="left"
                label={{ value: 'Intensidade', angle: -90, position: 'insideLeft' }}
              />
              <YAxis 
                yAxisId="right" 
                orientation="right"
                label={{ value: 'Dosagem', angle: 90, position: 'insideRight' }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Line 
                yAxisId="left"
                type="monotone" 
                dataKey="sintoma" 
                name="Sintoma" 
                stroke="#8884d8" 
                activeDot={{ r: 8 }} 
              />
              <Line 
                yAxisId="right"
                type="monotone" 
                dataKey="dosagem" 
                name="Dosagem" 
                stroke="#82ca9d" 
              />
            </LineChart>
          </ResponsiveContainer>
        </Box>
      ) : (
        <Alert severity="info">
          Não há dados suficientes para exibir o gráfico combinado.
        </Alert>
      )}
      
      <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between' }}>
        <Typography variant="body2" color="text.secondary">
          Este gráfico mostra a relação entre a intensidade dos sintomas e as dosagens ao longo do tempo.
        </Typography>
      </Box>
    </Paper>
  );
};

export default CombinedChartView;
