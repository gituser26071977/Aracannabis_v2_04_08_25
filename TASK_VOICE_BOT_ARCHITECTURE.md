# Task: Arquitetura Voice Bot Full-Duplex (Copilot Profissional)

## 🎯 Objetivo
Criar um assistente de voz bidirecional em tempo real (Full-Duplex) para profissionais de saúde no sistema Aracannabis, atuando como um "Mordomo Digital" mãos-livres durante consultas ou gestão de retaguarda.

## 🏗️ Arquitetura do Sistema (Visão Geral)

A integração do Gemini Live (Multimodal API via WebSockets) exige uma via de mão dupla constante de fluxo de áudio PCM. 

### 1. Frontend (React - Cliente)
- **Tecnologia:** React + Web Audio API + WebSockets.
- **Componente Principal:** `<LiveAudioCopilot />`
  - Um widget flutuante ou botão fixo no Dashboard do Profissional.
  - **Captura:** Acessa o microfone do dispositivo (ex: `navigator.mediaDevices.getUserMedia`) e utiliza um `AudioWorklet` (ou script processor) para capturar chunks de PCM linear (geralmente 16kHz, 16-bit mono) em tempo real.
  - **Transmissão:** Envia os chunks binários pelo WebSocket para o Backend.
  - **Recepção e Reprodução:** Recebe os chunks binários da fala da IA pelo mesmo WebSocket e os enfileira em um Buffer da Web Audio API para tocar fluidamente (áudio da resposta do assistente).
  - **Cancelamento (Interrupção):** Se o usuário falar sobre a IA, o Frontend (ou Backend) detecta a intenção e envia um sinal para interromper o áudio atual da IA, permitindo interações dinâmicas.

### 2. Backend (Flask / Python - Intermediário)
- **Tecnologia:** Flask-SocketIO ou FastAPI (WebSockets nativos), biblioteca `google-genai` (suporte ao Live API) ou integração via REST streaming se WebSockets puros não forem aplicáveis via WSGI. O ideal é usar `websockets` assíncrono.
- **Rota:** `wss://[domain]/api/voice-copilot`
- **Responsabilidades:**
  - Manter uma sessão persistente para cada tentativa de chamada de voz.
  - Repassar (Proxy) o PCM do Cliente para os servidores do Gemini (WSS da Google) mantendo a chave API segura.
  - Repassar as respostas de áudio emitidas pelo Gemini de volta para o Cliente.
  - **Injeção de Contexto (Ferramentas/Functions):** Chamar "Tools" (Function Calling). Se o usuário falar "Busque os dados do paciente X", o Gemini reconhece a intenção, dispara uma call para o backend buscar no banco (SQLAlchemy) e retornar os dados na mesma conexão, para o Gemini audivelizar a resposta.

### 3. Integração com IA (Google Gemini Live API)
- **Modelo Alvo:** `gemini-2.0-flash-exp` (habilitado para Live API multimodality).
- **Setup:** A conexão estabelece um `system_instruction` forte:
  - *"Você é o Aracannabis Copilot. Um assistente de voz estritamente profissional para médicos. Responda de forma extremamente curta e concisa, nunca listando pontos sem necessidade. Você pode realizar chamadas de funções no sistema."*
- **Capabilities (Tools Iniciais P0):**
  1. `buscar_paciente(nome_ou_id)` -> Retorna o sumário clínico do paciente no formato JSON para a IA ler.
  2. `salvar_evolucao(paciente_id, nota)` -> Cria uma nova Evolução no banco de dados baseado no que o médico ditou oralmente.
  3. `resumo_dia()` -> Retorna a agenda ou notificações de pacientes alertas.

---

## 🚀 Passos de Implementação (Roadmap)

### Fase 1: Prototipação do WebSocket + Audio (Backend)
- Criar pequeno serviço assíncrono (ex: novo arquivo `services/live_audio_server.py`) rodando com WebSockets independentes para não bloquear as threads do Flask puro (Gunicorn eventlet/gevent).
- Estabelecer túnel estático e conexão cliente WebSocket -> Servidor -> Gemini.
- Prova de conceito rodando um som "Hello" enviado para o Gemini e recebendo a voz do Gemini de volta e tocando no navegador.

### Fase 2: Interface Frontend Segura (Profissional)
- Implementar o componente `VoiceCopilotButton` no painel principal ou no Header (`<Header />`), mantendo ele em estado global (Zustand ou Context) para o áudio rolar navegando entre as abas.
- Tratar permissões de áudio no navegador e falhas de conexão WSS.

### Fase 3: Instrumentação do "Function Calling"
- Enganchar o backend com nossos serviços:
  - Serviço Paciente (Ler)
  - Serviço Evolução (Gravar)
- Traduzir a intenção em voz para modificação de banco de dados e confirmar audivelmente ("Pronto, Dr., evolução adicionada no prontuário do Joãozinho").

### Fase 4: Refinamento (Latência e Vozes)
- Otimizar o tamanho do chunk do WebAudio para o delay ficar < 500ms entre fala e resposta.
- Escolher as vozes padrões do Gemini mais agradáveis / humanas (Voices como *Aoede* ou *Puck*).

---
## Conclusão de Planejamento Inicial
Teremos um canal exclusivo e persistente de "rádio" (WebSocket) com a IA, permitindo uma comunicação natural enquanto o sistema traduz as falas em dados transacionais seguros no banco de dados.
