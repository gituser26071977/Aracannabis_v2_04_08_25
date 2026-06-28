/**
 * useRemember — persiste o "último valor" usado por chave (escopo: usuário logado).
 *
 * Por que existe:
 *   - Médicos re-digitam valores constantes a cada consulta:
 *     associação, gotás_por_ml, via_administracao, tipo_consulta, intensidade padrão...
 *   - Solução mais simples que mexer em backend: localStorage com prefixo por user.
 *
 * Como usar:
 *   const [value, setValue, resetValue] = useRemember('associacao', 'ABRACE');
 *
 *   // No submit:
 *   await save();
 *   setValue(newValue);  // persiste para o próximo uso
 *
 * Chave final no localStorage: `remember:${userId}:${key}`
 * Se não houver user, usa `remember:anon:${key}` (não conflita em logout/login).
 */
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';

const PREFIX = 'remember';

const storageKey = (userId, key) => `${PREFIX}:${userId || 'anon'}:${key}`;

export default function useRemember(key, defaultValue = null) {
  const { currentUser } = useAuth();
  const userId = currentUser?.id || currentUser?.uid || null;
  const sk = storageKey(userId, key);

  const [value, setValueInternal] = useState(() => {
    try {
      const stored = localStorage.getItem(sk);
      if (stored === null || stored === undefined) return defaultValue;
      // Tenta JSON parse para suportar arrays/objetos
      try {
        return JSON.parse(stored);
      } catch {
        return stored;
      }
    } catch {
      return defaultValue;
    }
  });

  // Re-hidrata se o user mudar (login/logout)
  useEffect(() => {
    try {
      const stored = localStorage.getItem(sk);
      if (stored === null || stored === undefined) {
        setValueInternal(defaultValue);
      } else {
        try {
          setValueInternal(JSON.parse(stored));
        } catch {
          setValueInternal(stored);
        }
      }
    } catch {
      setValueInternal(defaultValue);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sk]);

  const setValue = useCallback((newValue) => {
    setValueInternal(newValue);
    try {
      const serialized = typeof newValue === 'string' ? newValue : JSON.stringify(newValue);
      localStorage.setItem(sk, serialized);
    } catch {
      // localStorage cheio ou indisponível — silencioso
    }
  }, [sk]);

  const resetValue = useCallback(() => {
    setValueInternal(defaultValue);
    try {
      localStorage.removeItem(sk);
    } catch {
      // silencioso
    }
  }, [sk, defaultValue]);

  return [value, setValue, resetValue];
}
