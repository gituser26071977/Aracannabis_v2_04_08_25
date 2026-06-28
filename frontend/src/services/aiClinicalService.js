import axios from 'axios';

// Usar a mesma configuração de base URL do api.js
const API_BASE_URL = process.env.REACT_APP_API_URL ? `${process.env.REACT_APP_API_URL}/api` : 'http://localhost:5002/api';

const api = axios.create({
    baseURL: API_BASE_URL,
});

api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export const aiClinicalService = {
    /**
     * Gera um resumo SOAP a partir de texto clínico.
     * @param {string} text - Texto clínico bruto.
     * @param {number} patientId - ID do paciente.
     * @param {number} consultationId - ID da consulta (opcional).
     * @param {string} task - Tarefa a ser executada ('soap_summary' default).
     * @returns {Promise<any>} - Retorna o JSON do SOAP gerado.
     */
    generateSoap: async (text, patientId, consultationId = null, task = 'soap_summary') => {
        try {
            const response = await api.post('/ai-clinical/generate-soap', {
                text,
                patient_id: patientId,
                consultation_id: consultationId,
                task
            });
            return response.data;
        } catch (error) {
            if(process.env.NODE_ENV!=='production')console.error('Erro na geração de IA Clínica:', error);
            throw error.response ? error.response.data : { error: 'Erro de conexão com serviço de IA' };
        }
    }
};
