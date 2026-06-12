import api from './api';

const getAssociationHeader = () => {
    const associationId = localStorage.getItem('selectedAssociationId');
    return associationId ? { 'X-Association-ID': associationId } : {};
};

const associationService = {
    // --- Association Management ---
    getAssociations: async () => {
        try {
            const response = await api.get('/association/my-associations', {
                headers: getAssociationHeader()
            });
            return response.data;
        } catch (error) {
            console.error('Error fetching associations:', error);
            throw error;
        }
    },

    createAssociation: async (data) => {
        try {
            const response = await api.post('/association/associations', data, {
                headers: getAssociationHeader()
            });
            return response.data;
        } catch (error) {
            console.error('Error creating association:', error);
            throw error;
        }
    },

    getAssociationById: async (id) => {
        try {
            const response = await api.get(`/association/associations/${id}`, {
                headers: getAssociationHeader()
            });
            return response.data;
        } catch (error) {
            console.error('Error fetching association details:', error);
            throw error;
        }
    },

    /**
     * Convida um PROFISSIONAL para a instituição.
     */
    inviteProfessional: async (associationId, data) => {
        try {
            const response = await api.post(
                `/association/associations/${associationId}/professional-invites`,
                { ...data, invite_type: 'professional' },
                { headers: getAssociationHeader() }
            );
            return response.data;
        } catch (error) {
            console.error('Error inviting professional:', error);
            throw error;
        }
    },

    /**
     * Convida STAFF (secretária/gestor) para a instituição.
     * Aceita `role`: 'secretary' | 'manager' | 'admin'
     * Sem exigir CRM/conselho de classe.
     */
    inviteStaff: async (associationId, data) => {
        try {
            const response = await api.post(
                `/association/associations/${associationId}/professional-invites`,
                { ...data, invite_type: 'staff' },
                { headers: getAssociationHeader() }
            );
            return response.data;
        } catch (error) {
            console.error('Error inviting staff:', error);
            throw error;
        }
    },

    /**
     * Lista convites da instituição (profissionais e staff).
     * Filtros opcionais: { status, invite_type, email }
     */
    listInvites: async (associationId, filters = {}) => {
        try {
            const params = new URLSearchParams();
            if (filters.status) params.append('status', filters.status);
            if (filters.invite_type) params.append('invite_type', filters.invite_type);
            if (filters.email) params.append('email', filters.email);

            const qs = params.toString();
            const url = `/association/associations/${associationId}/professional-invites${qs ? `?${qs}` : ''}`;
            const response = await api.get(url, { headers: getAssociationHeader() });
            return response.data;
        } catch (error) {
            console.error('Error listing invites:', error);
            throw error;
        }
    },

    /**
     * Revoga um convite pendente (idempotente).
     */
    revokeInvite: async (inviteId) => {
        try {
            const response = await api.post(
                `/association/professional-invites/${inviteId}/revoke`,
                {},
                { headers: getAssociationHeader() }
            );
            return response.data;
        } catch (error) {
            console.error('Error revoking invite:', error);
            throw error;
        }
    },

    /**
     * Reenvia o email de um convite (se ainda válido).
     */
    resendInvite: async (inviteId) => {
        try {
            const response = await api.post(
                `/association/professional-invites/${inviteId}/resend`,
                {},
                { headers: getAssociationHeader() }
            );
            return response.data;
        } catch (error) {
            console.error('Error resending invite:', error);
            throw error;
        }
    },

    /**
     * Lookup público de convite pelo token (sem JWT).
     * Usado pela página /convite-staff/:token para pré-preencher o formulário.
     */
    getInviteByToken: async (token) => {
        try {
            const response = await api.get(`/association/professional-invites/${token}`);
            return response.data;
        } catch (error) {
            console.error('Error fetching invite by token:', error);
            throw error;
        }
    },

    // --- Member Management ---
    getMembers: async (associationId) => {
        try {
            const response = await api.get(`/association/associations/${associationId}/members`, {
                headers: getAssociationHeader()
            });
            return response.data;
        } catch (error) {
            console.error('Error fetching members:', error);
            throw error;
        }
    },

    addMember: async (associationId, data) => {
        try {
            const response = await api.post(`/association/associations/${associationId}/members`, data, {
                headers: getAssociationHeader()
            });
            return response.data;
        } catch (error) {
            console.error('Error adding member:', error);
            throw error;
        }
    },

    // --- Stock Management ---
    getStock: async (associationId) => {
        try {
            const response = await api.get(`/association/associations/${associationId}/stock`, {
                headers: getAssociationHeader()
            });
            return response.data;
        } catch (error) {
            console.error('Error fetching stock:', error);
            throw error;
        }
    },

    addStock: async (associationId, data) => {
        try {
            const response = await api.post(`/association/associations/${associationId}/stock`, data, {
                headers: getAssociationHeader()
            });
            return response.data;
        } catch (error) {
            console.error('Error adding stock:', error);
            throw error;
        }
    },

    // --- Produtos ---
    getProdutos: async () => {
        try {
            const response = await api.get('/produtos', {
                headers: getAssociationHeader()
            });
            return response.data;
        } catch (error) {
            console.error('Error fetching produtos:', error);
            throw error;
        }
    },

    // --- Dispensation ---
    dispenseItem: async (associationId, data) => {
        try {
            const response = await api.post(`/association/associations/${associationId}/dispense`, data, {
                headers: getAssociationHeader()
            });
            return response.data;
        } catch (error) {
            console.error('Error dispensing item:', error);
            throw error;
        }
    }
};

export default associationService;
