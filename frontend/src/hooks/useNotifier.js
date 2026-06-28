import { useState, useCallback } from 'react';
import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';

/**
 * useNotifier — hook leve para feedback transitório (substitui alert()).
 *
 * Retorna:
 *   - notifier: função para disparar mensagens
 *   - <NotifierElement />: componente a renderizar 1× no JSX
 *
 * Suporta 4 severidades: 'success' (default), 'info', 'warning', 'error'.
 *
 * Uso:
 *   const { notify, NotifierElement } = useNotifier();
 *   const handleClick = () => {
 *     try {
 *       doSomething();
 *       notify('Salvo com sucesso!', 'success');
 *     } catch (e) {
 *       notify('Erro ao salvar. Tente novamente.', 'error');
 *     }
 *   };
 *   return (<>{NotifierElement()} ...</>);
 *
 * MISSÃO 12 — UI Credibility Hardening: substitui alert() do browser.
 */
export default function useNotifier() {
  const [snack, setSnack] = useState({ open: false, message: '', severity: 'success' });

  const notify = useCallback((message, severity = 'success') => {
    setSnack({ open: true, message, severity });
  }, []);

  const handleClose = (event, reason) => {
    if (reason === 'clickaway') return;
    setSnack((s) => ({ ...s, open: false }));
  };

  const NotifierElement = () => (
    <Snackbar
      open={snack.open}
      autoHideDuration={6000}
      onClose={handleClose}
      anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
    >
      <Alert onClose={handleClose} severity={snack.severity} variant="filled" sx={{ width: '100%' }}>
        {snack.message}
      </Alert>
    </Snackbar>
  );

  return { notify, NotifierElement };
}
