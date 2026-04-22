"""
AAP — Arapath Agent Protocol
Cliente e utilitários para comunicação agent-to-agent.

Baseado em conceitos do A2A (Google/Linux Foundation) mas simplificado
para Flask/FastAPI sem dependências externas pesadas.
"""

import os
import json
import uuid
import time
import hmac
import hashlib
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Callable
import requests


# ── Configuração ──
AAP_API_KEY = os.getenv("AAP_API_KEY")
AAP_SECRET_KEY = os.getenv("AAP_SECRET_KEY")
AAP_REGISTRY_URL = os.getenv("AAP_REGISTRY_URL")
AAP_DEFAULT_TIMEOUT = int(os.getenv("AAP_DEFAULT_TIMEOUT", "30"))


class AAPClient:
    """Cliente HTTP para o protocolo AAP."""

    def __init__(self, agent_url: str, api_key: Optional[str] = None, secret_key: Optional[str] = None):
        self.agent_url = agent_url.rstrip("/")
        self.api_key = api_key or AAP_API_KEY
        self.secret_key = secret_key or AAP_SECRET_KEY
        self.session = requests.Session()

    def _headers(self, body: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "AAP-Client/1.0",
        }
        if self.api_key:
            headers["X-AAP-Key"] = self.api_key
        if self.secret_key and body:
            sig = hmac.new(
                self.secret_key.encode(),
                body.encode(),
                hashlib.sha256
            ).hexdigest()
            headers["X-AAP-Signature"] = sig
        return headers

    def discover(self) -> Optional[Dict[str, Any]]:
        """Busca o Agent Card de um agente remoto."""
        try:
            resp = self.session.get(
                f"{self.agent_url}/.well-known/agent.json",
                headers=self._headers(),
                timeout=10
            )
            if resp.status_code == 200:
                return resp.json()
            return None
        except Exception as e:
            print(f"[AAP] Erro ao descobrir agente {self.agent_url}: {e}")
            return None

    def submit_task(self, capability_id: str, method: str, params: Dict[str, Any],
                    callback_url: Optional[str] = None,
                    priority: str = "normal",
                    timeout_seconds: int = 300) -> Optional[Dict[str, Any]]:
        """Submete uma task para um agente remoto."""
        task_id = str(uuid.uuid4())
        payload = {
            "task_id": task_id,
            "capability_id": capability_id,
            "method": method,
            "params": params,
            "priority": priority,
            "timeout_seconds": timeout_seconds,
        }
        if callback_url:
            payload["callback_url"] = callback_url

        body = json.dumps(payload, ensure_ascii=False)
        try:
            resp = self.session.post(
                f"{self.agent_url}/aap/tasks",
                data=body.encode("utf-8"),
                headers=self._headers(body),
                timeout=AAP_DEFAULT_TIMEOUT
            )
            if resp.status_code in (200, 201, 202):
                return resp.json()
            else:
                print(f"[AAP] Erro ao submeter task: {resp.status_code} {resp.text}")
                return None
        except Exception as e:
            print(f"[AAP] Erro de rede ao submeter task: {e}")
            return None

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Consulta o status de uma task."""
        try:
            resp = self.session.get(
                f"{self.agent_url}/aap/tasks/{task_id}",
                headers=self._headers(),
                timeout=AAP_DEFAULT_TIMEOUT
            )
            if resp.status_code == 200:
                return resp.json()
            return None
        except Exception as e:
            print(f"[AAP] Erro ao consultar task {task_id}: {e}")
            return None

    def cancel_task(self, task_id: str) -> bool:
        """Cancela uma task."""
        try:
            resp = self.session.post(
                f"{self.agent_url}/aap/tasks/{task_id}/cancel",
                headers=self._headers(),
                timeout=AAP_DEFAULT_TIMEOUT
            )
            return resp.status_code in (200, 202, 204)
        except Exception as e:
            print(f"[AAP] Erro ao cancelar task {task_id}: {e}")
            return False

    def stream_events(self, task_id: str):
        """Generator que consome SSE de uma task."""
        import sseclient
        try:
            resp = self.session.get(
                f"{self.agent_url}/aap/tasks/{task_id}/events",
                headers=self._headers(),
                stream=True,
                timeout=AAP_DEFAULT_TIMEOUT
            )
            if resp.status_code == 200:
                client = sseclient.SSEClient(resp)
                for event in client.events():
                    yield event
            else:
                print(f"[AAP] SSE retornou {resp.status_code}")
        except Exception as e:
            print(f"[AAP] Erro no SSE da task {task_id}: {e}")


def verify_aap_request(request_headers: Dict[str, str], request_body: Optional[str] = None) -> bool:
    """Verifica se uma requisição AAP é autêntica."""
    api_key = request_headers.get("X-AAP-Key")
    if not api_key:
        return False

    expected_key = AAP_API_KEY
    if api_key != expected_key:
        return False

    signature = request_headers.get("X-AAP-Signature")
    if AAP_SECRET_KEY and signature:
        expected_sig = hmac.new(
            AAP_SECRET_KEY.encode(),
            (request_body or "").encode(),
            hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected_sig, signature):
            return False

    return True


def build_agent_card(
    name: str,
    version: str,
    description: str,
    url: str,
    capabilities: List[Dict[str, Any]],
    auth_type: str = "api_key",
    auth_header: str = "X-AAP-Key"
) -> Dict[str, Any]:
    """Constrói um Agent Card padronizado."""
    return {
        "name": name,
        "version": version,
        "description": description,
        "url": url,
        "capabilities": capabilities,
        "authentication": {
            "type": auth_type,
            "header": auth_header
        },
        "endpoints": {
            "tasks": "/aap/tasks",
            "events": "/aap/tasks/{id}/events",
            "health": "/aap/health"
        }
    }
