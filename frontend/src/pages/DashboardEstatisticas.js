import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, Grid, CircularProgress, Alert } from '@mui/material';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
} from 'recharts';
import api from '../services/api';

const COLORS = [
  '#2D5A3D',
  '#4CAF50',
  '#81C784',
  '#A5D6A7',
  '#C8E6C9',
  '#FF8A65',
  '#FF7043',
  '#FF5722',
  '#795548',
  '#607D8B',
];
const GENDER_COLORS = { Masculino: '#1976D2', Feminino: '#E91E63', 'Não informado': '#BDBDBD' };
const CONSULT_TIPO_COLORS = { Presencial: '#2D5A3D', Telemedicina: '#7B1FA2' };

const DashboardEstatisticas = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [data, setData] = useState(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        const resp = await api.get('/dashboard/stats-detalhado');
        setData(resp.data);
      } catch (err) {
        setError('Erro ao carregar estatísticas.');
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, []);

  if (loading)
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
        <CircularProgress />
      </Box>
    );
  if (error) return <Alert severity="error">{error}</Alert>;
  if (!data) return null;

  const ChartCard = ({ title, children }) => (
    <Paper elevation={2} sx={{ p: 3, height: '100%' }}>
      <Typography variant="h6" gutterBottom fontWeight={600}>
        {title}
      </Typography>
      {children}
    </Paper>
  );

  const PieChartView = ({ data, colors, dataKey = 'value' }) => (
    <ResponsiveContainer width="100%" height={280}>
      <PieChart>
        <Pie
          data={data}
          dataKey={dataKey}
          nameKey="name"
          cx="50%"
          cy="50%"
          outerRadius={100}
          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
        >
          {data.map((entry, i) => (
            <Cell key={i} fill={colors[entry.name] || colors[i % colors.length]} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 2 }}>
      <Typography variant="h4" gutterBottom fontWeight={700}>
        📊 Estatísticas
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        {data.total_pacientes} pacientes · {data.total_consultas} consultas registradas
      </Typography>

      <Grid container spacing={3}>
        {/* Sexo */}
        <Grid item xs={12} md={4}>
          <ChartCard title="🧑‍🤝‍🧑 Sexo">
            {data.sexo?.length > 0 ? (
              <PieChartView data={data.sexo} colors={GENDER_COLORS} />
            ) : (
              <Typography color="text.secondary">Sem dados</Typography>
            )}
          </ChartCard>
        </Grid>

        {/* Faixa Etária */}
        <Grid item xs={12} md={4}>
          <ChartCard title="📅 Faixa Etária">
            {data.faixa_etaria?.length > 0 ? (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={data.faixa_etaria}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#2D5A3D" radius={[4, 4, 0, 0]}>
                    {data.faixa_etaria.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <Typography color="text.secondary">Sem dados</Typography>
            )}
          </ChartCard>
        </Grid>

        {/* Consultas por Tipo */}
        <Grid item xs={12} md={4}>
          <ChartCard title="🩺 Consultas">
            {data.consultas_tipo?.length > 0 ? (
              <PieChartView data={data.consultas_tipo} colors={CONSULT_TIPO_COLORS} />
            ) : (
              <Typography color="text.secondary">Sem dados</Typography>
            )}
          </ChartCard>
        </Grid>

        {/* Cidades */}
        <Grid item xs={12} md={6}>
          <ChartCard title="🏙️ Cidades">
            {data.cidades?.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={data.cidades} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis type="category" dataKey="name" width={120} />
                  <Tooltip />
                  <Bar dataKey="value" fill="#1976D2" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <Typography color="text.secondary">Sem dados de localização</Typography>
            )}
          </ChartCard>
        </Grid>

        {/* Estados */}
        <Grid item xs={12} md={6}>
          <ChartCard title="🗺️ Estados">
            {data.estados?.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={data.estados} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis type="category" dataKey="name" width={60} />
                  <Tooltip />
                  <Bar dataKey="value" fill="#4CAF50" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <Typography color="text.secondary">Sem dados de localização</Typography>
            )}
          </ChartCard>
        </Grid>

        {/* Consultas por Mês */}
        <Grid item xs={12}>
          <ChartCard title="📈 Consultas por Mês (últimos 12 meses)">
            {data.consultas_mensal?.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={data.consultas_mensal}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="value"
                    name="Consultas"
                    stroke="#2D5A3D"
                    strokeWidth={2}
                    dot={{ r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <Typography color="text.secondary">Sem dados de consultas</Typography>
            )}
          </ChartCard>
        </Grid>
      </Grid>
    </Box>
  );
};

export default DashboardEstatisticas;
