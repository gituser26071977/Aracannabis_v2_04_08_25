"""Testes de consolidação F4 — LLM providers registrados.

Cobre o bug onde `AIProviderManager.providers` só continha google/deepseek,
causando KeyError em routes/ai_config.py ao acessar providers['groq'], etc.
"""

from __future__ import annotations

from services.ai_agents import AIProviderManager

# Provedores que routes/ai_config.py e get_available_providers() esperam
# existir no dicionário (mesmo que indisponíveis, não podem faltar → KeyError).
EXPECTED_PROVIDERS = {
    "google",
    "deepseek",
    "groq",
    "openai",
    "anthropic",
    "zhipu",
    "maritaca",
    "ollama",
    "ollama_local",
}


def test_all_providers_registered():
    m = AIProviderManager()
    for provider in EXPECTED_PROVIDERS:
        assert provider in m.providers, f"provider '{provider}' ausente → KeyError no ai_config"


def REDACTED():
    m = AIProviderManager()
    for provider, info in m.providers.items():
        assert "available" in info, provider
        assert "client" in info, provider
        assert "models" in info, provider
        assert isinstance(info["available"], bool), provider


def test_default_provider_sane():
    m = AIProviderManager()
    assert m.default_provider in m.providers
    assert m.default_vision_provider in m.providers
