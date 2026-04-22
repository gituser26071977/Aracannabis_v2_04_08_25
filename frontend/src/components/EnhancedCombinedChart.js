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
  Grid
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
import moment from 'moment';

const EnhancedCombinedChart = ({ patientId }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [sintomasData, setSintomasData] = useState([]);
  const [dosagensData, setDosagensData] = useState([]);
  const [selectedSintoma, setSelectedSintoma] = useState('');
  const [sintomasList, setSintomasList] = useState([]);
  const [selectedPeriod, setSelectedPeriod] = useState('integral');
  
  // Carregar dados
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Carregar dados de sintomas
        const sintomasResponse = await sintomasService.obterDadosGrafico(patientId, selectedPeriod);
        console.log('Dados de sintomas recebidos:', sintomasResponse);
        
        // Verificar a estrutura dos dados e definir sintomasData
        if (sintomasResponse.dados_grafico && Array.isArray(sintomasResponse.dados_grafico)) {
          setSintomasData(sintomasResponse.dados_grafico);
        } else if (Array.isArray(sintomasResponse)) {
          setSintomasData(sintomasResponse);
        } else {
          setSintomasData([]);
        }
        
        // Extrair lista de sintomas únicos
        let uniqueSintomas = [];
        if (Array.isArray(sintomasResponse)) {
          // Se for array direto, extrair nomes únicos
          uniqueSintomas = [...new Set(sintomasResponse.map(item => item.nome_sintoma))];
        } else if (sintomasResponse.dados_grafico && Array.isArray(sintomasResponse.dados_grafico)) {
          // Se for estrutura com dados_grafico
          uniqueSintomas = [...new Set(sintomasResponse.dados_grafico.map(item => item.label))];
        }
        
        setSintomasList(uniqueSintomas);
        
        // Selecionar o primeiro sintoma por padrão
        if (uniqueSintomas.length > 0 && !selectedSintoma) {
          setSelectedSintoma(uniqueSintomas[0]);
        }
        
        // Carregar dados de dosagens
        const dosagensResponse = await dosagensService.obterDadosGrafico(patientId, selectedPeriod);
        console.log('Dados de dosagens recebidos:', dosagensResponse);
        
        if (dosagensResponse.dados_grafico && Array.isArray(dosagensResponse.dados_grafico)) {
          setDosagensData(dosagensResponse.dados_grafico);
        } else if (Array.isArray(dosagensResponse)) {
          setDosagensData(dosagensResponse);
        } else {
          setDosagensData([]);
        }
        
        setError('');
      } catch (err) {
        console.error('Erro ao carregar dados para o gráfico combinado:', err);
        setError(`Não foi possível carregar os dados para o gráfico: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };
    
    if (patientId) {
      fetchData();
    }
  }, [patientId, selectedPeriod]);

  // Processar dados para o gráfico
  const processChartData = () => {
    if (!selectedSintoma || sintomasData.length === 0) {
      return [];
    }
    
    try {
      // Processar dados de sintomas
      // A API retorna: { dados_grafico: [ { label, data: [ {x, y} ] } ] }
      let processedSintomas = [];
      
      const datasets = Array.isArray(sintomasData) 
        ? sintomasData 
        : (sintomasData.dados_grafico || []);
      
      const selectedDataset = datasets.find(s => s.label === selectedSintoma);
      
      if (selectedDataset && Array.isArray(selectedDataset.data)) {
        processedSintomas = selectedDataset.data.map(point => ({
          date: moment(point.x).format('YYYY-MM-DD'),
          sintoma: point.y,
          sintoma_texto: `${selectedSintoma}: ${point.y}`
        }));
      }
      
      // Processar dados de dosagens
      // A API retorna: { dados_grafico: [ {x, y, dosagem_texto} ], dados_canabinoides: {cbd, thc, ...} }
      let processedDosagens = [];
      const dosagensList = Array.isArray(dosagensData)
        ? dosagensData
        : (dosagensData.dados_grafico || []);
      
      if (dosagensList.length > 0) {
        processedDosagens = dosagensList.map(point => ({
          date: moment(point.x).format('YYYY-MM-DD'),
          dosagem: point.y,
          dosagem_texto: point.dosagem_texto || `Dosagem: ${point.y} mg/dia`
        }));
      }
      
      // Criar mapa para combinar dados por data
      const combinedMap = new Map();
      
      // Adicionar sintomas
      processedSintomas.forEach(item => {
        combinedMap.set(item.date, {
          date: item.date,
          sintoma: item.sintoma,
          sintoma_texto: item.sintoma_texto,
          dosagem: null,
          dosagem_texto: null
        });
      });
      
      // Adicionar dosagens (agregadas no backend, então 1 por data)
      processedDosagens.forEach(item => {
        if (combinedMap.has(item.date)) {
          const existing = combinedMap.get(item.date);
          combinedMap.set(item.date, {
            ...existing,
            dosagem: item.dosagem,
            dosagem_texto: item.dosagem_texto
          });
        } else {
          combinedMap.set(item.date, {
            date: item.date,
            sintoma: null,
            sintoma_texto: null,
            dosagem: item.dosagem,
            dosagem_texto: item.dosagem_texto
          });
        }
      });
      
      // Converter para array e ordenar cronologicamente
      return Array.from(combinedMap.values()).sort((a, b) => 
        moment(a.date).valueOf() - moment(b.date).valueOf()
      );
    } catch (error) {
      console.error('Erro ao processar dados combinados:', error);
      setError('Erro ao combinar dados para o gráfico');
      return [];
    }
  };
  
  const combinedData = processChartData();
  
  // Debug: log dos dados processados
  console.log('Dados processados para o gráfico:', {
    selectedSintoma,
    sintomasData: sintomasData.length,
    dosagensData: dosagensData.length,
    processedSintomas: combinedData.filter(d => d.sintoma !== null).length,
    combinedData: combinedData.length
  });
  
  const handleSintomaChange = (event) => {
    setSelectedSintoma(event.target.value);
  };

  const handlePeriodChange = (event) => {
    setSelectedPeriod(event.target.value);
  };
  
  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = moment(dateString);
    return date.isValid() ? date.format('DD/MM/YYYY') : dateString;
  };
  
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <Paper elevation={3} sx={{ p: 2, backgroundColor: 'white' }}>
          <Typography variant="subtitle2">
            {formatDate(label || payload[0]?.payload?.date)}
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
  
  if (sintomasList.length === 0 || !selectedSintoma) {
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
      
      <Box sx={{ height: 400, width: '100%' }}>
        <ResponsiveContainer>
          <LineChart
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
            
            {/* Linha de sintomas */}
            <Line 
              yAxisId="left"
              type="monotone" 
              dataKey="sintoma" 
              name="Sintoma" 
              stroke="#8884d8" 
              activeDot={{ r: 8 }} 
              data={combinedData}
              connectNulls={false}
            />
            
            {/* Linha de dosagens */}
            <Line 
              yAxisId="right"
              type="monotone" 
              dataKey="dosagem" 
              name="Dosagem" 
              stroke="#82ca9d" 
              data={combinedData}
              connectNulls={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </Box>
      
      {combinedData.length === 0 && (
        <Alert severity="info" sx={{ mt: 2 }}>
          Não há dados suficientes para exibir o gráfico combinado.
        </Alert>
      )}
      
      <Box sx={{ mt: 2 }}>
        <Typography variant="body2" color="text.secondary">
          Este gráfico mostra a relação entre a intensidade dos sintomas e as dosagens ao longo do tempo.
        </Typography>
      </Box>
    </Paper>
  );
};

export default EnhancedCombinedChart;
