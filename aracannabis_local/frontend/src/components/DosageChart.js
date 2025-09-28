import React from 'react';
import { Line } from 'react-chartjs-2';
import { Box, Typography, Alert } from '@mui/material';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

// Registrar componentes do Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const DosageChart = ({ dosages }) => {
  // Preparar dados para o gráfico com múltiplas linhas
  const prepareMultiLineChartData = () => {
    if (!dosages || dosages.length === 0) return null;

    // Ordenar dosagens por data para garantir ordem cronológica crescente
    const sortedDosages = [...dosages].sort((a, b) => {
      const dateA = new Date(a.data);
      const dateB = new Date(b.data);
      return dateA - dateB;
    });

    // Preparar dados para cada linha
    const labels = sortedDosages.map(d => {
      const date = new Date(d.data);
      return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
    });

    // Calcular doses diárias para cada dosagem
    const cbdData = [];
    const thcData = [];
    const cbgData = [];
    const cbnData = [];

    sortedDosages.forEach(dosage => {
      const gotasPorMl = dosage.gotas_por_ml || 30;
      const mlPorGota = gotasPorMl > 0 ? 1 / gotasPorMl : 0.033;
      const mlPorDose = (dosage.gotas || 0) * mlPorGota;
      const mlPorDia = mlPorDose * (dosage.frequencia_diaria || 1);

      cbdData.push((mlPorDia * (dosage.concentracao_cbd || 0)).toFixed(2));
      thcData.push((mlPorDia * (dosage.concentracao_thc || 0)).toFixed(2));
      cbgData.push((mlPorDia * (dosage.concentracao_cbg || 0)).toFixed(2));
      cbnData.push((mlPorDia * (dosage.concentracao_cbn || 0)).toFixed(2));
    });

    const datasets = [];

    // Linha CBD (Azul)
    if (cbdData.some(value => parseFloat(value) > 0)) {
      datasets.push({
        label: 'CBD (mg/dia)',
        data: cbdData.map(v => parseFloat(v)),
        borderColor: '#2196F3', // Azul
        backgroundColor: 'rgba(33, 150, 243, 0.1)',
        pointBackgroundColor: '#2196F3',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 6,
        pointHoverRadius: 8,
        tension: 0.3,
        borderWidth: 3,
        fill: false
      });
    }

    // Linha THC (Verde)
    if (thcData.some(value => parseFloat(value) > 0)) {
      datasets.push({
        label: 'THC (mg/dia)',
        data: thcData.map(v => parseFloat(v)),
        borderColor: '#4CAF50', // Verde
        backgroundColor: 'rgba(76, 175, 80, 0.1)',
        pointBackgroundColor: '#4CAF50',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 6,
        pointHoverRadius: 8,
        tension: 0.3,
        borderWidth: 3,
        fill: false
      });
    }

    // Linha CBG (Roxo) - se houver dados
    if (cbgData.some(value => parseFloat(value) > 0)) {
      datasets.push({
        label: 'CBG (mg/dia)',
        data: cbgData.map(v => parseFloat(v)),
        borderColor: '#9C27B0', // Roxo
        backgroundColor: 'rgba(156, 39, 176, 0.1)',
        pointBackgroundColor: '#9C27B0',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 6,
        pointHoverRadius: 8,
        tension: 0.3,
        borderWidth: 3,
        fill: false
      });
    }

    // Linha CBN (Laranja) - se houver dados
    if (cbnData.some(value => parseFloat(value) > 0)) {
      datasets.push({
        label: 'CBN (mg/dia)',
        data: cbnData.map(v => parseFloat(v)),
        borderColor: '#FF9800', // Laranja
        backgroundColor: 'rgba(255, 152, 0, 0.1)',
        pointBackgroundColor: '#FF9800',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 6,
        pointHoverRadius: 8,
        tension: 0.3,
        borderWidth: 3,
        fill: false
      });
    }

    return {
      labels,
      datasets
    };
  };

  // Configuração do gráfico
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          usePointStyle: true,
          padding: 20,
          font: {
            size: 14,
            weight: 'bold'
          }
        }
      },
      title: {
        display: true,
        text: '📊 Evolução dos Canabinoides ao Longo do Tempo',
        font: {
          size: 18,
          weight: 'bold'
        },
        padding: 20
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: 'white',
        bodyColor: 'white',
        borderColor: 'rgba(255, 255, 255, 0.2)',
        borderWidth: 1,
        cornerRadius: 8,
        displayColors: true,
        callbacks: {
          title: function(context) {
            return `Data: ${context[0].label}`;
          },
          label: function(context) {
            return `${context.dataset.label}: ${context.parsed.y} mg/dia`;
          },
          afterBody: function(context) {
            const dataIndex = context[0].dataIndex;
            const dosage = dosages[dataIndex];
            if (dosage) {
              return [
                `Produto: ${dosage.dosagem}`,
                `Gotas: ${dosage.gotas} x ${dosage.frequencia_diaria}/dia`
              ];
            }
            return [];
          }
        }
      }
    },
    scales: {
      y: {
        min: 0,
        title: {
          display: true,
          text: 'Dose Diária (mg)',
          font: {
            size: 14,
            weight: 'bold'
          }
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.1)'
        },
        ticks: {
          font: {
            size: 12,
            weight: 'bold'
          },
          callback: function(value) {
            return value + ' mg';
          }
        }
      },
      x: {
        title: {
          display: true,
          text: 'Período',
          font: {
            size: 14,
            weight: 'bold'
          }
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.1)'
        },
        ticks: {
          font: {
            size: 12,
            weight: 'bold'
          }
        }
      }
    },
    onClick: (event, elements) => {
      if (elements.length > 0) {
        const element = elements[0];
        const dataIndex = element.dataIndex;
        const dosage = dosages[dataIndex];
        
        if (dosage) {
          const date = new Date(dosage.data).toLocaleDateString('pt-BR');
          alert(`Data: ${date}\nProduto: ${dosage.dosagem}\nGotas: ${dosage.gotas} x ${dosage.frequencia_diaria}/dia`);
        }
      }
    },
    onHover: (event, elements) => {
      event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
    }
  };

  const chartData = prepareMultiLineChartData();

  if (!chartData || chartData.datasets.length === 0) {
    return (
      <Alert severity="info">
        Registre dosagens com concentrações de canabinoides para visualizar o gráfico de evolução.
      </Alert>
    );
  }

  return (
    <Box>
      <Typography 
        variant="body2" 
        color="text.secondary" 
        sx={{ mb: 2, fontStyle: 'italic' }}
      >
        🔵 CBD em azul | 🟢 THC em verde | 🟣 CBG em roxo | 🟠 CBN em laranja
        <br />
        Clique nos pontos para ver detalhes da dosagem.
      </Typography>
      <Box sx={{ height: 400, width: '100%' }}>
        <Line data={chartData} options={chartOptions} />
      </Box>
    </Box>
  );
};

export default DosageChart;
