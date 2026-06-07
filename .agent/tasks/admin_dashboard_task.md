# Implementation Plan - Admin Dashboard Enhancements

## User Objective
The user wants to enhance the Admin Dashboard to include:
1. Detailed User Management: View users, their plans, and subscription status.
2. Audit Trail: View recent user access and "logged in time".
3. Prepare for Payment System integration (Mercado Pago).

## Current State
- **Frontend**: `AdminPage.js` exists with tabs for Users, Stats, and Logs.
- **Backend**: `routes/admin.py` provides basic user list and stats. `models.py` has `Assinatura` and `Plano` models.
- **Mercado Pago**: Existing routes in `routes/mercadopago.py` suggest plans like `sem_ia` and `com_ia`.

## Implementation Steps

### 1. Backend Updates (`routes/admin.py`) 
- **Modify `/api/admin/usuarios`**:
    - Join `Profissional` with `Assinatura` and `Plano`.
    - Retrieve "Last Access" date from `LogAtividade`.
    - Calculate "Days Since Registration".
    - Return enhanced user object including: `plano_nome`, `status_assinatura`, `ultimo_acesso`, `dias_cadastro`.

### 2. Frontend Updates (`src/pages/AdminPage.js`)
- **Enhanced User Table**:
    - Add columns: "Plano", "Status", "Último Acesso".
    - Display "Tempo de Casa" (e.g., "Membro há 30 dias").
- **Audit Section**:
    - Improve "Logs de Atividade" readability.
    - Clarify that "Tempo Logado" refers to session duration or account age (we will show "Last Seen" for now as session tracking isn't fully implemented).

### 3. Verification
- Verify that the Admin Dashboard loads correctly.
- Verify that user plans are visible (even if null currently).
- Check that "Last Access" updates when a user performs an action.

## Questions for Next Steps
- Confirm if "Tempo Logado" implies real-time session tracking (requires WebSocket/Heartbeat) or just historical usage.
- Confirm Mercado Pago credentials for the next phase.
