/**
 * ModuleGate.jsx — Componente que renderiza `children` apenas se o profissional
 * logado tiver acesso ativo ao módulo identificado por `slug`.
 *
 * Uso:
 *   <ModuleGate slug="cannabis-medicinal" fallback={<UpgradeCard />}>
 *     <CannabisOnlyFeature />
 *   </ModuleGate>
 *
 * Props:
 *   slug:        string  — slug do módulo (ex.: "cannabis-medicinal")
 *   fallback:    node    — o que mostrar se sem acesso (default: null = esconde)
 *   forceRender: bool    — se true, ignora checagem (admin/dev)
 */
import React, { useEffect, useState, useCallback } from 'react';
import { listarMinhas, indexarAssinaturasAtivas } from '../services/modulosService';

export default function ModuleGate({ slug, fallback = null, forceRender = false, children }) {
  const [state, setState] = useState({ loading: true, hasAccess: false, error: null });

  const check = useCallback(async () => {
    if (forceRender) {
      setState({ loading: false, hasAccess: true, error: null });
      return;
    }
    try {
      const data = await listarMinhas();
      const ativos = indexarAssinaturasAtivas(data.assinaturas || []);
      setState({ loading: false, hasAccess: Boolean(ativos[slug]), error: null });
    } catch (err) {
      setState({ loading: false, hasAccess: false, error: err.message });
    }
  }, [slug, forceRender]);

  useEffect(() => {
    check();
  }, [check]);

  if (state.loading) return null;
  if (state.error) return null;
  if (!state.hasAccess) return fallback;
  return children;
}
