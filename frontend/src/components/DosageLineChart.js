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
  MenuItem
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
import { dosagensService } from '../services/api';
import moment from 'moment';

const DosageLineChart = ({ patientId }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [dosagensData, setDosagensData] = useState([]);
  const [selectedPeriod, setSelectedPeriod] = useState('integral');
  
  // Carregar dados
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        console.log(`Buscando dados gráfico para paciente ${patientId}, período ${selectedPeriod}`);
        // Carregar dados de dosagens usando o novo endpoint
        const response = await dosagensService.obterDadosGraficoNovo(patientId, selectedPeriod);
        console.log('Resposta completa do serviço:', response);
        
        // Extrair dados de canabinoides (CBD e THC)
        let dadosGrafico = [];
        if (response && response.dados_canabinoides) {
          const cbdData = response.dados_canabinoides.cbd || [];
          const thcData = response.dados_canabinoides.thc || [];
          
          // Combinar dados de CBD e THC por data
          const dataMap = new Map();
          
          cbdData.forEach(item => {
            dataMap.set(item.x, {
              date: item.x,
              cbd: item.y,
              thc: 0
            });
          });
          
          thcData.forEach(item => {
            if (dataMap.has(item.x)) {
              dataMap.get(item.x).thc = item.y;
            } else {
              dataMap.set(item.x, {
                date: item.x,
                cbd: 0,
                thc: item.y
              });
            }
          });
          
          dadosGrafico = Array.from(dataMap.values()).sort((a, b) => new Date(a.date) - new Date(b.date));
        }
        
        console.log('Dados para gráfico:', dadosGrafico);
        setDosagensData(dadosGrafico);
        setError('');
      } catch (err) {
        console.error('Erro ao carregar dados para o gráfico de dosagens:', err);
        setError('Não foi possível carregar os dados de dosagens');
      } finally {
        setLoading(false);
      }
    };
    
    if (patientId) {
      fetchData();
    }
  }, [patientId, selectedPeriod]);

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
            {formatDate(label)}
          </Typography>
          {payload.map((entry, index) => (
            <Box key={index} sx={{ color: entry.color, mt: 1 }}>
              <Typography variant="body2">
                {entry.name}: {entry.value} mg/dia
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
  
  if (dosagensData.length === 0) {
    return (
      <Alert severity="info">
        Não há dados de dosagens registrados para este paciente.
      </Alert>
    );
  }
  
  // Usar dados diretamente
  const chartData = dosagensData;
  
  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">
          Evolução de CBD e THC
        </Typography>
        
        <FormControl sx={{ minWidth: 200 }}>
          <InputLabel id="period-select-label">Período</InputLabel>
          <Select
            labelId="period-select-label"
            id="period-select"
            value={selectedPeriod}
            label="Período"
            onChange={handlePeriodChange}
            size="small"
          >
            <MenuItem value="1m">1 Mês</MenuItem>
            <MenuItem value="3m">3 Meses</MenuItem>
            <MenuItem value="6m">6 Meses</MenuItem>
            <MenuItem value="1y">1 Ano</MenuItem>
            <MenuItem value="integral">Registro Integral</MenuItem>
          </Select>
        </FormControl>
      </Box>
      
      <Box sx={{ height: 350, width: '100%' }}>
        <ResponsiveContainer>
          <LineChart
            data={chartData}
            margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis 
              dataKey="date" 
              tickFormatter={formatDate}
              tick={{ fontSize: 12 }}
            />
            <YAxis 
              label={{ value: 'mg/dia', angle: -90, position: 'insideLeft' }}
              tick={{ fontSize: 12 }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="cbd" 
              name="CBD" 
              stroke="#4CAF50" 
              activeDot={{ r: 6 }}
              strokeWidth={3}
              dot={{ r: 4 }}
            />
            <Line 
              type="monotone" 
              dataKey="thc" 
              name="THC" 
              stroke="#FF9800" 
              activeDot={{ r: 6 }}
              strokeWidth={3}
              dot={{ r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </Box>
    </Box>
  );
};

export default DosageLineChart;
