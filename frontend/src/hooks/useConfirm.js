/**
 * useConfirm — Hook para confirmações destrutivas padronizadas.
 *
 * Substitui window.confirm() por Dialog MUI consistente com o design system.
 *
 * Uso:
 *   const { confirm, ConfirmDialog } = useConfirm();
 *   const ok = await confirm({
 *     title: 'Excluir paciente?',
 *     message: 'Esta ação não pode ser desfeita.',
 *     confirmLabel: 'Excluir',
 *     destructive: true,
 *   });
 *   if (ok) { ... }
 *
 *   return (<>...<ConfirmDialog /></>);
 */
import { useState, useCallback } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
} from '@mui/material';

export default function useConfirm() {
  const [state, setState] = useState({ open: false });

  const confirm = useCallback((options) => {
    return new Promise((resolve) => {
      setState({
        ...options,
        open: true,
        resolve,
      });
    });
  }, []);

  const handleClose = useCallback((result) => {
    state.resolve?.(result);
    setState({ open: false });
  }, [state]);

  const ConfirmDialog = () => (
    <Dialog
      open={state.open}
      onClose={() => handleClose(false)}
      maxWidth="xs"
      fullWidth
    >
      {state.title && <DialogTitle>{state.title}</DialogTitle>}
      {state.message && (
        <DialogContent>
          <DialogContentText>{state.message}</DialogContentText>
        </DialogContent>
      )}
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={() => handleClose(false)}>
          {state.cancelLabel || 'Cancelar'}
        </Button>
        <Button
          onClick={() => handleClose(true)}
          variant="contained"
          color={state.destructive ? 'error' : 'primary'}
          autoFocus
        >
          {state.confirmLabel || 'Confirmar'}
        </Button>
      </DialogActions>
    </Dialog>
  );

  return { confirm, ConfirmDialog };
}