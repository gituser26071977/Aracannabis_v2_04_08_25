import os
from crewai import Agent, Task, Crew, Process
from langchain_ollama import ChatOllama # Importação atualizada
from dotenv import load_dotenv
import json

# Importar as ferramentas de banco de dados
from services.db_tools import save_evolution_to_db, save_dosage_to_db

# Carregar variáveis de ambiente
load_dotenv()

from langchain_openai import ChatOpenAI # Adicionado para opção OpenAI
from langchain_groq import ChatGroq     # Adicionado para opção Groq

# Carregar variáveis de ambiente
load_dotenv()

# --- Configuração Dinâmica do LLM ---
DEFAULT_LLM_PROVIDER = os.getenv("DEFAULT_LLM_PROVIDER", "groq") # ollama, groq, openai. Mudado padrão para groq.

def get_llm(provider: str = None, model_name: str = None):
    """
    Retorna uma instância do LLM com base no provedor e nome do modelo.
    """
    provider = provider or DEFAULT_LLM_PROVIDER
    print(f"Tentando configurar LLM para o provedor: {provider}, Modelo: {model_name if model_name else 'padrão do provedor'}")

    if provider == "ollama":
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        # Modelo padrão para Ollama se não especificado, ou usa o model_name passado
        effective_model_name = model_name or os.getenv("OLLAMA_MODEL", "llama3:8b-instruct-q4_1")
        print(f"Usando Ollama: URL={ollama_base_url}, Modelo={effective_model_name}")
        return ChatOllama(
            base_url=ollama_base_url,
            model=effective_model_name,
            temperature=0.1,
        )
    elif provider == "groq":
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY não encontrada no .env para o provedor Groq.")
        # Modelo padrão para Groq se não especificado, ou usa o model_name passado
        effective_model_name = model_name or "llama3-8b-8192" 
        print(f"Usando Groq: Modelo={effective_model_name}")
        return ChatGroq(
            groq_api_key=groq_api_key,
            model_name=effective_model_name,
            temperature=0.1,
        )
    elif provider == "openai":
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY não encontrada no .env para o provedor OpenAI.")
        # Modelo padrão para OpenAI se não especificado, ou usa o model_name passado
        effective_model_name = model_name or "gpt-4-turbo-preview"
        print(f"Usando OpenAI: Modelo={effective_model_name}")
        return ChatOpenAI(
            openai_api_key=openai_api_key,
            model_name=effective_model_name,
            temperature=0.1,
        )
    else:
        raise ValueError(f"Provedor de LLM desconhecido: {provider}. Escolha entre 'ollama', 'groq', 'openai'.")

# A OPENAI_API_KEY ainda pode ser útil para transcrição de áudio/vídeo com Whisper
# Esta verificação é separada da seleção do LLM principal.
openai_api_key_for_whisper = os.getenv("OPENAI_API_KEY")
if not openai_api_key_for_whisper:
    print("AVISO: OPENAI_API_KEY não encontrada. Funcionalidades de transcrição com Whisper OpenAI não estarão disponíveis.")


# --- Agente Analista de Evolução Clínica (será instanciado dinamicamente) ---
# Não instanciamos mais o agente globalmente, pois o LLM pode mudar.

# --- Tarefas ---
# A definição da Task permanece a mesma, o agente será passado na hora.

# --- Tarefas ---

# Tarefa para o Analista de Evolução Clínica (VERSÃO SIMPLIFICADA PARA TESTE)
analyze_evolution_text_task_description = (
    "Resuma o seguinte texto em uma única frase: '{evolution_text}'.\n"
    "Retorne um JSON com a chave 'summary' contendo o resumo."
)

analyze_evolution_text_task_expected_output = (
    "Um objeto JSON contendo 'summary' (string).\n"
    "Exemplo: {\"summary\": \"O paciente disse oi.\"}"
)
# FIM DA VERSÃO SIMPLIFICADA PARA TESTE

# As ferramentas de banco de dados e o agente de banco de dados foram removidos deste arquivo,
# pois a interação com o BD será gerenciada diretamente pela rota Flask após a análise da IA.

# A função process_evolution_input agora aceita o provedor, nome do modelo e texto da imagem.
def process_evolution_input(
    evolution_text_input: str, 
    image_extracted_text: str = None, # Novo parâmetro
    llm_provider: str = None, 
    llm_model_name: str = None
) -> dict:
    """
    Processa o texto de entrada da evolução (e opcionalmente texto de imagem) usando a CrewAI.
    Retorna um dicionário com os dados estruturados.
    """
    selected_llm = get_llm(provider=llm_provider, model_name=llm_model_name)

    dynamic_evolution_analyst_agent = Agent(
        role="Analista de Evolução Clínica de Pacientes de Cannabis Medicinal",
        goal="Analisar o texto da evolução do paciente (e opcionalmente texto de imagem de rótulo) "
             "para extrair a descrição narrativa, identificar menções a dosagens (produto, quantidade, frequência, concentrações), "
             "ajustes de dosagem, e informações relevantes sobre a composição do produto.",
        backstory="Você é um especialista em analisar registros médicos de pacientes em tratamento com cannabis medicinal. "
                  "Sua principal habilidade é identificar com precisão informações cruciais sobre a evolução do tratamento, "
                  "focando em detalhes de dosagem, composição de produtos e feedback do paciente, considerando todas as fontes de texto fornecidas.",
        verbose=True,
        llm=selected_llm,
        allow_delegation=False
    )
    
    # Formatar a descrição da tarefa com os inputs disponíveis
    task_description_formatted = analyze_evolution_text_task_description.format(
        evolution_text=evolution_text_input,
        image_extracted_text=image_extracted_text if image_extracted_text else "Nenhum texto de imagem fornecido."
    )

    current_analyze_task = Task(
        description=task_description_formatted,
        expected_output=analyze_evolution_text_task_expected_output, 
        agent=dynamic_evolution_analyst_agent
    )

    analysis_crew = Crew(
        agents=[dynamic_evolution_analyst_agent],
        tasks=[current_analyze_task],
        process=Process.sequential,
        verbose=True # Alterado de 2 para True
    )

    # Não precisamos mais passar 'evolution_text' aqui se já está na descrição formatada.
    # No entanto, a CrewAI espera que os placeholders na descrição da task sejam preenchidos via inputs.
    # Vamos manter o input explícito para o placeholder '{evolution_text}' e adicionar '{image_extracted_text}'.
    analysis_inputs = {
        'evolution_text': evolution_text_input,
        'image_extracted_text': image_extracted_text if image_extracted_text else "N/A"
    }
    
    analysis_result_raw = ""
    analysis_result = {'narrative_evolution': evolution_text_input, 'dosage_info': None} # Padrão em caso de falha

    print(f"AI_AGENTS: Iniciando kickoff da crew com inputs: {analysis_inputs}")
    try:
        print(f"AI_AGENTS: ANTES do kickoff da crew.") # Novo Log
        analysis_result_raw = analysis_crew.kickoff(inputs=analysis_inputs)
        print(f"AI_AGENTS: DEPOIS do kickoff da crew.") # Novo Log
        print(f"AI_AGENTS: Resultado bruto do kickoff da crew: {analysis_result_raw}")
        print(f"AI_AGENTS: Tipo do resultado bruto: {type(analysis_result_raw)}")

        # Garantir que o resultado seja um dicionário
        if isinstance(analysis_result_raw, str):
            if not analysis_result_raw.strip(): # String vazia ou apenas espaços
                print("AI_AGENTS: Kickoff retornou string vazia. Usando input original.")
                analysis_result = {'narrative_evolution': evolution_text_input, 'dosage_info': None, 'warning': 'AI kickoff returned empty string'}
            else:
                try:
                    analysis_result = json.loads(analysis_result_raw)
                except json.JSONDecodeError as json_err:
                    print(f"AI_AGENTS: Erro ao decodificar JSON da IA: {json_err}")
                    print(f"AI_AGENTS: String JSON inválida: {analysis_result_raw}")
                    analysis_result = {'narrative_evolution': evolution_text_input, 'dosage_info': None, 'error': f'JSON decode error: {json_err}'}
        elif isinstance(analysis_result_raw, dict):
            analysis_result = analysis_result_raw
        else: 
            print(f"AI_AGENTS: Resultado inesperado da IA (tipo {type(analysis_result_raw)}): {analysis_result_raw}")
            analysis_result = {'narrative_evolution': evolution_text_input, 'dosage_info': None, 'error': f'Unexpected AI output type: {type(analysis_result_raw)}'}
            
    except Exception as e:
        import traceback
        print(f"AI_AGENTS: ERRO CRÍTICO ao executar a crew de análise: {str(e)}")
        print(f"AI_AGENTS: Traceback do erro da crew: {traceback.format_exc()}")
        # Retornar o texto original em caso de erro da crew
        analysis_result = {'narrative_evolution': evolution_text_input, 'dosage_info': None, 'error': f'Crew kickoff exception: {str(e)}'}
        
    print(f"AI_AGENTS: Resultado final da análise: {analysis_result}")
    return analysis_result


def process_import_data(text_content: str, patient_id: int, llm_provider: str = None, llm_model_name: str = None) -> dict:
    """
    Processa dados importados (CSV, TXT, etc.) usando IA para extrair informações estruturadas.
    """
    selected_llm = get_llm(provider=llm_provider, model_name=llm_model_name)

    import_analyst_agent = Agent(
        role="Analista de Importação de Dados Médicos",
        goal="Analisar texto importado para identificar e extrair informações sobre evoluções médicas, "
             "dosagens de cannabis medicinal, sintomas e outras informações clínicas relevantes.",
        backstory="Você é um especialista em análise de dados médicos importados. Sua função é identificar "
                  "diferentes tipos de informação (evoluções, dosagens, sintomas) e estruturá-las adequadamente "
                  "para inserção no sistema de prontuário eletrônico.",
        verbose=True,
        llm=selected_llm,
        allow_delegation=False
    )

    import_task_description = (
        "Analise o seguinte texto importado e identifique:\n"
        "1. Tipo de informação (evolução, dosagem, sintoma)\n"
        "2. Data (se mencionada)\n"
        "3. Detalhes específicos de cada tipo\n"
        "4. Extraia informações estruturadas\n\n"
        "Texto: '{text_content}'\n\n"
        "Retorne um JSON com:\n"
        "- 'tipo': 'evolucao', 'dosagem', 'sintoma' ou 'misto'\n"
        "- 'data': data no formato YYYY-MM-DD (ou null)\n"
        "- 'evolucoes': array de evoluções encontradas\n"
        "- 'dosagens': array de dosagens encontradas\n"
        "- 'sintomas': array de sintomas encontrados\n"
        "- 'confianca': nível de confiança da análise (0-100)"
    )

    import_task_expected_output = (
        "JSON estruturado com as informações extraídas:\n"
        "{\n"
        "  'tipo': 'string',\n"
        "  'data': 'YYYY-MM-DD ou null',\n"
        "  'evolucoes': [{'descricao': 'string', 'observacoes': 'string'}],\n"
        "  'dosagens': [{'produto': 'string', 'gotas': int, 'frequencia': int, 'cbd': float, 'thc': float}],\n"
        "  'sintomas': [{'sintoma': 'string', 'intensidade': int, 'observacoes': 'string'}],\n"
        "  'confianca': int\n"
        "}"
    )

    import_task = Task(
        description=import_task_description.format(text_content=text_content),
        expected_output=import_task_expected_output,
        agent=import_analyst_agent
    )

    import_crew = Crew(
        agents=[import_analyst_agent],
        tasks=[import_task],
        process=Process.sequential,
        verbose=True
    )

    try:
        result_raw = import_crew.kickoff(inputs={'text_content': text_content})
        
        if isinstance(result_raw, str):
            try:
                result = json.loads(result_raw)
            except json.JSONDecodeError:
                result = {
                    'tipo': 'evolucao',
                    'data': None,
                    'evolucoes': [{'descricao': text_content, 'observacoes': ''}],
                    'dosagens': [],
                    'sintomas': [],
                    'confianca': 50,
                    'error': 'Falha na análise da IA'
                }
        else:
            result = result_raw

        return result

    except Exception as e:
        print(f"Erro na análise de importação: {str(e)}")
        return {
            'tipo': 'evolucao',
            'data': None,
            'evolucoes': [{'descricao': text_content, 'observacoes': ''}],
            'dosagens': [],
            'sintomas': [],
            'confianca': 0,
            'error': str(e)
        }

def chat_with_data(question: str, context: dict, llm_provider: str = None, llm_model_name: str = None) -> dict:
    """
    Permite conversar com os dados do paciente usando IA.
    """
    selected_llm = get_llm(provider=llm_provider, model_name=llm_model_name)

    chat_agent = Agent(
        role="Assistente Médico Especializado em Cannabis Medicinal",
        goal="Responder perguntas sobre os dados do paciente de forma precisa e útil, "
             "fornecendo insights baseados no histórico de evoluções, dosagens e sintomas.",
        backstory="Você é um assistente médico especializado em cannabis medicinal com acesso "
                  "aos dados completos do paciente. Você pode analisar padrões, tendências e "
                  "fornecer insights valiosos sobre o tratamento baseado no histórico disponível.",
        verbose=True,
        llm=selected_llm,
        allow_delegation=False
    )

    # Preparar contexto formatado
    context_text = f"""
    DADOS DO PACIENTE:
    Nome: {context['paciente']['nome']}
    Condição Médica: {context['paciente']['condicao_medica']}
    
    EVOLUÇÕES RECENTES:
    {json.dumps(context['evolucoes'], indent=2, ensure_ascii=False)}
    
    DOSAGENS RECENTES:
    {json.dumps(context['dosagens'], indent=2, ensure_ascii=False)}
    
    SINTOMAS RECENTES:
    {json.dumps(context['sintomas'], indent=2, ensure_ascii=False)}
    """

    chat_task_description = (
        "Com base nos dados do paciente fornecidos, responda à seguinte pergunta de forma "
        "precisa e útil:\n\n"
        "PERGUNTA: {question}\n\n"
        "CONTEXTO DOS DADOS:\n{context_text}\n\n"
        "Forneça uma resposta detalhada que:\n"
        "1. Responda diretamente à pergunta\n"
        "2. Cite dados específicos quando relevante\n"
        "3. Identifique padrões ou tendências\n"
        "4. Forneça insights médicos quando apropriado\n"
        "5. Sugira próximos passos se relevante\n\n"
        "Retorne um JSON com:\n"
        "- 'resposta': resposta principal\n"
        "- 'dados_citados': dados específicos mencionados\n"
        "- 'insights': insights adicionais\n"
        "- 'sugestoes': sugestões para o tratamento"
    )

    chat_task_expected_output = (
        "JSON com resposta estruturada:\n"
        "{\n"
        "  'resposta': 'string com resposta principal',\n"
        "  'dados_citados': ['lista de dados específicos citados'],\n"
        "  'insights': ['lista de insights identificados'],\n"
        "  'sugestoes': ['lista de sugestões para o tratamento']\n"
        "}"
    )

    chat_task = Task(
        description=chat_task_description.format(question=question, context_text=context_text),
        expected_output=chat_task_expected_output,
        agent=chat_agent
    )

    chat_crew = Crew(
        agents=[chat_agent],
        tasks=[chat_task],
        process=Process.sequential,
        verbose=True
    )

    try:
        result_raw = chat_crew.kickoff(inputs={'question': question, 'context_text': context_text})
        
        if isinstance(result_raw, str):
            try:
                result = json.loads(result_raw)
            except json.JSONDecodeError:
                result = {
                    'resposta': result_raw,
                    'dados_citados': [],
                    'insights': [],
                    'sugestoes': [],
                    'error': 'Resposta não estruturada'
                }
        else:
            result = result_raw

        return result

    except Exception as e:
        print(f"Erro no chat com dados: {str(e)}")
        return {
            'resposta': f"Desculpe, ocorreu um erro ao processar sua pergunta: {str(e)}",
            'dados_citados': [],
            'insights': [],
            'sugestoes': [],
            'error': str(e)
        }

def process_pdf_file(pdf_file_path: str, llm_provider: str = None, llm_model_name: str = None) -> dict:
    """
    Processa arquivo PDF extraindo texto e analisando com IA.
    """
    try:
        text_content = ""
        
        # Tentar com PyMuPDF primeiro (melhor para PDFs complexos)
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(pdf_file_path)
            for page in doc:
                text_content += page.get_text()
            doc.close()
        except ImportError:
            # Fallback para PyPDF2
            try:
                import PyPDF2
                with open(pdf_file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text_content += page.extract_text()
            except ImportError:
                return {
                    'error': 'Bibliotecas PyMuPDF ou PyPDF2 não instaladas. Use: pip install PyMuPDF PyPDF2',
                    'source': 'pdf'
                }
            except Exception as e:
                return {
                    'error': f'Erro ao extrair texto do PDF: {str(e)}',
                    'source': 'pdf'
                }
        except Exception as e:
            return {
                'error': f'Erro ao processar PDF: {str(e)}',
                'source': 'pdf'
            }
        
        if not text_content.strip():
            return {
                'error': 'Não foi possível extrair texto do PDF',
                'source': 'pdf'
            }
        
        # Processar texto extraído com IA
        result = process_evolution_input(
            evolution_text_input=text_content,
            llm_provider=llm_provider,
            llm_model_name=llm_model_name
        )
        
        result['extracted_text'] = text_content
        result['source'] = 'pdf'
        
        return result
        
    except Exception as e:
        return {
            'error': f'Erro ao processar PDF: {str(e)}',
            'extracted_text': '',
            'source': 'pdf'
        }

def process_document_file(doc_file_path: str, llm_provider: str = None, llm_model_name: str = None) -> dict:
    """
    Processa arquivos de documento (DOC, DOCX, RTF, etc.) extraindo texto e analisando com IA.
    """
    try:
        text_content = ""
        file_extension = doc_file_path.lower().split('.')[-1]
        
        if file_extension == 'docx':
            # Processar DOCX
            try:
                import docx
                doc = docx.Document(doc_file_path)
                for paragraph in doc.paragraphs:
                    text_content += paragraph.text + '\n'
            except ImportError:
                return {
                    'error': 'Biblioteca python-docx não instalada. Use: pip install python-docx',
                    'source': 'document'
                }
            except Exception as e:
                return {
                    'error': f'Erro ao processar DOCX: {str(e)}',
                    'source': 'document'
                }
                
        elif file_extension == 'doc':
            # Para DOC, tentar usar python-docx2txt ou antiword
            try:
                import docx2txt
                text_content = docx2txt.process(doc_file_path)
            except ImportError:
                try:
                    import subprocess
                    result = subprocess.run(['antiword', doc_file_path], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        text_content = result.stdout
                    else:
                        return {
                            'error': 'Não foi possível processar arquivo DOC. Instale docx2txt ou antiword.',
                            'source': 'document'
                        }
                except:
                    return {
                        'error': 'Não foi possível processar arquivo DOC. Formato não suportado.',
                        'source': 'document'
                    }
                    
        elif file_extension == 'rtf':
            # Para RTF, usar striprtf
            try:
                from striprtf.striprtf import rtf_to_text
                with open(doc_file_path, 'r', encoding='utf-8') as file:
                    rtf_content = file.read()
                text_content = rtf_to_text(rtf_content)
            except ImportError:
                return {
                    'error': 'Biblioteca striprtf não instalada. Use: pip install striprtf',
                    'source': 'document'
                }
            except Exception as e:
                return {
                    'error': f'Erro ao processar RTF: {str(e)}',
                    'source': 'document'
                }
                
        elif file_extension in ['odt', 'ods', 'odp']:
            # Para documentos OpenDocument
            try:
                import zipfile
                from xml.etree import ElementTree
                with zipfile.ZipFile(doc_file_path, 'r') as zip_file:
                    content_xml = zip_file.read('content.xml')
                    root = ElementTree.fromstring(content_xml)
                    # Extrair texto de elementos de parágrafo
                    for elem in root.iter():
                        if elem.text:
                            text_content += elem.text + ' '
            except Exception as e:
                return {
                    'error': f'Erro ao processar documento OpenDocument: {str(e)}',
                    'source': 'document'
                }
        else:
            return {
                'error': f'Formato de documento não suportado: {file_extension}',
                'source': 'document'
            }
        
        if not text_content.strip():
            return {
                'error': 'Não foi possível extrair texto do documento',
                'source': 'document'
            }
        
        # Processar texto extraído com IA
        result = process_evolution_input(
            evolution_text_input=text_content,
            llm_provider=llm_provider,
            llm_model_name=llm_model_name
        )
        
        result['extracted_text'] = text_content
        result['source'] = 'document'
        
        return result
        
    except Exception as e:
        return {
            'error': f'Erro ao processar documento: {str(e)}',
            'extracted_text': '',
            'source': 'document'
        }

def process_text_file(text_file_path: str, llm_provider: str = None, llm_model_name: str = None) -> dict:
    """
    Processa arquivos de texto simples com diferentes codificações.
    """
    try:
        text_content = ""
        
        # Tentar diferentes codificações
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(text_file_path, 'r', encoding=encoding) as file:
                    text_content = file.read()
                break
            except UnicodeDecodeError:
                continue
        
        if not text_content:
            return {
                'error': 'Não foi possível ler o arquivo de texto com nenhuma codificação suportada',
                'source': 'text'
            }
        
        # Processar texto com IA
        result = process_evolution_input(
            evolution_text_input=text_content,
            llm_provider=llm_provider,
            llm_model_name=llm_model_name
        )
        
        result['extracted_text'] = text_content
        result['source'] = 'text'
        
        return result
        
    except Exception as e:
        return {
            'error': f'Erro ao processar arquivo de texto: {str(e)}',
            'extracted_text': '',
            'source': 'text'
        }

def process_audio_file(audio_file_path: str, llm_provider: str = None, llm_model_name: str = None) -> dict:
    """
    Processa arquivo de áudio usando Whisper para transcrição e depois IA para análise.
    """
    try:
        import openai
        
        # Configurar OpenAI para Whisper
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            return {'error': 'OPENAI_API_KEY necessária para transcrição de áudio'}
        
        client = openai.OpenAI(api_key=openai_api_key)
        
        # Transcrever áudio
        with open(audio_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        
        transcribed_text = transcript.text
        
        # Processar texto transcrito com IA
        result = process_evolution_input(
            evolution_text_input=transcribed_text,
            llm_provider=llm_provider,
            llm_model_name=llm_model_name
        )
        
        result['transcribed_text'] = transcribed_text
        result['source'] = 'audio'
        
        return result
        
    except Exception as e:
        return {
            'error': f'Erro ao processar áudio: {str(e)}',
            'transcribed_text': '',
            'source': 'audio'
        }

def process_video_file(video_file_path: str, llm_provider: str = None, llm_model_name: str = None) -> dict:
    """
    Processa arquivo de vídeo extraindo áudio e usando Whisper para transcrição.
    """
    try:
        import subprocess
        import tempfile
        import os
        
        # Extrair áudio do vídeo usando ffmpeg
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
            temp_audio_path = temp_audio.name
        
        # Comando ffmpeg para extrair áudio
        cmd = [
            'ffmpeg', '-i', video_file_path,
            '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
            temp_audio_path, '-y'
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Processar áudio extraído
        result = process_audio_file(temp_audio_path, llm_provider, llm_model_name)
        result['source'] = 'video'
        
        # Limpar arquivo temporário
        os.unlink(temp_audio_path)
        
        return result
        
    except subprocess.CalledProcessError as e:
        return {
            'error': f'Erro ao extrair áudio do vídeo: {str(e)}',
            'transcribed_text': '',
            'source': 'video'
        }
    except Exception as e:
        return {
            'error': f'Erro ao processar vídeo: {str(e)}',
            'transcribed_text': '',
            'source': 'video'
        }

def test_llm_connection(provider: str, model: str, api_key: str = None, base_url: str = None) -> dict:
    """
    Testa a conexão com um provedor de LLM específico.
    """
    try:
        # Configurar temporariamente as variáveis de ambiente para teste
        original_env = {}
        
        if provider == 'openai' and api_key:
            original_env['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
            os.environ['OPENAI_API_KEY'] = api_key
        elif provider == 'anthropic' and api_key:
            original_env['ANTHROPIC_API_KEY'] = os.getenv('ANTHROPIC_API_KEY')
            os.environ['ANTHROPIC_API_KEY'] = api_key
        elif provider == 'google' and api_key:
            original_env['GOOGLE_API_KEY'] = os.getenv('GOOGLE_API_KEY')
            os.environ['GOOGLE_API_KEY'] = api_key
        elif provider == 'groq' and api_key:
            original_env['GROQ_API_KEY'] = os.getenv('GROQ_API_KEY')
            os.environ['GROQ_API_KEY'] = api_key
        elif provider == 'xai' and api_key:
            original_env['XAI_API_KEY'] = os.getenv('XAI_API_KEY')
            os.environ['XAI_API_KEY'] = api_key
        
        # Tentar criar instância do LLM
        llm = get_llm(provider=provider, model_name=model)
        
        # Fazer uma pergunta simples para testar
        test_message = "Responda apenas 'OK' se você conseguir me ouvir."
        
        try:
            response = llm.invoke(test_message)
            
            # Restaurar variáveis de ambiente originais
            for key, value in original_env.items():
                if value is not None:
                    os.environ[key] = value
                elif key in os.environ:
                    del os.environ[key]
            
            return {
                'success': True,
                'message': f'Conexão com {provider} ({model}) estabelecida com sucesso',
                'response': str(response.content) if hasattr(response, 'content') else str(response),
                'provider': provider,
                'model': model
            }
            
        except Exception as llm_error:
            # Restaurar variáveis de ambiente originais
            for key, value in original_env.items():
                if value is not None:
                    os.environ[key] = value
                elif key in os.environ:
                    del os.environ[key]
            
            return {
                'success': False,
                'error': f'Erro ao comunicar com {provider}: {str(llm_error)}',
                'provider': provider,
                'model': model
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': f'Erro ao configurar {provider}: {str(e)}',
            'provider': provider,
            'model': model
        }
