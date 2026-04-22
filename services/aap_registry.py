"""
AAP — Registry de Agentes

Armazena e descobre Agent Cards via Redis.
Fallback para dicionário em memória quando Redis não está disponível.
"""

import os
import json
from typing import Optional, Dict, Any

# Tentar importar redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_PREFIX = "aap:agents"


class AAPRegistry:
    """Registry simples de Agent Cards."""

    def __init__(self):
        self._memory: Dict[str, Dict[str, Any]] = {}
        self._redis = None
        if REDIS_AVAILABLE:
            try:
                self._redis = redis.from_url(REDIS_URL, decode_responses=True)
                self._redis.ping()
            except Exception as e:
                print(f"[AAP Registry] Redis indisponível, usando memória: {e}")
                self._redis = None

    def register(self, agent_name: str, agent_card: Dict[str, Any]) -> bool:
        """Registra ou atualiza um Agent Card."""
        try:
            data = json.dumps(agent_card, ensure_ascii=False)
            if self._redis:
                self._redis.set(f"{REDIS_PREFIX}:{agent_name}", data)
            self._memory[agent_name] = agent_card
            return True
        except Exception as e:
            print(f"[AAP Registry] Erro ao registrar {agent_name}: {e}")
            return False

    def get(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Recupera um Agent Card pelo nome."""
        try:
            if self._redis:
                data = self._redis.get(f"{REDIS_PREFIX}:{agent_name}")
                if data:
                    return json.loads(data)
            return self._memory.get(agent_name)
        except Exception as e:
            print(f"[AAP Registry] Erro ao recuperar {agent_name}: {e}")
            return self._memory.get(agent_name)

    def list_agents(self) -> Dict[str, Dict[str, Any]]:
        """Lista todos os agentes registrados."""
        result = dict(self._memory)
        try:
            if self._redis:
                keys = self._redis.keys(f"{REDIS_PREFIX}:*")
                for key in keys:
                    name = key.decode() if isinstance(key, bytes) else key
                    name = name.replace(f"{REDIS_PREFIX}:", "")
                    data = self._redis.get(key)
                    if data:
                        result[name] = json.loads(data.decode() if isinstance(data, bytes) else data)
        except Exception as e:
            print(f"[AAP Registry] Erro ao listar: {e}")
        return result

    def unregister(self, agent_name: str) -> bool:
        """Remove um agente do registry."""
        try:
            if self._redis:
                self._redis.delete(f"{REDIS_PREFIX}:{agent_name}")
            self._memory.pop(agent_name, None)
            return True
        except Exception as e:
            print(f"[AAP Registry] Erro ao remover {agent_name}: {e}")
            return False


# Singleton global
_registry = None

def get_registry() -> AAPRegistry:
    global _registry
    if _registry is None:
        _registry = AAPRegistry()
    return _registry
