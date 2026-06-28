import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';

const AssociationContext = createContext();

export const useAssociation = () => useContext(AssociationContext);

export const AssociationProvider = ({ children }) => {
    const [currentAssociation, setCurrentAssociation] = useState(null);
    const [userAssociations, setUserAssociations] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Carregar associações do usuário ao iniciar
        fetchUserAssociations();
    }, []);

    const fetchUserAssociations = async () => {
        // Prevent calling if not authenticated to avoid 401 loops
        const token = localStorage.getItem('token');
        if (!token) {
            setLoading(false);
            return;
        }

        try {
            // Endpoint to get associations the user belongs to
            // For now, let's assume getAssociations returns only allowed ones or create a specific endpoint
            // Adjusting to use associationService approach or dedicated endpoint
            const response = await api.get('/association/my-associations'); // Validar se esse endpoint existe ou criar
            setUserAssociations(response.data);

            // Restore from localStorage or default to first
            const storedId = localStorage.getItem('selectedAssociationId');
            if (storedId && response.data.length > 0) {
                const found = response.data.find(a => a.id === parseInt(storedId));
                if (found) {
                    setCurrentAssociation(found);
                } else {
                    // Se o ID salvo não existe nas associações do usuário, pega a primeira
                    setCurrentAssociation(response.data[0]);
                    localStorage.setItem('selectedAssociationId', response.data[0].id);
                }
            } else if (response.data.length > 0) {
                setCurrentAssociation(response.data[0]);
                localStorage.setItem('selectedAssociationId', response.data[0].id);
            }
        } catch (error) {
            if(process.env.NODE_ENV!=='production')console.error("Failed to fetch user associations", error);
            // If 401, we should probably stop trying and let the interceptor handle it, 
            // but for context loading via useEffect, we just log and stop.
        } finally {
            setLoading(false);
        }
    };

    const selectAssociation = (association) => {
        setCurrentAssociation(association);
        localStorage.setItem('selectedAssociationId', association.id);
        // Reload page to ensure all components and api instances update? 
        // Ideally just context update, but interceptor needs to pick it up.
        // window.location.reload(); // Hard reload might be safer for MVP isolation
        // Assuming interceptor reads from localStorage directly or we update api defaults.
    };

    return (
        <AssociationContext.Provider value={{ currentAssociation, userAssociations, selectAssociation, loading }}>
            {children}
        </AssociationContext.Provider>
    );
};
