"""
Serviço de persistência de configurações de IA
Salva e carrega configurações de provedores, modelos e API keys
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Caminho do arquivo de configuração
CONFIG_DIR = Path(__file__).parent.parent / 'config'
CONFIG_FILE = CONFIG_DIR / 'ai_settings.json'

# Configuração padrão
DEFAULT_CONFIG = {
    # Configuração geral (fallback)
    "default_provider": "groq",
    "default_model": "llama-3.3-70b-versatile",
    
    # Chat & Análise de Evoluções
    "chat_provider": "groq",
    "chat_model": "llama-3.3-70b-versatile",
    
    # Visão & Imagens
    "vision_provider": "google",
    "vision_model": "gemini-2.0-flash-exp",
    
    # OCR & Documentos Simples
    "ocr_provider": "openai",
    "ocr_model": "gpt-4o",
    
    # Áudio & Transcrição
    "audio_provider": "openai",
    "audio_model": "whisper-1",
    
    # Planilhas & Dados Estruturados
    "spreadsheet_provider": "anthropic",
    "spreadsheet_model": "claude-3-5-sonnet-20241022",
    
    # PDFs Complexos
    "pdf_provider": "anthropic",
    "pdf_model": "claude-3-5-sonnet-20241022",
    
    # Mantém compatibilidade com código antigo
    "default_vision_provider": "google",
    "default_vision_model": "gemini-2.0-flash-exp",
    "default_multimodal_provider": "openai",
    "default_multimodal_model": "gpt-4o",
    
    "api_keys": {},
    "base_urls": {}
}

def ensure_config_dir():
    """Garante que o diretório de configuração existe"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def load_config() -> Dict[str, Any]:
    """
    Carrega as configurações do arquivo JSON.
    Se o arquivo não existir, retorna a configuração padrão.
    """
    try:
        ensure_config_dir()
        
        if not CONFIG_FILE.exists():
            logger.info("Arquivo de configuração não encontrado. Usando configuração padrão.")
            return DEFAULT_CONFIG.copy()
        
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        # Mesclar com defaults para garantir que todos os campos existam
        merged_config = DEFAULT_CONFIG.copy()
        merged_config.update(config)
        
        # Garantir que api_keys e base_urls existam
        if 'api_keys' not in merged_config:
            merged_config['api_keys'] = {}
        if 'base_urls' not in merged_config:
            merged_config['base_urls'] = {}
            
        logger.info(f"Configuração carregada de {CONFIG_FILE}")
        return merged_config
        
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar JSON de configuração: {e}")
        return DEFAULT_CONFIG.copy()
    except Exception as e:
        logger.error(f"Erro ao carregar configuração: {e}")
        return DEFAULT_CONFIG.copy()

def save_config(config: Dict[str, Any]) -> bool:
    """
    Salva as configurações no arquivo JSON.
    Retorna True se bem-sucedido, False caso contrário.
    """
    try:
        ensure_config_dir()
        
        # Validar estrutura básica
        if not isinstance(config, dict):
            logger.error("Configuração inválida: não é um dicionário")
            return False
        
        # Garantir que api_keys e base_urls existam
        if 'api_keys' not in config:
            config['api_keys'] = {}
        if 'base_urls' not in config:
            config['base_urls'] = {}
        
        # Salvar com indentação para legibilidade
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Configuração salva em {CONFIG_FILE}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao salvar configuração: {e}")
        return False

def get_api_key(provider: str) -> Optional[str]:
    """
    Obtém a API key de um provedor.
    Prioriza variáveis de ambiente, depois o arquivo de configuração.
    """
    # Primeiro tenta variável de ambiente
    env_var_map = {
        'openai': 'OPENAI_API_KEY',
        'groq': 'GROQ_API_KEY',
        'anthropic': 'ANTHROPIC_API_KEY',
        'google': 'GOOGLE_API_KEY',
        'deepseek': 'DEEPSEEK_API_KEY',
        'xai': 'XAI_API_KEY',
        'zhipu': 'ZHIPU_API_KEY'
    }
    
    env_var = env_var_map.get(provider)
    if env_var:
        env_key = os.getenv(env_var)
        if env_key:
            return env_key
    
    # Se não encontrar em env, busca no arquivo
    config = load_config()
    return config.get('api_keys', {}).get(provider)

def set_api_key(provider: str, api_key: str) -> bool:
    """
    Define a API key de um provedor e salva no arquivo.
    Também atualiza a variável de ambiente para a sessão atual.
    """
    config = load_config()
    config['api_keys'][provider] = api_key
    
    # Atualizar variável de ambiente também
    env_var_map = {
        'openai': 'OPENAI_API_KEY',
        'groq': 'GROQ_API_KEY',
        'anthropic': 'ANTHROPIC_API_KEY',
        'google': 'GOOGLE_API_KEY',
        'deepseek': 'DEEPSEEK_API_KEY',
        'xai': 'XAI_API_KEY',
        'zhipu': 'ZHIPU_API_KEY'
    }
    
    env_var = env_var_map.get(provider)
    if env_var:
        os.environ[env_var] = api_key
    
    return save_config(config)

def get_base_url(provider: str) -> Optional[str]:
    """Obtém a base URL de um provedor"""
    # Primeiro tenta variável de ambiente
    env_var_map = {
        'ollama_local': 'OLLAMA_BASE_URL',
        'ollama_cloud': 'OLLAMA_CLOUD_URL',
        'deepseek': 'DEEPSEEK_BASE_URL',
        'zhipu': 'ZHIPU_BASE_URL'
    }
    
    env_var = env_var_map.get(provider)
    if env_var:
        env_url = os.getenv(env_var)
        if env_url:
            return env_url
    
    # Se não encontrar em env, busca no arquivo
    config = load_config()
    return config.get('base_urls', {}).get(provider)

def set_base_url(provider: str, base_url: str) -> bool:
    """Define a base URL de um provedor e salva no arquivo"""
    config = load_config()
    config['base_urls'][provider] = base_url
    
    # Atualizar variável de ambiente também
    env_var_map = {
        'ollama_local': 'OLLAMA_BASE_URL',
        'ollama_cloud': 'OLLAMA_CLOUD_URL',
        'deepseek': 'DEEPSEEK_BASE_URL',
        'zhipu': 'ZHIPU_BASE_URL'
    }
    
    env_var = env_var_map.get(provider)
    if env_var:
        os.environ[env_var] = base_url
    
    return save_config(config)

def update_config(updates: Dict[str, Any]) -> bool:
    """
    Atualiza múltiplos campos da configuração de uma vez.
    """
    config = load_config()
    config.update(updates)
    return save_config(config)
