# AraFlow — Visão do Produto

> **Status:** Fase 0 — Descoberta e Arquitetura
> **Versão:** 0.1.0
> **Data:** 2026-06-24
> **Autores:** Product Owner · UX Designer · Software Architect · Tech Lead

---

## 1. Resumo executivo

O **AraFlow** é um novo módulo do ecossistema **AraOS** dedicado à **Neuroregulação Digital baseada em evidências científicas**. Ele vai muito além de um simples timer de respiração: é uma **plataforma terapêutica digital** que combina **breathwork, meditação, música terapêutica, relaxamento guiado** e, em fases futuras, **biofeedback (HRV)** e **inteligência artificial personalizada**.

O AraFlow foi desenhado para apoiar o trabalho de **médicos, psicólogos, fisioterapeutas, terapeutas e pacientes** no tratamento complementar de condições como **ansiedade, insônia, dor crônica, burnout, TDAH, TEA, AH/SD (apneia/SAHOS)** e para promoção de **foco, relaxamento e bem-estar**.

---

## 2. Declaração de visão

> *"Tornar a regulação autonômica, emocional e atencional acessível a qualquer pessoa, em qualquer lugar, com a qualidade clínica que o cuidado humano exige."*

### 2.1 Missão

Democratizar o acesso a técnicas terapêuticas baseadas em evidências (breathwork, mindfulness, HRV biofeedback) por meio de uma plataforma digital integrada ao prontuário e à jornada clínica do AraOS.

### 2.2 Visão de futuro (5 anos)

Ser a plataforma de referência em neuroregulação digital na América Latina, recomendada por profissionais de saúde e usada por mais de 500 mil pacientes como complemento terapêutico prescrito.

---

## 3. Princípios norteadores

| # | Princípio | Descrição |
|---|-----------|-----------|
| 1 | **Medicina baseada em evidências** | Cada protocolo precisa ter base científica publicada e nível de evidência declarado. |
| 2 | **Segurança primeiro** | Contraindicações sempre visíveis. Em caso de dúvida, não iniciar. |
| 3 | **Simplicidade radical** | UX minimalista. Um botão de começar. Zero fricção. |
| 4 | **Integração clínica** | Tudo o que o paciente faz no AraFlow pode (com consentimento) ir para o prontuário. |
| 5 | **Personalização progressiva** | Começar genérico; tornar-se pessoal conforme o uso e os dados clínicos. |
| 6 | **Acessibilidade universal** | Funciona em qualquer dispositivo, mesmo offline. Acessível a pessoas com deficiência. |
| 7 | **Privacidade por padrão** | LGPD/GDPR by design. Telemetria mínima. Consentimento explícito. |

---

## 4. Problema a resolver

### 4.1 Contexto clínico

- **Ansiedade** é a condição de saúde mental mais prevalente do mundo (OMS, 2023). No Brasil, 86% da população relata algum grau de ansiedade.
- **Insônia crônica** afeta ~33% dos adultos brasileiros e é fator de risco para depressão, hipertensão e doenças cardiovasculares.
- **Burnout** foi reconhecido pela OMS como fenômeno ocupacional (CID-11: QD85).
- **Dor crônica** afeta 37% dos brasileiros e tem forte componente emocional/autonômico.
- **TDAH em adultos** é frequentemente subdiagnosticado; técnicas de respiração e foco são adjuvantes reconhecidos.
- **TEA (autismo)** frequentemente cursa com desregulação autonômica e sensorial.
- **AH/SD (apneia/SAHOS)** tem relação direta com técnicas respiratórias específicas.

### 4.2 Oferta atual (gap)

- **Apps de respiração genéricos** (pranayama, box breathing) — sem contexto clínico, sem personalização, sem integração com profissional de saúde.
- **Plataformas de mindfulness** (Headspace, Calm) — boas em UX, mas genéricas e desconectadas do cuidado clínico.
- **Plataformas clínicas** — quase inexistentes no Brasil; as poucas existentes não combinam breathwork + mindfulness + música terapêutica + biofeedback.

### 4.3 Oportunidade

Existe um espaço vazio entre **bem-estar genérico** e **terapia clínica** que pode ser preenchido por uma plataforma:

1. Com **protocolos clinicamente referendados**.
2. **Prescrita e acompanhada por profissional de saúde**.
3. **Integrada ao prontuário** do paciente.
4. **Personalizada por IA** com base em adesão, resposta e contexto clínico.

---

## 5. Proposta de valor

### 5.1 Para o paciente

> *"Tenha um spa terapêutico de bolso, com técnicas clinicamente validadas, que entende o que você sente e se adapta a você."*

- Redução mensurável de ansiedade, insônia e estresse.
- Sessões curtas (3 a 20 minutos) que cabem em qualquer rotina.
- Acompanhamento de progresso e insights personalizados.
- Prescrito por um profissional que acompanha de verdade.

### 5.2 Para o profissional de saúde

> *"Prescreva neuroregulação digital com a mesma facilidade com que prescreve um exercício físico."*

- Biblioteca de protocolos baseados em evidência.
- Prescrição personalizada (dose, frequência, ajuste por fase).
- Dashboard de adesão e resposta do paciente.
- Integração com prontuário e registro de evolução.

### 5.3 Para o AraOS

- Diferenciação competitiva: nenhum concorrente direto combina prontuário + IA + neuroregulação.
- Aumento do tempo de retenção do profissional (prescrição gera recorrência).
- Aumento do LTV do paciente (adesão melhora desfechos clínicos).
- Base para novos módulos (cardiologia, sono, dor, performance).

---

## 6. Diferenciais

| Diferencial | Descrição |
|-------------|-----------|
| **Clínico, não wellness** | Prescrito por profissional. Cada protocolo tem evidência e contraindicacao. |
| **Personalizado por IA** | Adapta dose, ritmo, conteúdo ao perfil e à resposta do paciente. |
| **Integrado ao AraOS** | Login, prontuário, agenda, analytics e IA compartilhados. |
| **Biofeedback opcional (futuro)** | HRV em tempo real para ajustar protocolo. |
| **Multimodal** | Respiração + meditação + música + visual + biofeedback. |
| **Offline-first** | Funciona sem internet; sincroniza quando possível. |

---

## 7. Não-objetivos (Fase 0)

Para manter foco, **não** estão no escopo do AraFlow:

- Diagnóstico médico automatizado.
- Substituição de psicoterapia ou tratamento farmacológico.
- Telemedicina síncrona (consulta por vídeo).
- Dispositivos médicos vestíveis próprios.
- Marketplace de conteúdo genérico de bem-estar.

---

## 8. Métricas de sucesso da Fase 0 (definição de norte)

Quando o AraFlow entrar em produção, as métricas-chave serão:

| Categoria | Métrica | Meta ano 1 |
|----------|---------|-----------|
| **Adoção** | Profissionais prescritores ativos | 500 |
| **Adoção** | Pacientes ativos mensais (MAU) | 5.000 |
| **Adesão** | Taxa de conclusão de sessões prescritas | ≥ 60% |
| **Eficácia clínica** | Redução média de GAD-7 em 8 semanas | ≥ 4 pontos |
| **Eficácia clínica** | Redução média de ISI em 8 semanas | ≥ 4 pontos |
| **Engajamento** | NPS do paciente | ≥ 50 |
| **Segurança** | Eventos adversos reportados | < 0,1% das sessões |
| **Técnico** | Latência P95 de início de sessão | < 2s |

---

## 9. Stakeholders

| Papel | Interesse |
|-------|-----------|
| **Médicos prescritores** | Ferramenta complementar ao tratamento. |
| **Psicólogos e terapeutas** | Exercício entre sessões. Apoio à regulação autonômica. |
| **Pacientes** | Autonomia, alívio, insights. |
| **Gestores do AraOS** | Diferenciação, retenção, receita recorrente. |
| **Reguladores (CFM, CFP, ANVISA)** | Segurança, evidência, LGPD. |
| **Pesquisadores acadêmicos** | Dados anonimizados para estudos (futuro). |

---

## 10. Riscos de visão

| Risco | Mitigação |
|-------|-----------|
| Ser visto como "mais um app de respiração" | Posicionamento clínico, prescrição, evidência. |
| Baixa adesão do paciente | UX simples, sessões curtas, IA personalizada, gamificação leve. |
| Resistência do profissional | Educação, biblioteca de protocolos, integração com prontuário. |
| Regulação de "software como dispositivo médico" | Classificar como "wellness device" no MVP; planejar ANVISA pós-MVP. |
| Privacidade / LGPD | Privacy by design, criptografia, consentimento granular. |

---

## 11. Marcos conceituais (alto nível)

```
Fase 0 (agora)        → Discovery + Arquitetura (este documento)
Fase 1                → MVP técnico (vide 18_MVP.md)
Fase 2                → Personalização + analytics clínico
Fase 3                → Biofeedback (HRV) + IA avançada
Fase 4                → Pesquisa clínica + certificação
```

---

## 12. Glossário essencial

| Termo | Significado |
|-------|-------------|
| **Breathwork** | Conjunto de técnicas de respiração com finalidade terapêutica. |
| **HRV** | Heart Rate Variability — variabilidade da frequência cardíaca, marcador de regulação autonômica. |
| **Neuroregulação** | Capacidade do sistema nervoso de se autorregular. |
| **AH/SD** | Apneia do sono / SAHOS. |
| **TEA** | Transtorno do Espectro Autista. |
| **TDAH** | Transtorno de Déficit de Atenção e Hiperatividade. |
| **Box breathing** | Respiração 4-4-4-4 (inspira, segura, expira, segura). |
| **Coerência cardíaca** | Estado de sincronia entre respiração, coração e variabilidade cardíaca. |
| **Pranayama** | Técnicas respiratórias do yoga. |
| **Vagal tone** | Atividade do nervo vago, indicador de regulação parassimpática. |

---

## 13. Próximos passos

1. Aprovar esta visão com stakeholders (médicos-âncora, psicólogos, gestores).
2. Concluir os 20 documentos restantes da Fase 0.
3. Validar com pelo menos 3 profissionais prescritores (entrevistas estruturadas).
4. Iniciar planejamento técnico da Fase 1 (MVP).

---

*"O AraFlow não vende bem-estar. Ele oferece uma ferramenta clínica de regulação do sistema nervoso, tão respeitável quanto uma escala diagnóstica ou um protocolo de reabilitação."*