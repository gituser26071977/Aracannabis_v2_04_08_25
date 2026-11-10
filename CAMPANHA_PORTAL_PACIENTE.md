# Campanha — Convite ao Portal do Paciente

Objetivo: informar os pacientes sobre o Portal do Paciente e ativar o acesso por
OTP no WhatsApp, respeitando consentimento e opt-out (LGPD).

- Portal: https://api.aracannabis.com.br/paciente
- Acesso: CPF + código enviado no WhatsApp
- Base atual (10/11/2026): 24 pacientes, 3 com WhatsApp, 17 com CPF, 2 com
  e-mail

## 1. Pré-requisitos (coleta de dados)

O login exige **CPF + WhatsApp**. Sem os dois, o paciente não entra.

1. Coletar **WhatsApp** e **CPF** na consulta/recepção (documento + confirmação
   do número com o paciente).
2. Registrar o consentimento de comunicação (ver seção 3).
3. Validar o número no WhatsApp antes de enviar (o script faz isso).

Planilha de pendências: gere a partir do banco (`id`, `nome`, o que falta) e use
como checklist na recepção.

## 2. Textos

### 2.1 WhatsApp — convite (principal)

> Olá, [Primeiro nome]! Aqui é do Instituto Vittalis. Seu **Portal do Paciente**
> está disponível: lá você consulta consultas, exames, documentos e receitas.
> Acesse: https://api.aracannabis.com.br/paciente — entre com seu CPF e receba
> um código no WhatsApp. Qualquer dúvida, fale com nossa equipe. Para não
> receber avisos, responda **SAIR**.

### 2.2 WhatsApp — lembrete (7 dias sem acesso)

> Olá, [Primeiro nome]! Passando para lembrar que seu Portal do Paciente está
> disponível em https://api.aracannabis.com.br/paciente. É só entrar com seu CPF
> e usar o código que chega no WhatsApp. Se tiver qualquer dificuldade, responda
> esta mensagem que a equipe te ajuda.

### 2.3 E-mail

Assunto: **Seu Portal do Paciente está disponível**

> Olá, [Nome]!
>
> Liberamos o **Portal do Paciente** do Instituto Vittalis. Nele você consulta
> suas consultas, exames, documentos e receitas, a qualquer momento.
>
> **Acesse:** https://api.aracannabis.com.br/paciente **Como entrar:** informe
> seu CPF e o código de acesso enviado no seu WhatsApp.
>
> Em caso de dúvidas, é só responder este e-mail. Para não receber avisos,
> responda com "SAIR".

### 2.4 Recepção / consulta (script presencial)

> Você já conhece o Portal do Paciente? Nele você vê seus exames, receitas e o
> histórico de consultas pelo celular. Para liberar, preciso confirmar seu CPF e
> seu WhatsApp. Você recebe um código e entra sozinho. Quer que eu já envie o
> convite agora?

Sugestão: cartaz/QR code na recepção com o link e o passo a passo (CPF →
código).

## 3. Consentimento e opt-out

- Colunas em `pacientes`:
  - `aceita_comunicacao_whatsapp` — `NULL` não informado, `true` autorizado,
    `false` recusado.
  - `opt_out_em`, `opt_out_motivo` — descadastro.
  - `convite_portal_enviado_em` — data do último convite.
- Endpoints (JWT de profissional):
  - `GET /api/lgpd/comunicacao/<paciente_id>`
  - `POST /api/lgpd/comunicacao/<paciente_id>`
    - `{"aceita_comunicacao_whatsapp": true}`
    - `{"opt_out": true, "opt_out_motivo": "pediu para não receber"}`
- Registro de envios: tabela `patient_convites` (canal, template, status, erro).

## 4. Envio em lote (script)

```bash
# Simulação (não envia nada)
python scripts/campanha_portal_paciente.py

# Enviar (padrão: só quem tem consentimento explícito)
python scripts/campanha_portal_paciente.py --enviar

# Primeiro contato de serviço para quem ainda não tem consentimento
python scripts/campanha_portal_paciente.py --enviar --incluir-sem-consentimento

# Pacientes específicos, intervalo maior
python scripts/campanha_portal_paciente.py --enviar --ids 9,24 --intervalo 60
```

O script:

1. seleciona pacientes ativos, com CPF e WhatsApp, sem opt-out;
2. valida os números na Evolution API (`checkNumbers`);
3. envia mensagem personalizada;
4. registra cada tentativa em `patient_convites`;
5. marca `convite_portal_enviado_em`.

## 5. Cadência e boas práticas

- **Não** fazer disparo em massa pela conexão atual (WhatsApp comum/Baileys):
  risco de bloqueio. Lotes pequenos (≤20), intervalo 30–60s, horário comercial.
- Personalize pelo primeiro nome; nunca inclua dado clínico na mensagem.
- Para volume alto, migrar para **WhatsApp Business API oficial com templates**.
- Garanta opt-out fácil ("responda SAIR") e respeite imediatamente.

## 6. Métricas

| Etapa     | Como medir                                     |
| --------- | ---------------------------------------------- |
| Cobertura | % de pacientes com CPF + WhatsApp              |
| Entrega   | `patient_convites.status = 'enviado'`          |
| Interesse | OTPs solicitados (`patient_otp`)               |
| Ativação  | 1º acesso (`pacientes.last_login_at`)          |
| Suporte   | Dúvidas/erros de login registrados pela equipe |
