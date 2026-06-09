"""
Bridge AraOS ↔ Visual Smart Flow (VSF)

Responsável por:
- Autenticar no VSF e gerenciar token JWT
- Criar agendamentos no VSF quando consultas são agendadas no AraOS
- Fazer enrollment facial de pacientes
- Identificar pacientes por foto (login/check-in)
- Receber webhooks do VSF e atualizar status no AraOS
"""

import os
import json
import base64
import logging
import requests
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List

import redis

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Configuração
# ──────────────────────────────────────────────

VSF_BASE_URL = os.getenv("VSF_BASE_URL", "https://visualsmartflow.com.br/api")
VSF_EMAIL = os.getenv("VSF_EMAIL", "admin@arapath.com.br")
VSF_PASSWORD = os.getenv("VSF_PASSWORD", "")
VSF_ORG_ID = os.getenv("VSF_ORG_ID", "araos-org-001")

REDIS_HOST = os.getenv("REDIS_HOST", "siap-redis")
r = redis.Redis(host=REDIS_HOST, port=6379, db=2, decode_responses=True)

TOKEN_KEY = "vsf:access_token"
TOKEN_EXP_KEY = "vsf:token_exp"


class VSFAuthError(Exception):
    pass


class VSFBridge:
    """Cliente para integração com Visual Smart Flow."""

    def __init__(self):
        self.base_url = VSF_BASE_URL.rstrip("/")
        self.email = VSF_EMAIL
        self.password = VSF_PASSWORD
        self._token: Optional[str] = None

    # ──────────────────────────────────────────────
    # Autenticação
    # ──────────────────────────────────────────────

    def _get_cached_token(self) -> Optional[str]:
        """Recupera token do cache Redis se ainda válido."""
        try:
            token = r.get(TOKEN_KEY)
            exp_str = r.get(TOKEN_EXP_KEY)
            if not token or not exp_str:
                return None
            exp = datetime.fromtimestamp(int(exp_str), tz=timezone.utc)
            # Considera expirado 5 min antes para segurança
            if datetime.now(timezone.utc) > exp - timedelta(minutes=5):
                return None
            return token
        except Exception as e:
            logger.warning(f"Erro ao ler token do cache: {e}")
            return None

    def _cache_token(self, token: str, exp_timestamp: int):
        """Armazena token no Redis com TTL próximo da expiração."""
        try:
            ttl = max(60, exp_timestamp - int(datetime.now(timezone.utc).timestamp()))
            r.setex(TOKEN_KEY, ttl, token)
            r.setex(TOKEN_EXP_KEY, ttl, str(exp_timestamp))
        except Exception as e:
            logger.warning(f"Erro ao cachear token: {e}")

    def _decode_exp(self, token: str) -> int:
        """Decodifica expiração do token JWT (sem validar assinatura)."""
        try:
            payload = token.split(".")[1]
            # Adicionar padding se necessário
            payload += "=" * (4 - len(payload) % 4)
            data = json.loads(base64.b64decode(payload))
            return int(data.get("exp", 0))
        except Exception:
            return 0

    def get_token(self, force_refresh: bool = False) -> str:
        """Obtém token JWT válido, fazendo login se necessário."""
        if not force_refresh:
            cached = self._get_cached_token()
            if cached:
                return cached

        if not self.email or not self.password:
            raise VSFAuthError("VSF_EMAIL e VSF_PASSWORD devem estar configurados")

        url = f"{self.base_url}/auth/login"
        payload = {"email": self.email, "password": self.password}

        try:
            resp = requests.post(url, json=payload, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            token = data.get("access_token")
            if not token:
                raise VSFAuthError("Token não retornado pelo VSF")

            exp = self._decode_exp(token)
            if exp:
                self._cache_token(token, exp)
            else:
                # Fallback: cache por 23 horas
                self._cache_token(token, int((datetime.now(timezone.utc) + timedelta(hours=23)).timestamp()))

            logger.info("Token VSF obtido com sucesso")
            return token
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao autenticar no VSF: {e}")
            raise VSFAuthError(f"Falha na autenticação VSF: {e}")

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.get_token()}",
            "Content-Type": "application/json",
        }

    # ──────────────────────────────────────────────
    # Agendamentos
    # ──────────────────────────────────────────────

    def criar_agendamento(
        self,
        patient_name: str,
        patient_external_id: str,
        scheduled_for: datetime,
        exam_type: str = "consulta",
        room_id: Optional[str] = None,
        professional_id: Optional[str] = None,
        exam_duration_minutes: int = 30,
    ) -> Dict[str, Any]:
        """Cria um agendamento no VSF vinculado a um paciente do AraOS."""
        url = f"{self.base_url}/appointments"

        payload = {
            "patient_name": patient_name,
            "patient_external_id": patient_external_id,
            "scheduled_for": scheduled_for.isoformat(),
            "exam_type": exam_type,
            "room_id": room_id,
            "professional_id": professional_id,
            "exam_duration_minutes": exam_duration_minutes,
        }

        try:
            resp = requests.post(url, json=payload, headers=self._headers(), timeout=15)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"Erro HTTP ao criar agendamento VSF: {e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de rede ao criar agendamento VSF: {e}")
            raise

    def buscar_agendamentos_hoje(self) -> List[Dict[str, Any]]:
        """Busca agendamentos de hoje no VSF."""
        url = f"{self.base_url}/appointments"
        try:
            resp = requests.get(url, headers=self._headers(), timeout=15)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Erro ao buscar agendamentos VSF: {e}")
            return []

    # ──────────────────────────────────────────────
    # Biometria Facial
    # ──────────────────────────────────────────────

    def enroll_face(
        self,
        appointment_id: str,
        image_base64: str,
        consent: bool = True,
    ) -> Dict[str, Any]:
        """Cadastra face do paciente para um agendamento no VSF."""
        url = f"{self.base_url}/appointments/{appointment_id}/enroll"

        # Limpar prefixo data:image/...;base64,
        if "," in image_base64:
            image_base64 = image_base64.split(",", 1)[1]

        image_bytes = base64.b64decode(image_base64)

        try:
            files = {"image": ("face.jpg", image_bytes, "image/jpeg")}
            data = {"consent": str(consent).lower()}
            # Envio multipart precisa remover Content-Type json
            headers = {"Authorization": f"Bearer {self.get_token()}"}
            resp = requests.post(url, files=files, data=data, headers=headers, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"Erro HTTP no enrollment VSF: {e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de rede no enrollment VSF: {e}")
            raise

    def identify_by_face(self, image_base64: str) -> Optional[Dict[str, Any]]:
        """Identifica paciente por foto no VSF."""
        url = f"{self.base_url}/appointments/identify"

        if "," in image_base64:
            image_base64 = image_base64.split(",", 1)[1]

        image_bytes = base64.b64decode(image_base64)

        try:
            files = {"image": ("face.jpg", image_bytes, "image/jpeg")}
            headers = {"Authorization": f"Bearer {self.get_token()}"}
            resp = requests.post(url, files=files, headers=headers, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"Erro HTTP na identificação VSF: {e.response.text}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de rede na identificação VSF: {e}")
            return None

    def marcar_chegada(self, appointment_id: str, sensor_id: str = "araos-recepcao-01") -> Dict[str, Any]:
        """Marca chegada do paciente no VSF (chamado pelo VSF mesmo, mas disponível)."""
        url = f"{self.base_url}/appointments/{appointment_id}/arrived"
        try:
            resp = requests.post(url, json={"sensor_id": sensor_id}, headers=self._headers(), timeout=15)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Erro ao marcar chegada VSF: {e}")
            raise

    # ──────────────────────────────────────────────
    # Webhook Handler (VSF → AraOS)
    # ──────────────────────────────────────────────

    def handle_patient_arrived(self, vsf_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Processa evento de chegada do paciente vindo do VSF."""
        patient_id = vsf_payload.get("patient_id")
        appointment_id = vsf_payload.get("appointment_id")
        patient_name = vsf_payload.get("patient_name")
        confidence = vsf_payload.get("confidence")

        logger.info(
            f"[VSF Bridge] Paciente chegou: {patient_name} "
            f"(patient_id={patient_id}, appointment_id={appointment_id}, confidence={confidence})"
        )

        # TODO: Aqui integraremos com o AraOS para atualizar status da consulta
        # Na implementação real, buscar consulta no AraOS pelo patient_external_id
        # e atualizar status para 'paciente_chegou'
        return {
            "status": "received",
            "action": "check_in",
            "patient_id": patient_id,
            "appointment_id": appointment_id,
            "patient_name": patient_name,
            "confidence": confidence,
        }


# Instância global
vsf_bridge = VSFBridge()
