# Task: Otimização Multi-tenant e Correção de Exclusão de Usuário

## Problema
1. Erro 500 ao tentar excluir um usuário via API administrativa.
2. Necessidade de otimizar o sistema para suporte completo a multi-tenancy (isolamento de dados).

## Análise
O erro 500 é causado por restrições de chave estrangeira (Foreign Key Constraints) que impedem a exclusão de um `Profissional` quando existem registros vinculados em tabelas como `Assinatura`, `SolicitacoesCadastro`, `AuditLog`, etc., que não possuem a diretiva `ondelete='CASCADE'` ou `ondelete='SET NULL'`.

A otimização multi-tenant exige que todas as consultas ao banco de dados sejam automaticamente filtradas pelo ID da associação atual (`associacao_id`), garantindo que um usuário de uma associação não veja dados de outra.

## Plano de Ação

### Fase 1: Correção do Erro 500 (Constraints)
- [ ] Atualizar `models.py`:
    - Adicionar `ondelete='CASCADE'` em `Assinatura.profissional_id`.
    - Adicionar `ondelete='CASCADE'` em `ReminderSettings.profissional_id`.
    - Adicionar `ondelete='SET NULL'` em `SolicitacoesCadastro.aprovado_por`.
- [ ] Atualizar `models_extra.py`:
    - Adicionar `ondelete='SET NULL'` em `PharmacyDispense.dispensado_por`.
    - Adicionar `ondelete='SET NULL'` em `AuditLog.user_id`.
- [ ] Refinar `routes/admin.py`:
    - Melhorar a lógica de `deletar_usuario` para tratar dependências remanescentes se necessário.

### Fase 2: Otimização Multi-tenant (Isolamento)
- [ ] Padronizar colunas:
    - Garantir que modelos críticos tenham `associacao_id`.
- [ ] Implementar Filtro Global em `tenant_lib.py`:
    - Completar o evento `before_compile` de SQLAlchemy para injetar filtros de `associacao_id` automaticamente baseado em `g.current_association`.
- [ ] Atualizar Segurança:
    - Modificar `admin_required` em `routes/admin.py` para verificar o papel do usuário dentro da associação (`g.user_role`) além do papel global.

### Fase 3: Verificação
- [ ] Testar exclusão de usuário com dependências.
- [ ] Verificar isolamento de dados entre diferentes associações.
