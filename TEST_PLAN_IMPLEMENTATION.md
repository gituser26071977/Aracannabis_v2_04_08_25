# Plano de Testes - Sistema Aracannabis Prontuário Eletrônico

## Visão Geral
Este documento descreve o plano de testes abrangente para o sistema Aracannabis, incluindo testes funcionais, de segurança, performance e integração após as melhorias implementadas.

## 1. Ambiente de Testes

### 1.1 Configuração do Ambiente
- **Docker Environment**: Verificar funcionamento completo do docker-compose
- **Banco de Dados**: PostgreSQL com dados de teste
- **Frontend**: React application na porta 3000
- **Backend**: Flask API na porta 5002
- **Usuário de Teste**: admin / Aracannabis@2025

### 1.2 Dados de Teste
- Criar pelo menos 3 profissionais de saúde
- Criar 5-10 pacientes com dados completos
- Inserir dados de sintomas, dosagens e evoluções para cada paciente
- Upload de exames de imagem para testes de OCR

## 2. Testes de Segurança

### 2.1 Autenticação e Autorização
- [ ] Login com credenciais válidas
- [ ] Login com credenciais inválidas (usuário/senha incorretos)
- [ ] Tentativa de acesso sem token JWT
- [ ] Tentativa de acesso com token expirado
- [ ] Validação de força da senha no registro
- [ ] Sanitização de inputs (SQL injection, XSS)
- [ ] Rate limiting em endpoints de autenticação

### 2.2 Controle de Acesso
- [ ] Acesso a dados de outros profissionais
- [ ] Modificação de dados de outros profissionais
- [ ] Validação de permissões em todas as rotas protegidas

### 2.3 Segurança de Dados
- [ ] Criptografia de senhas (PBKDF2)
- [ ] Sanitização de dados de entrada
- [ ] Validação de formatos (CRM, email, etc.)
- [ ] Proteção contra CSRF
- [ ] Headers de segurança (CORS, HSTS)

## 3. Testes Funcionais

### 3.1 Gestão de Profissionais
- [ ] Cadastro de novo profissional
- [ ] Validação de CRM e UF
- [ ] Prevenção de CRM duplicado
- [ ] Edição de perfil profissional
- [ ] Alteração de senha

### 3.2 Gestão de Pacientes
- [ ] Cadastro de paciente com foto
- [ ] Upload e armazenamento de foto do paciente
- [ ] Exibição de avatar na lista de pacientes
- [ ] Validação de dados obrigatórios
- [ ] Edição de dados do paciente
- [ ] Exclusão de paciente

### 3.3 Gestão de Sintomas
- [ ] Cadastro de sintomas por paciente
- [ ] Visualização de gráficos de sintomas
- [ ] Filtros por período
- [ ] Exportação de dados

### 3.4 Gestão de Dosagens
- [ ] Cadastro de dosagens
- [ ] Validação de formatos numéricos
- [ ] Gráficos de dosagem
- [ ] Histórico de dosagens

### 3.5 Gestão de Exames
- [ ] Upload de imagem de exame
- [ ] Processamento OCR (placeholder)
- [ ] Cadastro manual de resultados
- [ ] Autocomplete de nomes de exames
- [ ] Geração de gráficos para valores numéricos
- [ ] Visualização de imagens

### 3.6 Gestão de Evoluções
- [ ] Cadastro de evoluções clínicas
- [ ] Associação com paciente
- [ ] Histórico cronológico

## 4. Testes de Integração

### 4.1 Frontend-Backend
- [ ] Comunicação via API REST
- [ ] Tratamento de erros HTTP
- [ ] Loading states
- [ ] Mensagens de erro amigáveis

### 4.2 Banco de Dados
- [ ] Conexão PostgreSQL
- [ ] Migrações de schema
- [ ] Integridade referencial
- [ ] Backup e restore

### 4.3 Upload de Arquivos
- [ ] Armazenamento seguro de fotos
- [ ] Validação de tipos de arquivo
- [ ] Limitação de tamanho
- [ ] Organização de diretórios

## 5. Testes de Performance

### 5.1 Carga
- [ ] Tempo de resposta das APIs (< 500ms)
- [ ] Carregamento do frontend (< 3s)
- [ ] Upload de arquivos (< 10s)
- [ ] Consultas ao banco (< 200ms)

### 5.2 Concorrência
- [ ] Múltiplos usuários simultâneos
- [ ] Operações de escrita concorrentes
- [ ] Lock de recursos

## 6. Testes de Usabilidade

### 6.1 Interface
- [ ] Navegação intuitiva
- [ ] Responsividade mobile/desktop
- [ ] Feedback visual para ações
- [ ] Validação em tempo real

### 6.2 Funcionalidades
- [ ] Fluxo completo de cadastro de paciente
- [ ] Processo de upload de exame
- [ ] Visualização de gráficos
- [ ] Exportação de relatórios

## 7. Testes de Regressão

### 7.1 Funcionalidades Existentes
- [ ] Login e autenticação
- [ ] CRUD básico de pacientes
- [ ] Gestão de consultas
- [ ] Relatórios existentes

### 7.2 Integrações
- [ ] Mercado Pago (se aplicável)
- [ ] Email service
- [ ] LGPD compliance

## 8. Estratégia de Execução

### 8.1 Fases de Teste
1. **Unidade**: Testes isolados de componentes
2. **Integração**: Testes de comunicação entre módulos
3. **Sistema**: Testes end-to-end
4. **Aceitação**: Testes com usuário final

### 8.2 Ferramentas
- **Backend**: pytest para testes unitários
- **Frontend**: Jest/React Testing Library
- **API**: Postman/Newman para testes de integração
- **Performance**: JMeter ou k6
- **E2E**: Cypress ou Selenium

### 8.3 Critérios de Aprovação
- Cobertura de código > 80%
- Zero falhas críticas
- Performance dentro dos limites
- Usabilidade aprovada

## 9. Plano de Contingência

### 9.1 Riscos Identificados
- Dependência de bibliotecas externas (OCR)
- Limitações de recursos do Docker
- Complexidade da integração frontend-backend

### 9.2 Mitigações
- Implementação gradual de funcionalidades
- Testes automatizados para regressão
- Documentação detalhada de APIs
- Backup de dados de teste

## 10. Métricas de Sucesso

- [ ] Todos os testes funcionais passando
- [ ] Cobertura de testes > 80%
- [ ] Tempo médio de resposta < 500ms
- [ ] Zero vulnerabilidades de segurança críticas
- [ ] Interface responsiva em todos os dispositivos
- [ ] Funcionalidades implementadas operacionais

## 11. Cronograma

### Semana 1: Preparação
- Configuração do ambiente de testes
- Criação de dados de teste
- Setup de ferramentas de teste

### Semana 2: Testes de Segurança
- Validação de autenticação
- Testes de autorização
- Auditoria de segurança

### Semana 3: Testes Funcionais
- Testes de todas as funcionalidades
- Validação de fluxos completos
- Testes de integração

### Semana 4: Performance e Usabilidade
- Testes de carga
- Validação de UX
- Otimizações

## 12. Responsabilidades

- **Desenvolvedor**: Correção de bugs identificados
- **QA**: Execução de testes e documentação
- **Product Owner**: Validação de requisitos
- **DevOps**: Manutenção do ambiente de testes

## 13. Relatórios de Teste

### 13.1 Formato dos Relatórios
- Status dos testes (Passou/Falhou/Bloqueado)
- Descrição detalhada de falhas
- Screenshots de problemas
- Logs de erro
- Métricas de performance

### 13.2 Frequência
- Diário: Status dos testes em andamento
- Semanal: Relatório consolidado
- Final: Relatório completo de aceitação