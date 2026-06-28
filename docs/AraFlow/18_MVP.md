# AraFlow — MVP (Minimum Viable Product)

> **Versão:** 0.1.0
> **Data:** 2026-06-24
> **Owner:** Product Owner + Tech Lead
>
> Este documento define **com precisão** o que entra e o que **não** entra no MVP do AraFlow.

---

## Sumário

1. Filosofia do MVP
2. Escopo funcional
3. Personas cobertas
4. Casos de uso cobertos
5. Protocolos clínicos (12)
6. Áudio (12 trilhas)
7. Visual respiratório
8. Modos especiais
9. Recursos profissionais
10. LGPD
11. Acessibilidade
12. Telemetria
13. Plataformas suportadas
14. Critérios de aceite do MVP
15. O que NÃO entra no MVP
16. Riscos conhecidos
17. Cronograma
18. Recursos necessários

---

## 1. Filosofia do MVP

> **MVP não é "mínimo possível". É "mínimo suficiente para validar valor clínico real, com segurança, sem causar dano".**

Princípios:

1. **Segurança clínica inegociável.**
2. **LGPD completo desde o dia 1.**
3. **Acessibilidade como piso, não como teto.**
4. **Curadoria clínica humana** (sem depender de IA generativa).
5. **UX simples a ponto de uma avó usar** (testado com idoso real).
6. **Funciona offline** (sessão inteira sem rede).
7. **Zero impacto** no AraOS.

---

## 2. Escopo funcional

### 2.1 Paciente

| Funcionalidade | Status |
|----------------|--------|
| Login via AraOS | ✅ MVP |
| Onboarding (objetivo + permissões) | ✅ MVP |
| Modo SOS (ansiedade aguda) | ✅ MVP |
| Modo Idoso (acessibilidade ampliada) | ✅ MVP |
| Modo Infantil (visual lúdico) | ✅ MVP |
| Sessão completa (visual + áudio) | ✅ MVP |
| Player offline | ✅ MVP |
| Histórico das últimas 30 sessões | ✅ MVP |
| Sumário de progresso (sessões, minutos, streak) | ✅ MVP |
| Streak simples | ✅ MVP |
| Mensagens calorosas de re-engajamento | ✅ MVP |
| Compartilhamento de relatório com profissional | ❌ Fase 2 |
| Escalas clínicas (GAD-7 etc.) | ❌ Fase 2 |
| Recomendações personalizadas | ❌ Fase 2 |
| Biofeedback | ❌ Fase 3 |
| Avatar / planta que cresce | ❌ Fase 2 |
| Missões semanais | ❌ Fase 2 |

### 2.2 Profissional

| Funcionalidade | Status |
|----------------|--------|
| Login via AraOS | ✅ MVP |
| Lista de pacientes com vínculo | ✅ MVP |
| Prescrição simples (1 protocolo + dose) | ✅ MVP |
| Visualização de adesão do paciente | ✅ MVP |
| Ajuste de prescrição | ❌ Fase 2 (somente encerrar no MVP) |
| Notas clínicas | ❌ Fase 2 |
| Escalas e insights | ❌ Fase 2 |
| Relatórios exportáveis | ❌ Fase 2 |

### 2.3 LGPD

| Funcionalidade | Status |
|----------------|--------|
| Consentimento granular (4 categorias) | ✅ MVP |
| Tela "Seus dados" | ✅ MVP |
| Exportação JSON | ✅ MVP |
| Solicitação de exclusão (60d carência) | ✅ MVP |
| Cancelamento de exclusão | ✅ MVP |
| Política de privacidade e termos | ✅ MVP |
| Consent log | ✅ MVP |
| RIPD | ✅ MVP |

---

## 3. Personas cobertas no MVP

### 3.1 Pacientes

| Persona | Coberta | Observação |
|---------|---------|------------|
| Carlos (adulto ansiedade + insônia) | ✅ Total | Persona primária |
| Bia (adolescente TDAH) | ✅ Total | Modo infantil |
| Sr. Antônio (idoso SAHOS) | ✅ Total | Modo idoso |
| Mariana (mãe TEA) | ✅ Parcial | Modo infantil; relatórios completos Fase 2 |
| Helena (enfermagem Burnout) | ✅ Total | Persona primária |

### 3.2 Profissionais

| Persona | Coberta | Observação |
|---------|---------|------------|
| Dra. Marina (médica) | ✅ Total | Persona primária |
| Dr. Rafael (psicólogo) | ✅ Total | Persona primária |
| Lúcia (fisioterapeuta) | ✅ Total | Persona primária |
| Dr. Pedro (sono) | ✅ Total | — |

### 3.3 Personas **não** totalmente cobertas no MVP

| Persona | Por quê | Próxima fase |
|---------|---------|---------------|
| João (TDAH adulto) | Gamificação avançada | Fase 2 |
| Pesquisador acadêmico | Dados pesquisa | Fase 3 |

---

## 4. Casos de uso cobertos

| UC | Caso | Cobertura |
|----|------|-----------|
| UC-01 | Reduzir ansiedade aguda (pico) | ✅ Total (SOS) |
| UC-02 | Melhorar qualidade do sono | ✅ Total (4-7-8, coerência, body scan) |
| UC-03 | Alívio de dor crônica | ✅ Parcial (sem biofeedback) |
| UC-04 | Burnout e estresse ocupacional | ✅ Total (coerência, diafragmática) |
| UC-05 | Suporte em uso de cannabis medicinal | ✅ Total (sugestão de coerência) |
| UC-06 | Pré-sono e apneia leve | ✅ Parcial (com aviso) |
| UC-07 | TEA — regulação sensorial | ✅ Total (modo infantil) |
| UC-08 | TDAH — foco e atenção | ✅ Total (modo infantil + box) |
| UC-09 | Foco para trabalho/estudo | ✅ Total (box, coerência) |
| UC-10 | Relaxamento geral / bem-estar | ✅ Total (body scan, diafragmática) |

---

## 5. Protocolos clínicos (12 do MVP)

> Detalhes completos em `07_BREATH_PROTOCOLS.md`.

1. **Box Breathing (4-4-4-4)** — ansiedade, foco. Nível B.
2. **4-7-8 (Andrew Weil)** — ansiedade, sono. Nível B.
3. **Coerência Cardíaca 5.5** — ansiedade, estresse. Nível B.
4. **Respiração Diafragmática** — ansiedade, dor, sono. Nível A.
5. **Nadi Shodhana (alternada)** — foco, equilíbrio. Nível B.
6. **Respiração 6-2-6 (intensa)** — energia, foco. Nível C (com aviso).
7. **Respiração Triangular (3-3-3)** — iniciação. Nível D.
8. **Papworth Modificada** — asma, ansiedade. Nível B.
9. **Buteyko Leve** — hiperventilação. Nível B.
10. **Suspiro Fisiológico** — ansiedade aguda. Nível B.
11. **Body Scan 10 min** — sono, dor. Nível A.
12. **SOS 60 segundos** — crise. Nível D.

---

## 6. Áudio (12 trilhas do MVP)

> Detalhes em `08_AUDIO_SYSTEM.md`.

| Trilha | Categoria | Duração |
|--------|-----------|---------|
| `calm-deepsleep-01` | Calma profunda | 30 min |
| `calm-deepsleep-02` | Calma profunda | 20 min |
| `calm-anxiety-01` | Calma média | 10 min |
| `calm-anxiety-02` | Calma média | 5 min |
| `focus-deep-01` | Foco suave | 20 min |
| `focus-deep-02` | Foco suave | 10 min |
| `morning-rise-01` | Energia suave | 5 min |
| `sleep-drone-01` | Drone contínuo | 30 min |
| `rain-light` | Paisagem (loop) | 60 min |
| `forest-soft` | Paisagem (loop) | 60 min |
| `ocean-far` | Paisagem (loop) | 60 min |
| `white-noise-soft` | Ruído (loop) | 60 min |

Narração:
- 1 voz feminina PT-BR (padrão).
- 3 frases gravadas (início, fases, encerramento).
- Body scan narrado (10 min).

---

## 7. Visual respiratório

| Visual | MVP | Observação |
|--------|-----|------------|
| Círculo respiratório | ✅ | Padrão |
| Pulmão | ❌ Fase 2 | — |
| Flor | ✅ Modo infantil | Simples |
| Onda | ❌ Fase 2 | — |
| Esfera | ❌ Fase 2 | — |
| Mandala | ❌ Fase 2 | — |
| Partículas | ❌ Fase 2 | — |

> MVP entrega **2 visuais**: círculo (padrão) + flor (modo infantil). Demais na Fase 2 com base em uso real.

---

## 8. Modos especiais

| Modo | MVP | Observação |
|------|-----|------------|
| SOS (ansiedade aguda) | ✅ | Acesso rápido |
| Modo Idoso | ✅ | Acessibilidade ampliada |
| Modo Infantil | ✅ | Visual lúdico + textos simples |
| Modo "Sem áudio" | ✅ | Acessibilidade |
| Modo "Sem animação" | ✅ | Acessibilidade |
| Modo Profundo (sessão) | ✅ | Visual fullscreen mínimo |

---

## 9. Recursos profissionais (MVP)

- Login via AraOS.
- Visualização de pacientes com vínculo ativo.
- Prescrição simples:
  - Selecionar paciente.
  - Selecionar protocolo.
  - Definir dose (1x, 2x, personalizado).
  - Definir horário(s).
  - Definir duração (14d, 30d, contínuo).
  - Notas livres (opcional).
- Encerramento de prescrição.
- Visualização de adesão (% das sessões concluídas).

> Sem dashboard clínico avançado. Sem escalas. Sem notas estruturadas. Sem relatórios exportáveis. (Tudo Fase 2.)

---

## 10. LGPD (MVP completo)

- Consentimento granular em 4 categorias.
- Tela "Seus dados" lista o que é coletado.
- Exportação JSON (todas as sessões + perfil).
- Exportação PDF (resumo legível).
- Solicitação de exclusão com 60 dias de carência.
- Cancelamento de exclusão.
- Política de privacidade e termos de uso.
- Consent log (auditoria).
- RIPD atualizado.
- DPO designado.

---

## 11. Acessibilidade (MVP)

- WCAG 2.1 AA nas 5 telas principais.
- Modo alto contraste.
- Tamanho de texto ajustável (A A A).
- Áreas de toque ≥ 44×44 px.
- Suporte a leitor de tela (VoiceOver, TalkBack).
- `prefers-reduced-motion` respeitado.
- Versão sem áudio.
- Versão sem animação.

---

## 12. Telemetria (MVP mínimo)

- Eventos de onboarding.
- Eventos de sessão (start, pause, complete, abort).
- Eventos de prescrição (created, ended).
- Eventos de consentimento.
- Telemetria técnica (crash, latência).
- Dashboard interno de uso e latência.

> Sem analytics clínicos (escalas). Sem ML.

---

## 13. Plataformas suportadas

| Plataforma | MVP | Observação |
|------------|-----|------------|
| Web (Chrome, Safari, Firefox, Edge) | ✅ | PWA |
| iOS 15+ (iPhone, iPad) | ✅ | PWA + opcional nativo |
| Android 10+ | ✅ | PWA + opcional nativo |
| Smartwatch | ❌ | Fase 3 |
| App nativo dedicado | ❌ | Fase 2 |

---

## 14. Critérios de aceite do MVP

O MVP será considerado pronto quando **todos** os itens abaixo forem verdadeiros:

### 14.1 Clínicos
- [ ] 12 protocolos revisados por pelo menos 1 profissional de cada categoria (médico, psicólogo, fisio).
- [ ] Cada protocolo tem ficha técnica completa (incluindo nível de evidência e referências).
- [ ] Pelo menos 1 consulta de validação com médico prescritor e 1 com psicólogo.

### 14.2 Produto
- [ ] Sessão completa (visual + áudio) funcional em iOS, Android e Web.
- [ ] Login via AraOS funcionando com 99% de sucesso.
- [ ] 5 telas principais validadas com teste de usabilidade.
- [ ] NPS de teste interno ≥ 50.

### 14.3 Profissionais
- [ ] Pelo menos 20 profissionais beta conseguem prescrever sem ajuda.
- [ ] Tempo médio para criar prescrição ≤ 90s.

### 14.4 LGPD
- [ ] Consentimento granular implementado e testado.
- [ ] Exportação e exclusão testadas em E2E.
- [ ] DPO aprovou RIPD.
- [ ] Auditoria externa de segurança OK (P0/P1 = 0).

### 14.5 Técnico
- [ ] Uptime ≥ 99% em beta.
- [ ] Latência P95 início de sessão < 2s.
- [ ] Crash-free sessions ≥ 99%.
- [ ] Lighthouse Performance ≥ 85 (PWA).
- [ ] Cobertura de testes ≥ 80%.

### 14.6 Acessibilidade
- [ ] Auditoria WCAG AA nas 5 telas principais.
- [ ] Testes com leitor de tela passando.

### 14.7 Segurança
- [ ] Pentest sem vulnerabilidades críticas.
- [ ] WAF + DDoS ativos.

### 14.8 Conteúdo
- [ ] 12 trilhas de áudio licenciadas e integradas.
- [ ] Narração PT-BR gravada e integrada.
- [ ] Documentação clínica revisada.

---

## 15. O que NÃO entra no MVP

> Lista explícita para evitar scope creep.

| Item | Por quê não |
|------|-------------|
| Escalas clínicas (GAD-7 etc.) | Requer validação de UX + revisão clínica; Fase 2. |
| ML / IA preditiva | Requer volume mínimo de dados; Fase 2. |
| Biofeedback (HRV) | Requer integração com hardware; Fase 3. |
| IA generativa | Risco clínico alto; Fase 3. |
| Pesquisa clínica integrada | Requer aprovação regulatória; Fase 3. |
| Internacionalização (EN, ES) | Apenas PT-BR no MVP. |
| App nativo dedicado | PWA suficiente. |
| Modo profundo expandido | Modo simplificado atende MVP. |
| Avatar / planta que cresce | Streak simples atende MVP. |
| Missões semanais | Fase 2. |
| Ranking entre amigos | Fase 3. |
| Marketplace de conteúdo | Fora de escopo. |
| Integração com smartwatches | Fase 3. |
| Marketplace de áudio | Fora de escopo. |
| Vídeos de meditação | Fora de escopo. |
| Consultas por vídeo | AraOS já tem. |
| Compra de bens / monetização | Fase 3+, com cuidado. |
| Notas clínicas estruturadas | Fase 2. |
| Relatórios PDF para profissional | Fase 2. |

---

## 16. Riscos conhecidos do MVP

| Risco | Mitigação |
|-------|-----------|
| Baixa adesão do paciente | UX simples; mensagem de re-engajamento. |
| Resistência do profissional | Onboarding com casos reais; biblioteca visível. |
| Bugs em offline | Testes E2E específicos; cache robusto. |
| Performance em device low-end | Visual conservador; testes em mid-range. |
| Conteúdo de áudio com qualidade variável | Curadoria + revisão de QA. |
| Erro de cálculo de tempo | Testes de borda + revisão. |
| Erro clínico em protocolo | Revisão por profissional + comitê. |
| Vazamento de dados | LGPD + DPO + auditoria. |
| Streak quebrando por bug | Tolerância de 4h; validação antes de salvar. |

---

## 17. Cronograma

| Semana | Marco |
|--------|-------|
| F0-S1 | Documentação aprovada |
| F0-S4 | Entrevistas com profissionais concluídas |
| F0-S8 | Personas e arquitetura validadas |
| F1-S1 | Kick-off técnico |
| F1-S4 | Backend MVP (auth + dados + prescrições) |
| F1-S8 | Player + visual + áudio integrados |
| F1-S10 | LGPD completo |
| F1-S12 | Acessibilidade + analytics |
| F1-S13 | Beta fechado (20 profissionais) |
| F1-S16 | Lançamento público |

---

## 18. Recursos necessários

| Recurso | Qtd |
|---------|-----|
| Product Owner | 1 |
| UX Designer | 1 |
| Engenheiro Backend | 2 |
| Engenheiro Frontend | 2 |
| Engenheiro QA | 1 |
| Designer Motion | 0.5 |
| Engenheiro DevOps | 0.3 |
| DPO | 0.3 |
| Diretor Clínico | 0.3 |
| Compositor (áudio) | pontual |
| Locutor (voz PT-BR) | pontual |
| Revisor clínico dos protocolos | pontual |

---

## 19. Decisões congeladas

A partir do kick-off do MVP, **decisões abaixo não mudam** sem aprovação formal do comitê:

1. Stack tecnológica do AraOS (alinhamento).
2. Conjunto dos 12 protocolos.
3. Conjunto das 12 trilhas de áudio.
4. Escopo de acessibilidade (WCAG AA).
5. Modelo de dados clínicos.
6. LGPD: 4 categorias de consentimento.
7. Janela de exclusão: 60 dias.
8. Classificação regulatória: software de bem-estar (MVP).

---

## 20. Comunicação de release

| Audiência | Mensagem |
|-----------|----------|
| Profissionais AraOS | E-mail + webinar de lançamento |
| Pacientes AraOS | Banner no app + push opcional |
| Imprensa médica | Press release com foco em evidência |
| Comunidade | Blog post + thread em canal |

---

*MVP é fundamento. Cuide dele.*