// intelligentImportService.js — Wrapper axios para /api/intelligent-import
import api from './api';

const getAssocHeader = () => {
  const id = localStorage.getItem('selectedAssociationId');
  return id ? { 'X-Association-ID': id } : {};
};

const intelligentImportService = {
  /**
   * Lista intents suportados com schema (campos esperados por intent).
   * @returns {Promise<{success: boolean, intents: Array}>}
   */
  listIntents: async () => {
    const res = await api.get('/intelligent-import/options', {
      headers: getAssocHeader(),
    });
    return res.data;
  },

  /**
   * Envia um arquivo para análise. NÃO persiste — retorna preview estruturado.
   * @param {File} file
   * @param {string|null} intent Opcional: força um intent; senão autodetectado
   * @returns {Promise<{success, preview}>}
   */
  analyze: async (file, intent = null) => {
    const fd = new FormData();
    fd.append('file', file);
    if (intent) fd.append('intent', intent);
    const res = await api.post('/intelligent-import/analyze', fd, {
      headers: {
        ...getAssocHeader(),
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  /**
   * Aplica um preview já validado pelo usuário.
   * @param {string} intent
   * @param {Array} records
   * @returns {Promise<{success, intent, aplicados, vinculados, ignorados, warnings, invalid_skipped}>}
   */
  apply: async (intent, records) => {
    const res = await api.post(
      '/intelligent-import/apply',
      { intent, records },
      { headers: getAssocHeader() }
    );
    return res.data;
  },
};

export default intelligentImportService;
