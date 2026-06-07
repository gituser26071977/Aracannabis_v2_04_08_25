# Task: Lançamento MVP (Early Adopters) - V1.0

## 🎯 Escopo do "Pronto para Venda" (MVP Final)
A estratégia do lançamento v1 será voltada a **early adopters** em ambiente **Hostinger controlado**, usando IA local (**Ollama** com LLMs leves e *prompts* restritivos/orientados a tarefas específicas). Todo o fluxo de cadastro e automação de prontuário foi definido.

## 📋 Funcionalidades Core (P0)

### 1. Cadastro e Integração de Médicos (Admin-Aprovado)
- **Status Anterior:** CFM Captcha bloqueava aprovação 100% autônoma.
- **Definição V1:** Cadastro via formulário -> Vai para painel da Administração -> Admin valida manual -> Aprova e libera sistema/gera credenciais.
- **Ação Restante:** Revisar fluxo `SolicitacoesCadastro` em `routes/cadastro_profissionais.py` e UI de Aprovação Administrativa para garantir que está sem falhas.

### 2. Cadastro Inteligente de Pacientes e Prontuários
- **Entrada Multimodal:** 
  - Captura de áudio para evoluções (já pré-existente, precisa validação).
  - Imagens + OCR (Docs de identidade, laudos, exames). 
- **Definição V1:** Subir documento/exame, passar por OCR, jogar texto extraído no modelo Ollama para formatar em JSON/dados estruturados e auto-preencher ou arquivar no prontuário do paciente.
- **Ação Restante:** Revisar/Integrar rota de OCR e Parsing com LLM. Garantir que as informações formatadas alimentam o prontuário.

### 3. Agente Conversacional (Follow-up)
- **Definição V1:** IA que consulta o contexto do paciente (diagnóstico, evolução e dosagens) para interações inteligentes de acompanhamento.
- **Ação Restante:** Verificar `routes/chat_paciente_routes.py` (se aplicável), e garantir que os prompts base para os agentes estejam restritivos para evitar tangentes e consumos altos de recursos de máquina na Hostinger.

### 4. Gráficos e Acompanhamento
- **Definição V1:** Visão gráfica de evolução clínica (sintomas vs. dosagens).
- **Ação Restante:** Garantir que front/back conectam através dos atributos de evolução de dosagens e sintomas numéricos.

### 5. Prescrições, Receitas e Relatórios Avancados
- **Definição V1:** Emissão formal de receitas (já mapeado no sistema base).
- **Inovação P0:** **Geração de Relatório Estruturado para Habeas Corpus Preventivo**. A IA deve consolidar diagnóstico, evolução clínica crônica e necessidade de canabinoides para base de HC do advogado do paciente.
- **Ação Restante:** Criar um template de prompt dedicado para o Agente gerar o "Relatório de Justificativa/HC" juntando dados históricos do pacote do paciente no prompt do modelo.

### 6. IA Local Controlada
- **Ambiente:** Servidor usando **Ollama** + modelos leves (ex: Llama3-8B ou Llama3.2-1B/3B, Gemma2) para processamento rápido na Hostinger com prompts muito objetivos.

---

## Plano de Execução Imediata (Próximos Passos):
1. **Auditoria de Código e Testes**: Rodamos a checagem geral com `.agent/scripts/checklist.py` que aponta para `python3` e ignora varreduras em pastas estáticas de `.venv`, otimizando a checagem de bugs na Hostinger. Corrigimos SyntaxErrors críticos (ex: `test_tenant_isolation.py`) e refatoramos importações desnecessárias.
2. **Revisão `cadastro_profissionais.py`**: O acesso ao fluxo com a aprovação inicial será via painel administrativo.
3. **Módulo de Habeas Corpus**: Foi configurado (em `services/hc_report_service.py`) para utilizar as LLMs da Zhipu AI (`glm-4-plus`, etc) como provedoras de inteligência padrão. Se a Zhipu falhar, o serviço tem um fallback garantido local para o `ollama_local` (com modelos testados como Llama 3.1) e não deixar o prontuário dependente de instabilidades de rede externa. O prompt foi mantido restrito (3 parágrafos diretos).
4. **Chat Simples Contextual e Automações Gerais (Follow-Up)**: O arquivo inicial `ai_chat_simples.py` e a ingestão de OCR (`routes/exames.py`) foram direcionados para o provedor `zhipu` por padrão para ganharmos com inteligência superior e menor custo de hardware na Hostinger, reservando os recursos locais para backup.
5. **Estratégia Backend e LLMs**: Ajustada no `.env` com parâmetros `DEFAULT_LLM_PROVIDER=zhipu` operando nativamente em Nuvem (via API) de alta performance e preservando a arquitetura local já testada/homologada em Ollama como retaguarda.

**Agentes em Ação:** `@orchestrator`, `@backend-specialist`, `@api-patterns`.
