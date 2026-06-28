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
            if(process.env.NODE_ENV!=='production')console.error('Error fetching associations:', error);
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
            if(process.env.NODE_ENV!=='production')console.error('Error creating association:', error);
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
            if(process.env.NODE_ENV!=='production')console.error('Error fetching association details:', error);
            throw error;
        }
    },

    updateAssociation: async (id, data) => {
        try {
            const response = await api.put(`/association/associations/${id}`, data, {
                headers: getAssociationHeader()
            });
            return response.data;
        } catch (error) {
            if(process.env.NODE_ENV!=='production')console.error('Error updating association:', error);
            throw error;
        }
    },

    deleteAssociation: async (id) => {
        try {
            const response = await api.delete(`/association/associations/${id}`, {
                headers: getAssociationHeader()
            });
            return response.data;
        } catch (error) {
            if(process.env.NODE_ENV!=='production')console.error('Error deleting association:', error);
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
            if(process.env.NODE_ENV!=='production')console.error('Error fetching members:', error);
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
            if(process.env.NODE_ENV!=='production')console.error('Error adding member:', error);
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
            if(process.env.NODE_ENV!=='production')console.error('Error fetching stock:', error);
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
            if(process.env.NODE_ENV!=='production')console.error('Error adding stock:', error);
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
            if(process.env.NODE_ENV!=='production')console.error('Error fetching produtos:', error);
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
            if(process.env.NODE_ENV!=='production')console.error('Error dispensing item:', error);
            throw error;
        }
    }
};

export default associationService;
