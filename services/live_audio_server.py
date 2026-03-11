import asyncio
import websockets
import os
import json
import logging
from google import genai
from google.genai import types

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('VoiceCopilot')

# Obter chave da variável de ambiente ou injetar para testes locais
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')

# Configuração do Gemini 2.0 Flash (Live API habilitada via genai)
client = genai.Client(api_key=GOOGLE_API_KEY)
MODEL = 'gemini-2.0-flash-exp'

# Cache global de arquivos PDF enviados pro Gemini pra nao ter que ler na hora do WebSocket_connect
global _GEMINI_KNOWLEDGE_FILES
if "_GEMINI_KNOWLEDGE_FILES" not in globals():
    try:
        from google.genai import types as genai_types
        _GEMINI_KNOWLEDGE_FILES = [genai_types.Part.from_uri(file_uri=f.uri, mime_type=f.mime_type) for f in client.files.list() if f.mime_type == 'application/pdf']
    except Exception as e:
        logger.error(f"Erro ler arquivos knowledge Gemini: {e}")
        _GEMINI_KNOWLEDGE_FILES = []

# Função assíncrona para gerenciar a ponte entre o Navegador (Cliente) e o Gemini (Servidor)
async def handle_client_connection(client_ws, path):
    logger.info(f"Nova conexão do cliente: {path}")
    
    # Opções do Assistente: Configurando a Persona do Copilot Profissional
    sys_instruct = (
        "Você é o Aracannabis Copilot, um assistente de voz especializado e médico/farmacêutico para prescritores. "
        "Baseie-se fortemente nos materiais técnicos e guidelines de dosagem/titulação fornecidos em PDF. "
        "Não use formatações como Markdown (asteriscos, negritos) pois a sua resposta será diretamente falada. "
        "Responda as dúvidas e seja muito direto na resposta."
    )
    
    parts = _GEMINI_KNOWLEDGE_FILES + [types.Part.from_text(text=sys_instruct)]

    config = types.LiveConnectConfig(
        system_instruction=types.Content(parts=parts),
        response_modalities=["AUDIO"], # Garantir que ele retorne ÁUDIO
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name="Aoede" # Voz amigável e limpa
                )
            )
        )
    )
    
    try:
        # Abre o túnel assíncrono pro Google Gemini
        async with client.aio.live.connect(model=MODEL, config=config) as gemini_ws:
            logger.info("Túnel com Gemini Live estabelecido.")

            # Task 1: Ler áudio do Frontend e enviar para o Gemini
            async def receive_from_client():
                try:
                    async for message in client_ws:
                        # Se for string (texto/comando JSON)
                        if isinstance(message, str):
                            data = json.loads(message)
                            if 'client_content' in data:
                                # Pode enviar texto de inicialização, por exemplo
                                await gemini_ws.send(input={"parts": [{"text": data['client_content']}]})
                        # Se for bytes (PCM audio) do microfone do celular do médico
                        else: 
                            await gemini_ws.send(input={"mime_type": "audio/pcm;rate=16000", "data": message})
                except websockets.exceptions.ConnectionClosed:
                    logger.info("Cliente fechou a conexão web.")
                except Exception as e:
                    logger.error(f"Erro ao receber do cliente: {e}")

            # Task 2: Ler respostas do Gemini e jogar p/ Frontend (Áudio ou Functions)
            async def receive_from_gemini():
                try:
                    async for response in gemini_ws.receive():
                        server_content = response.server_content
                        if server_content is not None:
                            model_turn = server_content.model_turn
                            if model_turn:
                                for part in model_turn.parts:
                                    # Se o Gemini mandou áudio
                                    if part.inline_data:
                                        # Enviar direto como bytes pro Frontend tocar no Speaker
                                        await client_ws.send(part.inline_data.data)
                                    # Se o Gemini mandou texto (transcrição do que ele falou)
                                    elif part.text:
                                        logger.info(f"Gemini Speech: {part.text}")
                                        status = json.dumps({"type": "text", "text": part.text})
                                        await client_ws.send(status)
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    logger.error(f"Erro ao ler do Gemini: {e}")

            # Rodar as duas pistas de ida e volta simultaneamente
            gather_params = asyncio.gather(receive_from_client(), receive_from_gemini())
            await gather_params

    except Exception as e:
        logger.error(f"Erro crítico no túnel Gemini: {e}")
    finally:
        logger.info("Conexão finalizada com sucesso.")

# Iniciar o servidor de WebSockets na porta 8765
async def main():
    async with websockets.serve(handle_client_connection, "0.0.0.0", 8765):
        logger.info("🚀 Voice Copilot Server rodando em ws://0.0.0.0:8765 ...")
        await asyncio.Future()  # Rodar para sempre

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Servidor desligado.")
