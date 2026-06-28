/**
 * useFormShortcuts — atalhos de teclado globais para forms clínicos.
 *
 * Resolve:
 *   - Médico precisa parar de digitar, pegar o mouse, achar o botão "Salvar"
 *   - Atalhos não padronizados: alguns forms usam Ctrl+S, outros só click
 *   - Esc para cancelar diálogos era imprevisível
 *
 * Como usar dentro de um componente de form:
 *   useFormShortcuts({
 *     onSave: () => formRef.current?.requestSubmit(),
 *     onCancel: () => onClose?.(),
 *     enabled: open,        // desativa quando modal está fechado
 *   });
 *
 * Atalhos registrados:
 *   - Ctrl+S / Cmd+S → save
 *   - Ctrl+Enter / Cmd+Enter → save (alternativa, mais comum em textareas)
 *   - Esc → cancel
 *   - Ctrl+K / Cmd+K → focus na busca (se onSearch fornecido)
 */
import { useEffect } from 'react';

const isMac = typeof navigator !== 'undefined' && /Mac|iPod|iPhone|iPad/.test(navigator.platform);

export default function useFormShortcuts({ onSave, onCancel, onSearch, enabled = true }) {
  useEffect(() => {
    if (!enabled) return undefined;

    const handler = (e) => {
      const mod = isMac ? e.metaKey : e.ctrlKey;

      // Ctrl/Cmd + S → save
      if (mod && e.key === 's') {
        e.preventDefault();
        if (onSave) onSave();
        return;
      }

      // Ctrl/Cmd + Enter → save (comum em textareas)
      if (mod && e.key === 'Enter') {
        e.preventDefault();
        if (onSave) onSave();
        return;
      }

      // Esc → cancel (apenas se não estiver em input de busca)
      if (e.key === 'Escape' && !e.defaultPrevented) {
        if (onCancel) onCancel();
        return;
      }

      // Ctrl/Cmd + K → focus search
      if (mod && e.key === 'k') {
        e.preventDefault();
        if (onSearch) onSearch();
        return;
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [enabled, onSave, onCancel, onSearch]);
}
