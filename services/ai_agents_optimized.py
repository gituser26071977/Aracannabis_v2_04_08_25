"""
Sistema de IA Otimizado para Aracannabis
Versão robusta com fallbacks e tratamento de erros aprimorado
"""

import os
import json
import requests
import time
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

class AIProvider:
    """Classe base para provedores de IA"""
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout = 30
        
    def make_request(self, messages: List[Dict], **kwargs) -> Dict:
        """Método base para fazer requisições"""
        raise NotImplementedError
        
    def test_connection(self) -> Dict:
        """Testa a conexão com o provedor"""
        try:
            response = self.make_request([
                {"role": "user", "content": "Responda apenas 'OK' se conseguir me ouvir."}
            ])
            return {
                "success": True,
                "message": "Conexão estabelecida com sucesso",
                "response": response.get("content", "")
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

class OpenAIProvider(AIProvider):
    """Provedor OpenAI"""
    
    def __init__(self, api_key: str = None, model: str = "gpt-4o"):
        super().__init__(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            base_url="https://api.openai.com/v1",
            model=model
        )
        
    def make_request(self, messages: List[Dict], **kwargs) -> Dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.1),
            "max_tokens": kwargs.get("max_tokens", 2000)
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=self.timeout
        )
        
        if response.status_code != 200:
            raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")
            
        result = response.json()
        return {
            "content": result["choices"][0]["message"]["content"],
            "usage": result.get("usage", {}),
            "model": result.get("model", self.model)
        }

class GroqProvider(AIProvider):
    """Provedor Groq"""
    
    def __init__(self, api_key: str = None, model: str = "llama-3.1-70b-versatile"):
        super().__init__(
            api_key=api_key or os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1",
            model=model
        )
        
    def make_request(self, messages: List[Dict], **kwargs) -> Dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.1),
            "max_tokens": kwargs.get("max_tokens", 2000)
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=self.timeout
        )
        
        if response.status_code != 200:
            raise Exception(f"Groq API error: {response.status_code} - {response.text}")
            
        result = response.json()
        return {
            "content": result["choices"][0]["message"]["content"],
            "usage": result.get("usage", {}),
            "model": result.get("model", self.model)
        }

class AnthropicProvider(AIProvider):
    """Provedor Anthropic Claude"""
    
    def __init__(self, api_key: str = None, model: str = "claude-3-5-sonnet-20241022"):
        super().__init__(
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
            base_url="https://api.anthropic.com",
            model=model
        )
        
    def make_request(self, messages: List[Dict], **kwargs) -> Dict:
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # Converter formato de mensagens para Anthropic
        system_message = ""
        user_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                user_messages.append(msg)
        
        data = {
            "model": self.model,
            "messages": user_messages,
            "max_tokens": kwargs.get("max_tokens", 2000),
            "temperature": kwargs.get("temperature", 0.1)
        }
        
        if system_message:
            data["system"] = system_message
        
        response = requests.post(
            f"{self.base_url}/v1/messages",
            headers=headers,
            json=data,
            timeout=self.timeout
        )
        
        if response.status_code != 200:
            raise Exception(f"Anthropic API error: {response.status_code} - {response.text}")
            
        result = response.json()
        return {
            "content": result["content"][0]["text"],
            "usage": result.get("usage", {}),
            "model": result.get("model", self.model)
        }

class GoogleProvider(AIProvider):
    """Provedor Google Gemini"""
    
    def __init__(self, api_key: str = None, model: str = "gemini-1.5-pro"):
        super().__init__(
            api_key=api_key or os.getenv("GOOGLE_API_KEY"),
            base_url="https://generativelanguage.googleapis.com/v1beta",
            model=model
        )
        
    def make_request(self, messages: List[Dict], **kwargs) -> Dict:
        # Converter mensagens para formato Gemini
        contents = []
        for msg in messages:
            if msg["role"] == "user":
                contents.append({"parts": [{"text": msg["content"]}]})
            elif msg["role"] == "assistant":
                contents.append({"parts": [{"text": msg["content"]}], "role": "model"})
        
        data = {
            "contents": contents,
            "generationConfig": {
                "temperature": kwargs.get("temperature", 0.1),
                "maxOutputTokens": kwargs.get("max_tokens", 2000)
            }
        }
        
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        
        response = requests.post(
            url,
            json=data,
            timeout=self.timeout
        )
        
        if response.status_code != 200:
            raise Exception(f"Google API error: {response.status_code} - {response.text}")
            
        result = response.json()
        
        if "candidates" not in result or not result["candidates"]:
            raise Exception("Google API returned no candidates")
            
        content = result["candidates"][0]["content"]["parts"][0]["text"]
        
        return {
            "content": content,
            "usage": result.get("usageMetadata", {}),
            "model": self.model
        }

class OllamaProvider(AIProvider):
    """Provedor Ollama (local)"""
    
    def __init__(self, base_url: str = None, model: str = "mistral-small3.1:24b"):
        super().__init__(
            base_url=base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            model=model
        )
        
    def make_request(self, messages: List[Dict], **kwargs) -> Dict:
        data = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.1),
                "num_predict": kwargs.get("max_tokens", 2000)
            }
        }
        
        response = requests.post(
            f"{self.base_url}/api/chat",
            json=data,
            timeout=self.timeout
        )
        
        if response.status_code != 200:
            raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
            
        result = response.json()
        return {
            "content": result["message"]["content"],
            "usage": {},
            "model": result.get("model", self.model)
        }

class AIManager:
    """Gerenciador principal de IA com fallbacks"""
    
    def __init__(self):
        self.providers = {}
        self.current_provider = None
        self.setup_providers()
        
    def setup_providers(self):
        """Configura todos os provedores disponíveis"""
        
        # Configurar provedores baseado nas variáveis de ambiente
        if os.getenv("OPENAI_API_KEY"):
            self.providers["openai"] = OpenAIProvider()
            
        if os.getenv("GROQ_API_KEY"):
            self.providers["groq"] = GroqProvider()
            
        if os.getenv("ANTHROPIC_API_KEY"):
            self.providers["anthropic"] = AnthropicProvider()
            
        if os.getenv("GOOGLE_API_KEY"):
            self.providers["google"] = GoogleProvider()
            
        # Ollama sempre disponível (local)
        self.providers["ollama"] = OllamaProvider()
        
        # Definir provedor padrão
        default_provider = os.getenv("DEFAULT_LLM_PROVIDER", "groq")
        if default_provider in self.providers:
            self.current_provider = default_provider
        elif self.providers:
            self.current_provider = list(self.providers.keys())[0]
            
    def get_provider(self, provider_name: str = None) -> AIProvider:
        """Obtém um provedor específico ou o atual"""
        if provider_name and provider_name in self.providers:
            return self.providers[provider_name]
        elif self.current_provider and self.current_provider in self.providers:
            return self.providers[self.current_provider]
        else:
            raise Exception("Nenhum provedor de IA disponível")
            
    def make_request_with_fallback(self, messages: List[Dict], provider_name: str = None, **kwargs) -> Dict:
        """Faz requisição com fallback automático"""
        
        # Lista de provedores para tentar (em ordem de preferência)
        providers_to_try = []
        
        if provider_name and provider_name in self.providers:
            providers_to_try.append(provider_name)
            
        # Adicionar provedor atual se não for o mesmo
        if self.current_provider and self.current_provider not in providers_to_try:
            providers_to_try.append(self.current_provider)
            
        # Adicionar outros provedores como fallback
        for name in ["groq", "openai", "anthropic", "google", "ollama"]:
            if name in self.providers and name not in providers_to_try:
                providers_to_try.append(name)
        
        last_error = None
        
        for provider_name in providers_to_try:
            try:
                provider = self.providers[provider_name]
                print(f"Tentando provedor: {provider_name}")
                
                result = provider.make_request(messages, **kwargs)
                result["provider_used"] = provider_name
                
                print(f"Sucesso com provedor: {provider_name}")
                return result
                
            except Exception as e:
                last_error = e
                print(f"Erro com provedor {provider_name}: {str(e)}")
                continue
        
        # Se chegou aqui, todos os provedores falharam
        raise Exception(f"Todos os provedores falharam. Último erro: {str(last_error)}")

# Instância global do gerenciador
ai_manager = AIManager()

def process_evolution_input_optimized(
    evolution_text_input: str,
    image_extracted_text: str = None,
    provider: str = None,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Versão otimizada do processamento de evolução com fallbacks
    """
    
    # Inicia medição de tempo
    start_time = time.time()
    
    try:
        # Preparar prompt otimizado
        system_prompt = """Você é um especialista em análise de registros médicos de cannabis medicinal.
        
Analise o texto fornecido e extraia informações estruturadas sobre:
1. Evolução narrativa do paciente
2. Informações sobre dosagens (produto, quantidade, frequência, concentrações)
3. Sintomas mencionados
4. Observações relevantes

Retorne APENAS um JSON válido no seguinte formato:
{
  "narrative_evolution": "descrição da evolução do paciente",
  "dosage_info": {
    "produto": "nome do produto se mencionado",
    "gotas": "número de gotas se mencionado",
    "frequencia": "frequência se mencionada",
    "cbd": "concentração CBD se mencionada",
    "thc": "concentração THC se mencionada"
  },
  "symptoms": ["lista de sintomas mencionados"],
  "observations": "observações adicionais",
  "confidence": 85
}"""

        user_content = f"Texto da evolução: {evolution_text_input}"
        if image_extracted_text:
            user_content += f"\n\nTexto extraído de imagem: {image_extracted_text}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        # Fazer requisição com fallback
        result = ai_manager.make_request_with_fallback(
            messages=messages,
            provider_name=provider,
            temperature=0.1,
            max_tokens=1500
        )
        
        # Processar resposta
        content = result["content"].strip()
        
        # Registra tempo de resposta da API
        api_response_time = time.time() - start_time
        
        # Tentar extrair JSON da resposta
        try:
            # Procurar por JSON na resposta
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                parsed_result = json.loads(json_str)
                
                # Adicionar metadados
                parsed_result["provider_used"] = result.get("provider_used", "unknown")
                parsed_result["model_used"] = result.get("model_used", "unknown")
                parsed_result["api_response_time"] = api_response_time
                parsed_result["total_processing_time"] = time.time() - start_time
                
                # Log de desempenho
                print(f"Processamento de evolução concluído | Provedor: {parsed_result['provider_used']} | "
                      f"Modelo: {parsed_result['model_used']} | "
                      f"Tempo API: {api_response_time:.2f}s | "
                      f"Tempo total: {parsed_result['total_processing_time']:.2f}s")
                
                return parsed_result
            else:
                raise ValueError("JSON não encontrado na resposta")
                
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Erro ao parsear JSON: {e}")
            print(f"Resposta da IA: {content}")
            
            # Fallback: retornar estrutura básica
            return {
                "narrative_evolution": evolution_text_input,
                "dosage_info": None,
                "symptoms": [],
                "observations": "Análise automática não disponível",
                "confidence": 50,
                "provider_used": result.get("provider_used", "unknown"),
                "error": f"JSON parse error: {str(e)}",
                "raw_response": content
            }
            
    except Exception as e:
        print(f"Erro no processamento de evolução: {str(e)}")
        
        # Fallback final
        end_time = time.time()
        return {
            "narrative_evolution": evolution_text_input,
            "dosage_info": None,
            "symptoms": [],
            "observations": "Erro na análise de IA",
            "confidence": 0,
            "provider_used": "none",
            "error": str(e),
            "total_processing_time": end_time - start_time
        }

def process_import_data_optimized(
    text_content: str,
    patient_id: int,
    provider: str = None,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Versão otimizada do processamento de importação
    """
    
    # Inicia medição de tempo
    start_time = time.time()
    
    try:
        system_prompt = """Você é um especialista em análise de dados médicos importados.

Analise o texto e identifique:
1. Tipo de informação (evolução, dosagem, sintoma)
2. Data (se mencionada)
3. Detalhes específicos

Retorne APENAS um JSON válido:
{
  "tipo": "evolucao|dosagem|sintoma|misto",
  "data": "YYYY-MM-DD ou null",
  "evolucoes": [{"descricao": "texto", "observacoes": "obs"}],
  "dosagens": [{"produto": "nome", "gotas": 10, "frequencia": 3, "cbd": 25.0, "thc": 2.5}],
  "sintomas": [{"sintoma": "nome", "intensidade": 5, "observacoes": "obs"}],
  "confianca": 80
}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analise este texto: {text_content}"}
        ]
        
        result = ai_manager.make_request_with_fallback(
            messages=messages,
            provider_name=provider,
            temperature=0.1,
            max_tokens=1500
        )
        
        # Registra tempo de resposta da API
        api_response_time = time.time() - start_time
        
        content = result["content"].strip()
        
        try:
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                parsed_result = json.loads(json_str)
                parsed_result["provider_used"] = result.get("provider_used", "unknown")
                parsed_result["model_used"] = result.get("model_used", "unknown")
                parsed_result["api_response_time"] = api_response_time
                parsed_result["total_processing_time"] = time.time() - start_time
                
                # Log de desempenho
                print(f"Processamento de importação concluído | Provedor: {parsed_result['provider_used']} | "
                      f"Modelo: {parsed_result['model_used']} | "
                      f"Tempo API: {api_response_time:.2f}s | "
                      f"Tempo total: {parsed_result['total_processing_time']:.2f}s")
                return parsed_result
            else:
                raise ValueError("JSON não encontrado")
                
        except (json.JSONDecodeError, ValueError):
            # Fallback
            return {
                "tipo": "evolucao",
                "data": None,
                "evolucoes": [{"descricao": text_content, "observacoes": ""}],
                "dosagens": [],
                "sintomas": [],
                "confianca": 50,
                "provider_used": result.get("provider_used", "unknown"),
                "error": "JSON parse error"
            }
            
    except Exception as e:
        end_time = time.time()
        return {
            "tipo": "evolucao",
            "data": None,
            "evolucoes": [{"descricao": text_content, "observacoes": ""}],
            "dosagens": [],
            "sintomas": [],
            "confianca": 0,
            "provider_used": "none",
            "error": str(e),
            "total_processing_time": end_time - start_time
        }

def chat_with_data_optimized(
    question: str,
    context: Dict,
    provider: str = None,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Versão otimizada do chat com dados
    """
    
    # Inicia medição de tempo
    start_time = time.time()
    
    try:
        system_prompt = """Você é um assistente médico especializado em cannabis medicinal.

Responda perguntas sobre os dados do paciente de forma precisa e útil.
Cite dados específicos quando relevante e forneça insights médicos apropriados.

Retorne APENAS um JSON válido:
{
  "resposta": "resposta principal detalhada",
  "dados_citados": ["dados específicos mencionados"],
  "insights": ["insights identificados"],
  "sugestoes": ["sugestões para o tratamento"]
}"""

        context_text = f"""
DADOS DO PACIENTE:
Nome: {context['paciente']['nome']}
Condição: {context['paciente']['condicao_medica']}

EVOLUÇÕES: {json.dumps(context['evolucoes'][:5], ensure_ascii=False)}
DOSAGENS: {json.dumps(context['dosagens'][:5], ensure_ascii=False)}
SINTOMAS: {json.dumps(context['sintomas'][:10], ensure_ascii=False)}
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Pergunta: {question}\n\nContexto: {context_text}"}
        ]
        
        result = ai_manager.make_request_with_fallback(
            messages=messages,
            provider_name=provider,
            temperature=0.2,
            max_tokens=2000
        )
        
        # Registra tempo de resposta da API
        api_response_time = time.time() - start_time
        
        content = result["content"].strip()
        
        try:
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                parsed_result = json.loads(json_str)
                parsed_result["provider_used"] = result.get("provider_used", "unknown")
                parsed_result["model_used"] = result.get("model_used", "unknown")
                parsed_result["api_response_time"] = api_response_time
                parsed_result["total_processing_time"] = time.time() - start_time
                
                # Log de desempenho
                print(f"Chat com dados concluído | Provedor: {parsed_result['provider_used']} | "
                      f"Modelo: {parsed_result['model_used']} | "
                      f"Tempo API: {api_response_time:.2f}s | "
                      f"Tempo total: {parsed_result['total_processing_time']:.2f}s")
                return parsed_result
            else:
                raise ValueError("JSON não encontrado")
                
        except (json.JSONDecodeError, ValueError):
            return {
                "resposta": content,
                "dados_citados": [],
                "insights": [],
                "sugestoes": [],
                "provider_used": result.get("provider_used", "unknown"),
                "error": "JSON parse error"
            }
            
    except Exception as e:
        end_time = time.time()
        return {
            "resposta": f"Desculpe, ocorreu um erro: {str(e)}",
            "dados_citados": [],
            "insights": [],
            "sugestoes": [],
            "provider_used": "none",
            "error": str(e),
            "total_processing_time": end_time - start_time
        }

def test_llm_connection_optimized(
    provider: str,
    model: str,
    api_key: str = None,
    base_url: str = None
) -> Dict[str, Any]:
    """
    Testa conexão com provedor específico
    """
    
    try:
        # Criar instância temporária do provedor
        if provider == "openai":
            test_provider = OpenAIProvider(api_key=api_key, model=model)
        elif provider == "groq":
            test_provider = GroqProvider(api_key=api_key, model=model)
        elif provider == "anthropic":
            test_provider = AnthropicProvider(api_key=api_key, model=model)
        elif provider == "google":
            test_provider = GoogleProvider(api_key=api_key, model=model)
        elif provider == "ollama":
            test_provider = OllamaProvider(base_url=base_url, model=model)
        else:
            return {
                "success": False,
                "error": f"Provedor não suportado: {provider}"
            }
        
        return test_provider.test_connection()
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# Funções de compatibilidade com o sistema existente
def process_evolution_input(*args, **kwargs):
    """Wrapper para compatibilidade"""
    return process_evolution_input_optimized(*args, **kwargs)

def process_import_data(*args, **kwargs):
    """Wrapper para compatibilidade"""
    return process_import_data_optimized(*args, **kwargs)

def chat_with_data(*args, **kwargs):
    """Wrapper para compatibilidade"""
    return chat_with_data_optimized(*args, **kwargs)

def test_llm_connection(*args, **kwargs):
    """Wrapper para compatibilidade"""
    return test_llm_connection_optimized(*args, **kwargs)
