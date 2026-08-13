import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { listarMinhas, indexarAssinaturasAtivas } from '../services/modulosService';

const ModulosContext = createContext(null);

export const useModulos = () => {
  const ctx = useContext(ModulosContext);
  if (!ctx) throw new Error('useModulos deve ser usado dentro de <ModulosProvider>');
  return ctx;
};

/**
 * Provê o estado das assinaturas de módulos do profissional logado.
 * Carrega /api/meus-modulos uma única vez e expõe:
 *   - loading: boolean
 *   - ativos:  { [slug]: assinatura } (apenas acesso ativo)
 *   - hasModulo(slug): boolean
 *   - refresh(): recarrega assinaturas (após trial/checkout)
 *
 * Base para o gate de funcionalidades por especialidade (ex.: prontuário
 * clínico base sempre disponível; cannabis-medicinal só com módulo ativo).
 */
export const ModulosProvider = ({ children }) => {
  const [loading, setLoading] = useState(true);
  const [ativos, setAtivos] = useState({});
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listarMinhas();
      setAtivos(indexarAssinaturasAtivas(data.assinaturas || []));
      setError(null);
    } catch (err) {
      setError(err.message || 'Falha ao carregar módulos');
      setAtivos({});
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const hasModulo = useCallback((slug) => Boolean(ativos[slug]), [ativos]);

  return (
    <ModulosContext.Provider value={{ loading, ativos, hasModulo, error, refresh: load }}>
      {children}
    </ModulosContext.Provider>
  );
};

export default ModulosProvider;
