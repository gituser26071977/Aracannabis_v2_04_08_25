import api from './api';

const getAssociationHeader = () => {
    const associationId = localStorage.getItem('selectedAssociationId');
    return associationId ? { 'X-Association-ID': associationId } : {};
};

const secretariaService = {
    /**
     * GET /api/secretaria/dashboard
     * Retorna cards de resumo para o dashboard da secretária.
     */
    getDashboard: async () => {
        try {
            const res = await api.get('/secretaria/dashboard', {
                headers: getAssociationHeader(),
            });
            return res.data;
        } catch (error) {
            console.error('Error fetching dashboard:', error);
            throw error;
        }
    },

    /**
     * GET /api/secretaria/agenda?data=YYYY-MM-DD
     * Retorna agenda completa de uma data (default: hoje).
     */
    getAgenda: async (data = null) => {
        try {
            const params = data ? `?data=${data}` : '';
            const res = await api.get(`/secretaria/agenda${params}`, {
                headers: getAssociationHeader(),
            });
            return res.data;
        } catch (error) {
            console.error('Error fetching agenda:', error);
            throw error;
        }
    },

    /**
     * POST /api/secretaria/consultas/<id>/checkin
     * Marca uma consulta como confirmada (check-in da secretária).
     */
    checkinConsulta: async (consultaId) => {
        try {
            const res = await api.post(
                `/secretaria/consultas/${consultaId}/checkin`,
                {},
                { headers: getAssociationHeader() }
            );
            return res.data;
        } catch (error) {
            console.error('Error checking in consulta:', error);
            throw error;
        }
    },

    /**
     * GET /api/secretaria/pacientes?q=...
     * Quick search de pacientes do tenant.
     */
    quickSearchPacientes: async (query) => {
        try {
            const res = await api.get(`/secretaria/pacientes?q=${encodeURIComponent(query)}`, {
                headers: getAssociationHeader(),
            });
            return res.data;
        } catch (error) {
            console.error('Error searching pacientes:', error);
            throw error;
        }
    },

    /**
     * GET /api/secretaria/pacientes?limit=&offset=
     * Lista pacientes do tenant.
     */
    listPacientes: async (params = {}) => {
        try {
            const qs = new URLSearchParams(params).toString();
            const url = `/secretaria/pacientes${qs ? `?${qs}` : ''}`;
            const res = await api.get(url, {
                headers: getAssociationHeader(),
            });
            return res.data;
        } catch (error) {
            console.error('Error listing pacientes:', error);
            throw error;
        }
    },
};

export default secretariaService;
