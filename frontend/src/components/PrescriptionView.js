import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';

const PrescriptionView = () => {
  const { consultaId } = useParams();
  const { currentUser } = useAuth();
  const [prescricao, setPrescricao] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchPrescricao = async () => {
      try {
        const response = await api.get(`/prescricao/${consultaId}`, {
          headers: {
            Authorization: `Bearer ${currentUser.token}`,
          },
        });
        setPrescricao(response.data);
      } catch (err) {
        setError('Erro ao carregar prescrição');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    if (currentUser) {
      fetchPrescricao();
    }
  }, [consultaId, currentUser]);

  const handlePrint = () => {
    window.print();
  };

  if (loading) return <div>Carregando...</div>;
  if (error) return <div>{error}</div>;
  if (!prescricao) return <div>Nenhuma prescrição encontrada</div>;

  return (
    <div className="prescription-container">
      <div className="print-header">
        <h1>Prescrição Médica</h1>
        <button onClick={handlePrint} className="print-button">
          Imprimir
        </button>
      </div>

      <div className="prescription-content">
        <div className="header">
          <div className="clinic-info">
            <h2>Clínica Aracannabis</h2>
            <p>Especializada em Cannabis Medicinal</p>
            <p>CNPJ: XX.XXX.XXX/0001-XX</p>
          </div>
          <div className="prescription-info">
            <p>Prescrição: #{prescricao.id}</p>
            <p>Data: {new Date(prescricao.data_consulta).toLocaleDateString()}</p>
          </div>
        </div>

        <div className="patient-info">
          <h3>Paciente</h3>
          <p><strong>Nome:</strong> {prescricao.paciente.nome}</p>
          <p><strong>Data Nasc.:</strong> {prescricao.paciente.data_nascimento}</p>
          <p><strong>CPF:</strong> {prescricao.paciente.cpf}</p>
        </div>

        <div className="professional-info">
          <h3>Profissional</h3>
          <p><strong>Nome:</strong> {prescricao.profissional.nome}</p>
          <p><strong>CRM:</strong> {prescricao.profissional.crm}</p>
        </div>

        <div className="medication-list">
          <h3>Medicação Prescrita</h3>
          <table>
            <thead>
              <tr>
                <th>Composição</th>
                <th>Dosagem</th>
              </tr>
            </thead>
            <tbody>
              {prescricao.composicao.map((item, index) => (
                <tr key={index}>
                  <td>{item.nome}</td>
                  <td>{item.dosagem}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {prescricao.observacoes && (
          <div className="observations">
            <h3>Observações</h3>
            <p>{prescricao.observacoes}</p>
          </div>
        )}

        <div className="signature">
          <p>_________________________________________</p>
          <p>Assinatura do Profissional</p>
        </div>
      </div>
    </div>
  );
};

export default PrescriptionView;

<style jsx>{`
  /* Estilos para tela */
  .prescription-container {
    max-width: 800px;
    margin: 20px auto;
    padding: 20px;
    background-color: white;
    box-shadow: 0 0 10px rgba(0,0,0,0.1);
  }
  
  .print-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }
  
  .print-button {
    background-color: #007bff;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 5px;
    cursor: pointer;
  }
  
  .header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 30px;
  }
  
  .patient-info, .professional-info {
    margin-bottom: 20px;
  }
  
  table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 20px;
  }
  
  th, td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
  }
  
  th {
    background-color: #f2f2f2;
  }
  
  .signature {
    margin-top: 50px;
    text-align: center;
  }
  
  /* Estilos específicos para impressão */
  @media print {
    body * {
      visibility: hidden;
    }
    
    .prescription-container, .prescription-container * {
      visibility: visible;
    }
    
    .prescription-container {
      position: absolute;
      left: 0;
      top: 0;
      width: 100%;
      box-shadow: none;
    }
    
    .print-button {
      display: none;
    }
  }
`}</style>
