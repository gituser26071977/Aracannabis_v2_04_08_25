# PIPELINE DE IA CLÍNICA – ARACANABIS (VERSÃO CERTIFICÁVEL)

## 1. Princípios Arquiteturais (Security & Compliance by Design)

Antes do fluxo técnico, definimos os princípios norteadores para atender LGPD, ISO 27001 e SOC 2:

*   **Minimização de Dados**: Somente o mínimo necessário é enviado à LLM externa.
*   **Separação de Domínios**: PHI (dados sensíveis/Protected Health Information) nunca trafega fora do domínio controlado sem anonimização.
*   **Processamento em Camadas**: Transcrição (Local) → Anonimização → LLM → Reidratação.
*   **Logging Seguro**: Nenhum dado clínico bruto pode aparecer em logs de aplicação ou infraestrutura.
*   **Criptografia**:
    *   *Em trânsito*: TLS 1.3 obrigatório.
    *   *Em repouso*: AES-256 para banco de dados e backups.
    *   *Mapas de anonimização*: Criptografia de aplicação (Application Level Encryption) com chaves rotativas.

## 2. Arquitetura de Serviços

```mermaid
graph TD
    Client[Frontend (React)] -->|HTTPS| Backend[Backend Principal (FastAPI)]
    
    subgraph "Ambiente Seguro (Aracannabis Controlled)"
        Backend -->|Audio Stream| Transcriber[Transcription Service (Local Whisper)]
        Transcriber -->|Raw Text| Anonymizer[Anonymization Service]
        Anonymizer -->|Anonymized Text| Gateway[LLM Gateway]
        
        Gateway -->|Response| Validator[Rehydration + Validation]
        Validator -->|Sanitized Data| DB[(Banco de Dados)]
    end
    
    subgraph "External Providers"
        Gateway -->|TLS 1.3| LLM[External LLM (DeepSeek/GPT/etc)]
    end
```

### Componentes:
1.  **Transcription Service**: Processamento local (CPU/GPU) usando `faster-whisper`. Garante que o áudio da consulta nunca saia da infraestrutura.
2.  **Anonymization Service**: Motor de NLP para identificar e mascarar PII/PHI antes do envio para a IA.
3.  **LLM Gateway**: Ponto único de saída para IAs externas. Implementa Circuit Breaker, Rate Limiting e Auditoria.
4.  **Rehydration Service**: Recompõe a resposta da IA com os dados originais (se necessário) e valida a estrutura.

## 3. Pipeline Detalhada

### 🔵 ETAPA 1 — Transcrição Local
*   **Tecnologia**: `faster-whisper`
*   **Entrada**: Arquivo de áudio (WAV/MP3) ou stream
*   **Saída**: Texto bruto + Timestamps
*   **Segurança**: O áudio e o texto bruto **nunca** são persistidos em logs, apenas em armazenamento temporário volátil ou criptografado até o término do processamento.

### 🟡 ETAPA 2 — Anonimização (Nível Certificável)
Estratégia híbrida de detecção:
1.  **Regex Estruturado**: Padrões rígidos para CPF, Telefone, E-mail, Datas, Nº Prontuário.
2.  **NER (Named Entity Recognition)**: Uso de modelos (ex: spaCy `pt_core_news_lg`) para detectar PESSOA, LOCAL, ORGANIZAÇÃO.
3.  **Generalização Semântica**: Substituição de dados específicos por categorias genéricas (ex: "42 anos" -> "ADULTO_MEIA_IDADE").

**Fluxo de Dados**:
*   Entrada: "João da Silva, morador de São Paulo..."
*   Saída: "PACIENTE_01, morador de LOC_01..."
*   **Persistência**: O mapa de-para (`{'PACIENTE_01': 'João da Silva'}`) é salvo na tabela `anonymization_maps` com criptografia AES-256.

### 🟣 ETAPA 3 — LLM Gateway
*   **Função**: Abstração de provedores (DeepSeek, OpenAI, etc).
*   **Controles**:
    *   Logs sanitizados (apenas metadados: tokens, tempo, custo).
    *   Bloqueio de prompts que contenham padrões de PII não anonimizados (failsafe).

### 🟢 ETAPA 4 — Reidratação e Validação
*   Processo inverso da etapa 2, restaurando os dados originais na resposta gerada pela IA (ex: resumo clínico).
*   Validação de formato (JSON Schema enforcement) antes de salvar no prontuário.

## 4. Estrutura de Dados (Compliance)

### Tabela: `ai_requests` (Audit Log Técnico)
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | Identificador único |
| `consultation_id` | UUID | Vínculo com a consulta |
| `provider` | VARCHAR | Provedor usado (ex: 'openai') |
| `model` | VARCHAR | Modelo usado (ex: 'gpt-4') |
| `tokens_input` | INT | Qtd tokens entrada |
| `tokens_output` | INT | Qtd tokens saída |
| `processing_time_ms` | INT | Latência |
| `status` | VARCHAR | success/error |
| `created_at` | TIMESTAMP | Data/hora |

### Tabela: `ai_outputs` (Resultado Clínico)
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | Identificador |
| `request_id` | UUID | Link para o request |
| `soap_summary` | TEXT | Resumo SOAP gerado |
| `structured_data` | JSONB | Dados estruturados extraídos |
| `validation_hash` | VARCHAR | Hash para integridade |

### Tabela: `anonymization_maps` (Alta Segurança)
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | Identificador |
| `request_id` | UUID | Link para o request |
| `token` | VARCHAR | O token usado (ex: 'PACIENTE_01') |
| `original_value_encrypted` | TEXT | Valor original criptografado (AES-256) |
| `salt` | VARCHAR | Salt usado na criptografia |

### Tabela: `patient_consents` (LGPD)
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `patient_id` | INT | ID do paciente |
| `ai_processing_allowed` | BOOLEAN | Se permite uso de IA |
| `purpose` | VARCHAR | Finalidade (ex: 'transcricao_consulta') |
| `signed_at` | TIMESTAMP | Data do consentimento |
| `ip_address` | VARCHAR | IP de origem |

## 5. Implementação de Segurança

1.  **Segregação Multi-tenant**: Uso de `tenant_id` mandatório em todas as queries (RSL - Row Level Security).
2.  **Rotation Keys**: Chaves de criptografia dos mapas de anonimização devem ser rotacionadas periodicamente.
3.  **Audit Trail**: Toda leitura na tabela `anonymization_maps` gera um log de auditoria imutável.

## 6. Infraestrutura Recomendada
*   **Servidor Backend**: VPS 4 vCPU / 8GB RAM (API + Postgres).
*   **Processamento Local**: Máquina do profissional ou servidor local dedicado para rodar Whisper (transcrição) e spaCy (NER), evitando envio de áudio para nuvem.
