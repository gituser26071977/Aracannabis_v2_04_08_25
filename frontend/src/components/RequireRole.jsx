/**
 * RequireRole — Higher-Order Component para proteção de rotas por role.
 *
 * Renderiza children somente se o currentUser.role está na lista de allowed.
 * Caso contrário, redireciona para /dashboard com mensagem de erro.
 *
 * Uso:
 *   <RequireRole roles={['secretary', 'auxiliar', 'admin', 'manager']}>
 *     <SecretariaDashboardPage />
 *   </RequireRole>
 */
import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const RequireRole = ({ roles, children }) => {
    const { currentUser } = useAuth();
    const location = useLocation();

    if (!currentUser) {
        return <Navigate to="/login" replace state={{ from: location }} />;
    }

    if (!roles || roles.length === 0) {
        return children;
    }

    if (!roles.includes(currentUser.role)) {
        return <Navigate to="/dashboard" replace state={{ accessDenied: true }} />;
    }

    return children;
};

export default RequireRole;
