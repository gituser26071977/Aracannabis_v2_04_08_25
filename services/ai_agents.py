"""
Sistema de Agentes de IA para o Aracannabis
Versão otimizada com fallbacks e tratamento de erros
"""

import os
from functools import wraps
from typing import Dict, List
import json
import logging

# Configurar logging
logger = logging.getLogger(__name__)

# Importar serviço de persistência
try:
    from services.ai_config_storage import load_config, get_api_key, get_base_url
    CONFIG_STORAGE_AVAILABLE = True
except ImportError:
    logger.warning("Serviço de persistência de configuração não disponível")
    CONFIG_STORAGE_AVAILABLE = False
    def load_config():
        return {}
    def get_api_key(provider):
        return None
    def get_base_url(provider):
        return None

# Importações condicionais para evitar erros de dependência
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI não disponível")

try:
    import groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("Groq não disponível")

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic não disponível")

try:
    import google.generativeai as genai
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    logger.warning("Google Generative AI não disponível")

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logger.warning("Ollama não disponível")

try:
    # Maritaca usa API estilo OpenAI; habilitamos como provedor opcional
    MARITACA_AVAILABLE = True
except Exception:
    MARITACA_AVAILABLE = False
    logger.warning("Maritaca AI não disponível")

class AIProviderManager:
    """Gerenciador de provedores de IA"""
    
    def __init__(self):
        self.providers = {
            'groq': {
                'available': GROQ_AVAILABLE,
                'client': None,
                'models': ['llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 'mixtral-8x7b-32768'],
                'type': 'cloud'
            },
            'openai': {
                'available': OPENAI_AVAILABLE,
                'client': None,
                'models': ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo'],
                'type': 'cloud'
            },
            'anthropic': {
                'available': ANTHROPIC_AVAILABLE,
                'client': None,
                'models': ['claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022', 'claude-3-opus-20240229'],
                'type': 'cloud'
            },
            'google': {
                'available': GOOGLE_AVAILABLE,
                'client': None,
                'models': ['gemini-2.5-flash-lite', 'gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.0-flash-exp', 'gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-2.REDACTED', 'gemini-2.5-flash-preview-tts'],
                'type': 'cloud'
            },
            'ollama_local': {
                'available': OLLAMA_AVAILABLE,
                'client': None,
                'models': ['deepseek-ocr:latest', 'deepseek-coder:6.7b', 'gemma3:4b', 'gemma3:12b', 'gpt-oss:20b', 'llama3.1:8b', 'llama3.2:1b', 'llama3.2:3b', 'mistral:7b', 'phi3:mini', 'qwen3:1.7b', 'qwen3-coder:480b-cloud', 'qwen3-coder:latest', 'qwen3-vl:2b', 'qwen3-vl:8b'],
                'type': 'local'
            },
            'ollama_cloud': {
                'available': OLLAMA_AVAILABLE,
                'client': None,
                'models': ['deepseek-ocr:latest', 'deepseek-coder:6.7b', 'gemma3:4b', 'gemma3:12b', 'gpt-oss:20b', 'llama3.1:8b', 'llama3.2:1b', 'llama3.2:3b', 'mistral:7b', 'phi3:mini', 'qwen3:1.7b', 'qwen3-coder:480b-cloud', 'qwen3-coder:latest', 'qwen3-vl:2b', 'qwen3-vl:8b'],
                'type': 'cloud'
            },
            'deepseek': {
                'available': OPENAI_AVAILABLE,  # Uses OpenAI compatible API
                'client': None,
                'models': ['deepseek-chat', 'deepseek-coder'],
                'type': 'cloud'
            },
            'maritaca': {
                'available': MARITACA_AVAILABLE,
                'client': None,
                'models': ['sabiazinho-4', 'maritaca-ocr', 'maritaca-base'],
                'type': 'cloud'
            },
            'xai': {
                'available': False,  # xAI Grok API not publicly available yet
                'client': None,
                'models': ['grok-beta', 'grok-vision'],
                'type': 'cloud'
            },
            'zhipu': {
                'available': OPENAI_AVAILABLE, # Uses OpenAI compatible API
                'client': None,
                'models': ['glm-4', 'glm-4-plus', 'glm-4-air', 'glm-4-flash', 'glm-4v', 'glm-4v-flash', 'glm-4-alltools'],
                'type': 'cloud'
            }
        }
        
        # Carregar configurações persistidas
        if CONFIG_STORAGE_AVAILABLE:
            try:
                config = load_config()
                self.default_provider = config.get('default_provider', os.getenv('DEFAULT_LLM_PROVIDER', 'groq'))
                self.default_model = config.get('default_model', os.getenv('DEFAULT_LLM_MODEL', 'llama-3.3-70b-versatile'))
                self.default_vision_provider = config.get('default_vision_provider', os.getenv('DEFAULT_LLM_VISION_PROVIDER', self.default_provider))
                self.default_vision_model = config.get('default_vision_model', os.getenv('DEFAULT_LLM_VISION_MODEL', self.default_model))
                self.default_multimodal_provider = config.get('default_multimodal_provider', os.getenv('DEFAULT_LLM_MULTIMODAL_PROVIDER', self.default_vision_provider))
                self.default_multimodal_model = config.get('default_multimodal_model', os.getenv('DEFAULT_LLM_MULTIMODAL_MODEL', self.default_vision_model))
                logger.info("Configurações carregadas do arquivo de persistência")
            except Exception as e:
                logger.warning(f"Erro ao carregar configurações persistidas: {e}. Usando variáveis de ambiente.")
                self.default_provider = os.getenv('DEFAULT_LLM_PROVIDER', 'groq')
                self.default_model = os.getenv('DEFAULT_LLM_MODEL', 'llama-3.3-70b-versatile')
                self.default_vision_provider = os.getenv('DEFAULT_LLM_VISION_PROVIDER', self.default_provider)
                self.default_vision_model = os.getenv('DEFAULT_LLM_VISION_MODEL', self.default_model)
                self.default_multimodal_provider = os.getenv('DEFAULT_LLM_MULTIMODAL_PROVIDER', self.default_vision_provider)
                self.default_multimodal_model = os.getenv('DEFAULT_LLM_MULTIMODAL_MODEL', self.default_vision_model)
        else:
            self.default_provider = os.getenv('DEFAULT_LLM_PROVIDER', 'groq')
            self.default_model = os.getenv('DEFAULT_LLM_MODEL', 'llama-3.3-70b-versatile')
            self.default_vision_provider = os.getenv('DEFAULT_LLM_VISION_PROVIDER', self.default_provider)
            self.default_vision_model = os.getenv('DEFAULT_LLM_VISION_MODEL', self.default_model)
            self.default_multimodal_provider = os.getenv('DEFAULT_LLM_MULTIMODAL_PROVIDER', self.default_vision_provider)
            self.default_multimodal_model = os.getenv('DEFAULT_LLM_MULTIMODAL_MODEL', self.default_vision_model)
        
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Inicializa os clientes dos provedores"""
        try:
            if self.providers['groq']['available']:
                api_key = get_api_key('groq') or os.getenv('GROQ_API_KEY')
                if api_key:
                    self.providers['groq']['client'] = groq.Groq(api_key=api_key)
            
            if self.providers['openai']['available']:
                api_key = get_api_key('openai') or os.getenv('OPENAI_API_KEY')
                if api_key:
                    self.providers['openai']['client'] = OpenAI(api_key=api_key)
            
            if self.providers['anthropic']['available']:
                api_key = get_api_key('anthropic') or os.getenv('ANTHROPIC_API_KEY')
                if api_key:
                    self.providers['anthropic']['client'] = anthropic.Anthropic(api_key=api_key)
            
            if self.providers['google']['available']:
                api_key = get_api_key('google') or os.getenv('GOOGLE_API_KEY')
                if api_key:
                    genai.configure(api_key=api_key)
                    self.providers['google']['client'] = genai
            
            # Inicializar Ollama Local - verificar conectividade local
            if self.providers['ollama_local']['available']:
                try:
                    # Testar conexão com Ollama local (default: localhost:11434)
                    ollama.list()
                    self.providers['ollama_local']['client'] = ollama
                    logger.info("Ollama local conectado com sucesso")
                except Exception as e:
                    logger.warning(f"Ollama local não disponível: {str(e)}")
                    self.providers['ollama_local']['available'] = False
            
            # Inicializar Ollama Cloud - configurar base URL customizada
            if self.providers['ollama_cloud']['available']:
                try:
                    # Configurar Ollama para cloud (base URL customizada)
                    ollama_cloud_url = os.getenv('OLLAMA_CLOUD_URL', 'http://localhost:11434')
                    # Nota: o pacote ollama não suporta fácil mudança de URL base
                    # Para cloud, precisaríamos de uma solução diferente
                    # Por enquanto, usamos a mesma instância local
                    ollama.list()
                    self.providers['ollama_cloud']['client'] = ollama
                    logger.info("Ollama cloud configurado (nota: usando instância local por padrão)")
                except Exception as e:
                    logger.warning(f"Ollama cloud não disponível: {str(e)}")
                    self.providers['ollama_cloud']['available'] = False
            
            # Inicializar DeepSeek (compatível com OpenAI)
            if self.providers['deepseek']['available']:
                try:
                    api_key = get_api_key('deepseek') or os.getenv('DEEPSEEK_API_KEY')
                    if api_key:
                        base_url = get_base_url('deepseek') or os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
                        self.providers['deepseek']['client'] = OpenAI(
                            api_key=api_key,
                            base_url=base_url
                        )
                except Exception as e:
                    logger.warning(f"DeepSeek não disponível: {str(e)}")
                    self.providers['deepseek']['available'] = False

            # Inicializar Maritaca (compatível com OpenAI)
            if self.providers['maritaca']['available']:
                try:
                    api_key = get_api_key('maritaca') or os.getenv('MARITACA_API_KEY')
                    if api_key:
                        base_url = get_base_url('maritaca') or os.getenv('MARITACA_BASE_URL', 'https://chat.maritaca.ai/api')
                        self.providers['maritaca']['client'] = OpenAI(
                            api_key=api_key,
                            base_url=base_url,
                            timeout=60.0
                        )
                    else:
                        self.providers['maritaca']['available'] = False
                except Exception as e:
                    logger.warning(f"Maritaca não disponível: {str(e)}")
                    self.providers['maritaca']['available'] = False

            # Inicializar Zhipu AI (GLM-4)
            if self.providers['zhipu']['available']:
                try:
                    api_key = get_api_key('zhipu') or os.getenv('ZHIPU_API_KEY')
                    if api_key:
                        base_url = get_base_url('zhipu') or os.getenv('ZHIPU_BASE_URL', "https://open.bigmodel.cn/api/paas/v4/")
                        self.providers['zhipu']['client'] = OpenAI(
                            api_key=api_key,
                            base_url=base_url
                        )
                    else:
                        self.providers['zhipu']['available'] = False
                except Exception as e:
                    logger.warning(f"Zhipu AI não disponível: {str(e)}")
                    self.providers['zhipu']['available'] = False
        
        except Exception as e:
            logger.error(f"Erro ao inicializar clientes de IA: {str(e)}")
    
    def get_available_providers(self) -> List[str]:
        """Retorna lista de provedores disponíveis"""
        return [provider for provider, info in self.providers.items() 
                if info['available'] and info['client'] is not None]
    
    def vision_completion(self, prompt: str, image_data: str, provider: str = None, model: str = None, 
                        temperature: float = 0.1, max_tokens: int = 1500) -> Dict:
        """Executa análise de imagem (Visão) com fallback"""
        
        provider = provider or self.default_vision_provider
        model = model or self.default_vision_model
        
        # Tentar provedor solicitado
        if self._is_provider_available(provider):
            try:
                return self._call_vision_provider(provider, model, prompt, image_data, temperature, max_tokens)
            except Exception as e:
                logger.warning(f"Erro de visão no provedor {provider}: {str(e)}")
        
        # Fallback para outros provedores de visão disponíveis
        # Lista de provedores conhecidos por suportar visão
        vision_capable = ['openai', 'google', 'ollama_local', 'ollama_cloud', 'zhipu']
        available_providers = self.get_available_providers()
        
        for fallback_provider in available_providers:
            if fallback_provider in vision_capable and fallback_provider != provider:
                try:
                    # Modelos padrão de visão para fallback
                    fallback_model = self.providers[fallback_provider]['models'][0]
                    if fallback_provider == 'zhipu': fallback_model = 'glm-4v'
                    elif fallback_provider == 'google': fallback_model = 'gemini-1.5-flash'
                    elif fallback_provider == 'openai': fallback_model = 'gpt-4o-mini'
                    
                    return self._call_vision_provider(fallback_provider, fallback_model, prompt, image_data, temperature, max_tokens)
                except Exception as e:
                    logger.warning(f"Erro no fallback de visão {fallback_provider}: {str(e)}")
        
        return {
            'content': 'Recurso de visão temporariamente indisponível.',
            'provider': 'fallback',
            'model': 'none',
            'error': 'Todos os provedores de visão falharam'
        }

    def _call_vision_provider(self, provider: str, model: str, prompt: str, image_data: str, 
                             temperature: float, max_tokens: int) -> Dict:
        """Chama o provedor específico para tarefa de visão"""
        
        if provider == 'openai':
            return self._call_openai_vision(model, prompt, image_data, temperature, max_tokens)
        elif provider == 'google':
            return self._call_google_vision(model, prompt, image_data, temperature, max_tokens)
        elif provider in ['ollama_local', 'ollama_cloud']:
            return self._call_ollama_vision(provider, model, prompt, image_data, temperature, max_tokens)
        elif provider == 'zhipu':
            return self._call_zhipu_vision(model, prompt, image_data, temperature, max_tokens)
        else:
            # Fallback para chat normal se o provedor não tiver visão específica (improvável aqui)
            messages = [{"role": "user", "content": prompt}]
            return self._call_provider(provider, model, messages, temperature, max_tokens)

    def _call_openai_vision(self, model: str, prompt: str, image_data: str, temperature: float, max_tokens: int) -> Dict:
        """Chama visão da OpenAI"""
        # Garantir que image_data seja base64 com prefixo se necessário
        if not image_data.startswith('data:image'):
            # Assumindo JPEG por padrão se não houver prefixo
            image_url = f"data:image/jpeg;base64,{image_data}"
        else:
            image_url = image_data

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url}
                    }
                ]
            }
        ]
        
        response = self.providers['openai']['client'].chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return {
            'content': response.choices[0].message.content,
            'provider': 'openai',
            'model': model
        }

    def _call_google_vision(self, model: str, prompt: str, image_data: str, temperature: float, max_tokens: int) -> Dict:
        """Chama visão do Google Gemini"""
        # Remover prefixo data:image/...;base64, se existir
        if ';base64,' in image_data:
            pure_base64 = image_data.split(';base64,')[1]
        else:
            pure_base64 = image_data
            
        # Google requer bytes ou objeto de imagem
        image_part = {
            "mime_type": "image/jpeg",
            "data": pure_base64
        }
        
        model_obj = self.providers['google']['client'].GenerativeModel(model)
        response = model_obj.generate_content(
            [prompt, image_part],
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens
            )
        )
        
        return {
            'content': response.text,
            'provider': 'google',
            'model': model
        }

    def _call_ollama_vision(self, provider: str, model: str, prompt: str, image_data: str, temperature: float, max_tokens: int) -> Dict:
        """Chama visão do Ollama"""
        # Remover prefixo se existir
        if ';base64,' in image_data:
            pure_base64 = image_data.split(';base64,')[1]
        else:
            pure_base64 = image_data

        response = self.providers[provider]['client'].chat(
            model=model,
            messages=[{
                "role": "user",
                "content": prompt,
                "images": [pure_base64]
            }],
            options={
                "temperature": temperature,
                "num_predict": max_tokens
            }
        )
        
        return {
            'content': response['message']['content'],
            'provider': provider,
            'model': model
        }

    def _call_zhipu_vision(self, model: str, prompt: str, image_data: str, temperature: float, max_tokens: int) -> Dict:
        """Chama visão da Zhipu AI (GLM-4V)"""
        # Zhipu aceita formato similar à OpenAI para visão
        if not image_data.startswith('data:image'):
            image_url = f"data:image/jpeg;base64,{image_data}"
        else:
            image_url = image_data

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url}
                    }
                ]
            }
        ]
        
        response = self.providers['zhipu']['client'].chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return {
            'content': response.choices[0].message.content,
            'provider': 'zhipu',
            'model': model
        }

    def chat_completion(self, messages: List[Dict], provider: str = None, model: str = None, 
                       temperature: float = 0.7, max_tokens: int = 1000) -> Dict:
        """Executa chat completion com fallback entre provedores"""
        
        provider = provider or self.default_provider
        model = model or self.default_model
        
        # Tentar provedor solicitado primeiro
        if self._is_provider_available(provider):
            try:
                return self._call_provider(provider, model, messages, temperature, max_tokens)
            except Exception as e:
                logger.warning(f"Erro no provedor {provider}: {str(e)}")
        
        # Fallback para outros provedores disponíveis
        available_providers = self.get_available_providers()
        for fallback_provider in available_providers:
            if fallback_provider != provider:
                try:
                    # Usar modelo padrão do provedor de fallback
                    fallback_model = self.providers[fallback_provider]['models'][0]
                    return self._call_provider(fallback_provider, fallback_model, messages, temperature, max_tokens)
                except Exception as e:
                    logger.warning(f"Erro no fallback {fallback_provider}: {str(e)}")
        
        # Fallback final - retornar resposta básica
        return {
            'content': 'Sistema de IA temporariamente indisponível. Tente novamente mais tarde.',
            'provider': 'fallback',
            'model': 'none',
            'error': 'Todos os provedores de IA falharam'
        }
    
    def _is_provider_available(self, provider: str) -> bool:
        """Verifica se um provedor está disponível"""
        return (provider in self.providers and 
                self.providers[provider]['available'] and 
                self.providers[provider]['client'] is not None)
    
    def _call_provider(self, provider: str, model: str, messages: List[Dict], 
                      temperature: float, max_tokens: int) -> Dict:
        """Chama o provedor específico"""
        
        if provider == 'groq':
            return self._call_groq(model, messages, temperature, max_tokens)
        elif provider == 'openai':
            return self._call_openai(model, messages, temperature, max_tokens)
        elif provider == 'anthropic':
            return self._call_anthropic(model, messages, temperature, max_tokens)
        elif provider == 'google':
            return self._call_google(model, messages, temperature, max_tokens)
        elif provider in ['ollama_local', 'ollama_cloud']:
            return self._call_ollama(provider, model, messages, temperature, max_tokens)
        elif provider == 'deepseek':
            return self._call_deepseek(model, messages, temperature, max_tokens)
        elif provider == 'maritaca':
            return self._call_maritaca(model, messages, temperature, max_tokens)
        elif provider == 'zhipu':
            return self._call_zhipu(model, messages, temperature, max_tokens)
        else:
            raise ValueError(f"Provedor não suportado: {provider}")
    
    def _call_groq(self, model: str, messages: List[Dict], temperature: float, max_tokens: int) -> Dict:
        """Chama API Groq"""
        response = self.providers['groq']['client'].chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return {
            'content': response.choices[0].message.content,
            'provider': 'groq',
            'model': model
        }
    
    def _call_openai(self, model: str, messages: List[Dict], temperature: float, max_tokens: int) -> Dict:
        """Chama API OpenAI"""
        response = self.providers['openai']['client'].chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return {
            'content': response.choices[0].message.content,
            'provider': 'openai',
            'model': model
        }
    
    def _call_anthropic(self, model: str, messages: List[Dict], temperature: float, max_tokens: int) -> Dict:
        """Chama API Anthropic"""
        # Converter mensagens para formato Anthropic
        system_message = ""
        user_messages = []
        
        for msg in messages:
            if msg['role'] == 'system':
                system_message = msg['content']
            else:
                user_messages.append(msg['content'])
        
        user_content = "\n".join(user_messages)
        
        response = self.providers['anthropic']['client'].messages.create(
            model=model,
            system=system_message,
            messages=[{"role": "user", "content": user_content}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return {
            'content': response.content[0].text,
            'provider': 'anthropic',
            'model': model
        }
    
    def _call_google(self, model: str, messages: List[Dict], temperature: float, max_tokens: int) -> Dict:
        """Chama API Google"""
        # Converter mensagens para formato Google
        contents = []
        for msg in messages:
            parts = [{"text": msg['content']}]
            contents.append({
                "role": "user" if msg['role'] == 'user' else "model",
                "parts": parts
            })
        
        model_obj = self.providers['google']['client'].GenerativeModel(model)
        response = model_obj.generate_content(
            contents,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens
            )
        )
        
        return {
            'content': response.text,
            'provider': 'google',
            'model': model
        }

    def _call_deepseek(self, model: str, messages: List[Dict], temperature: float, max_tokens: int) -> Dict:
        """Chama API DeepSeek (compatível com OpenAI)"""
        response = self.providers['deepseek']['client'].chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return {
            'content': response.choices[0].message.content,
            'provider': 'deepseek',
            'model': model
        }

    def _call_maritaca(self, model: str, messages: List[Dict], temperature: float, max_tokens: int) -> Dict:
        """Chama API Maritaca (compatível com OpenAI)"""
        response = self.providers['maritaca']['client'].chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return {
            'content': response.choices[0].message.content,
            'provider': 'maritaca',
            'model': model
        }

    def _call_zhipu(self, model: str, messages: List[Dict], temperature: float, max_tokens: int) -> Dict:
        """Chama API Zhipu AI (GLM-4)"""
        response = self.providers['zhipu']['client'].chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=0.7 # Recomendado para GLM-4
        )
        
        return {
            'content': response.choices[0].message.content,
            'provider': 'zhipu',
            'model': model
        }

    def _call_ollama(self, provider: str, model: str, messages: List[Dict], temperature: float, max_tokens: int) -> Dict:
        """Chama Ollama (local ou cloud)"""
        # Converter mensagens para formato Ollama
        ollama_messages = []
        for msg in messages:
            ollama_messages.append({
                "role": msg['role'],
                "content": msg['content']
            })
        
        response = self.providers[provider]['client'].chat(
            model=model,
            messages=ollama_messages,
            options={
                "temperature": temperature,
                "num_predict": max_tokens
            }
        )
        
        return {
            'content': response['message']['content'],
            'provider': provider,
            'model': model
        }

# Instância global do gerenciador de IA
ai_manager = AIProviderManager()

def handle_ai_errors(f):
    """Decorator para tratar erros de IA"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Erro na função de IA {f.__name__}: {str(e)}")
            return {
                'error': f'Erro de IA: {str(e)}',
                'fallback_used': True
            }
    return decorated_function

@handle_ai_errors
def process_evolution_input(evolution_text_input: str, timeout: int = 30) -> Dict:
    """Processa entrada de evolução com IA"""
    
    system_prompt = """Você é um assistente médico especializado em cannabis medicinal. 
    Analise o texto de evolução do paciente e extraia informações relevantes sobre:
    1. Sintomas relatados
    2. Efeitos do tratamento
    3. Observações importantes
    4. Sugestões para ajustes
    
    Retorne um JSON estruturado com essas informações."""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Analise esta evolução: {evolution_text_input}"}
    ]
    
    response = ai_manager.chat_completion(
        messages=messages,
        temperature=0.3,
        max_tokens=800
    )
    
    try:
        # Tentar parsear JSON da resposta
        content = response['content']
        if content.startswith('```json'):
            content = content[7:-3]  # Remover markdown code blocks
        analysis = json.loads(content)
    except:
        # Fallback se não conseguir parsear JSON
        analysis = {
            'narrative_evolution': response['content'],
            'symptoms_detected': [],
            'treatment_effects': 'Análise não estruturada disponível',
            'observations': 'IA processou mas não retornou estrutura esperada',
            'suggestions': []
        }
    
    return {
        **analysis,
        'ai_provider': response.get('provider', 'unknown'),
        'ai_model': response.get('model', 'unknown')
    }

@handle_ai_errors
def process_import_data(text_content: str, patient_id: int) -> Dict:
    """Processa dados de importação com IA"""
    
    system_prompt = """Você é um assistente médico especializado em importação de dados de pacientes.
    Analise o texto fornecido e identifique:
    1. Evoluções clínicas
    2. Dosagens de medicamentos
    3. Sintomas relatados
    4. Datas relevantes
    
    Estruture os dados para importação no sistema de prontuário."""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Analise estes dados para importação: {text_content}"}
    ]
    
    response = ai_manager.chat_completion(
        messages=messages,
        temperature=0.2,
        max_tokens=1200
    )
    
    try:
        content = response['content']
        if content.startswith('```json'):
            content = content[7:-3]
        structured_data = json.loads(content)
    except:
        # Fallback básico
        structured_data = {
            'tipo': 'evolucao',
            'evolucoes': [{'descricao': text_content[:1000]}],
            'dosagens': [],
            'sintomas': [],
            'confianca': 50
        }
    
    return {
        **structured_data,
        'ai_provider': response.get('provider', 'unknown'),
        'ai_model': response.get('model', 'unknown')
    }

@handle_ai_errors
def chat_with_data(question: str, context: Dict) -> Dict:
    """Permite conversar com os dados do paciente usando IA"""
    
    system_prompt = f"""Você é um assistente médico analisando dados do paciente {context.get('paciente', {}).get('nome', 'desconhecido')}.
    
    Dados disponíveis:
    - Evoluções: {len(context.get('evolucoes', []))} registros
    - Dosagens: {len(context.get('dosagens', []))} registros  
    - Sintomas: {len(context.get('sintomas', []))} registros
    
    Forneça insights úteis baseados nos dados disponíveis."""
    
    # Preparar contexto detalhado
    context_text = f"""
    Paciente: {context.get('paciente', {}).get('nome', 'N/A')}
    Condição: {context.get('paciente', {}).get('condicao_medica', 'N/A')}
    
    Últimas evoluções:
    {json.dumps(context.get('evolucoes', [])[:3], ensure_ascii=False, indent=2)}
    
    Últimas dosagens:
    {json.dumps(context.get('dosagens', [])[:3], ensure_ascii=False, indent=2)}
    
    Últimos sintomas:
    {json.dumps(context.get('sintomas', [])[:5], ensure_ascii=False, indent=2)}
    """
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Contexto: {context_text}\n\nPergunta: {question}"}
    ]
    
    response = ai_manager.chat_completion(
        messages=messages,
        temperature=0.5,
        max_tokens=1500
    )
    
    return {
        'resposta': response['content'],
        'dados_citados': ['evolucoes', 'dosagens', 'sintomas'],  # Simplificado
        'insights': ['Análise baseada nos dados disponíveis'],
        'sugestoes': ['Considere revisar os dados completos para análise mais detalhada'],
        'ai_provider': response.get('provider', 'unknown'),
        'ai_model': response.get('model', 'unknown')
    }

@handle_ai_errors  
def process_text_file(file_path: str) -> Dict:
    """Processa arquivo de texto com IA"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return process_import_data(content, 0)  # patient_id 0 para processamento genérico
    except Exception as e:
        return {'error': f'Erro ao processar arquivo: {str(e)}'}

# Funções de fallback para quando IA não está disponível
def fallback_evolution_processing(text: str) -> Dict:
    """Fallback para processamento de evolução sem IA"""
    return {
        'narrative_evolution': text,
        'symptoms_detected': ['Processamento manual necessário'],
        'treatment_effects': 'Análise não disponível',
        'observations': 'Sistema de IA indisponível',
        'suggestions': ['Revise manualmente os dados'],
        'fallback_used': True
    }

def fallback_import_processing(text: str, patient_id: int) -> Dict:
    """Fallback para importação sem IA"""
    return {
        'tipo': 'evolucao',
        'evolucoes': [{'descricao': text[:1000]}],
        'dosagens': [],
        'sintomas': [],
        'confianca': 0,
        'fallback_used': True
    }

# Versão otimizada com timeout
def process_evolution_input_optimized(evolution_text_input: str, timeout: int = 30) -> Dict:
    """Versão otimizada do processamento de evolução"""
    try:
        return process_evolution_input(evolution_text_input)
    except Exception as e:
        logger.warning(f"Erro no processamento otimizado: {str(e)}")
        return fallback_evolution_processing(evolution_text_input)
