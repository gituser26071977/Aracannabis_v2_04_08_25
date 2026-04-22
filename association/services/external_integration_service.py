"""
External Association Service — AAP (Arapath Agent Protocol)

Comunicação SIAP ↔ SGAC via protocolo padronizado AAP.
Substitui as chamadas HTTP diretas quebradas (JWT auth mismatch)
por delegação de tasks via Agent-to-Agent.

Mantém compatibilidade com a interface antiga:
  - search_associate(cpf) -> dict|None
  - sync_patient_to_association(paciente_data) -> bool
"""

import os
import re

# AAP imports
from services.aap_protocol import AAPClient, build_agent_card
from services.aap_registry import get_registry


class ExternalAssociationService:
    """Cliente AAP para comunicação com SGAC (Agrobuds)."""

    @staticmethod
    def _get_aap_client() -> AAPClient:
        """Factory do cliente AAP para o SGAC."""
        sgac_url = os.getenv("SGAC_AAP_URL", os.getenv("EXTERNAL_ASSOC_API_URL", "http://host.docker.internal:8011"))
        api_key = os.getenv("AAP_API_KEY")
        secret_key = os.getenv("AAP_SECRET_KEY")
        return AAPClient(agent_url=sgac_url, api_key=api_key, secret_key=secret_key)

    @staticmethod
    def _normalize_cpf(cpf: str) -> str:
        return re.sub(r"\D", "", cpf or "")

    @staticmethod
    def search_associate(cpf: str):
        """
        Busca associado no SGAC via AAP.
        Retorna dicionário normalizado ou None.
        """
        client = ExternalAssociationService._get_aap_client()
        clean_cpf = ExternalAssociationService._normalize_cpf(cpf)

        try:
            # Descoberta opcional (cacheia no registry)
            registry = get_registry()
            if not registry.get("sgac-agrobuds"):
                card = client.discover()
                if card:
                    registry.register("sgac-agrobuds", card)

            # Delega task ao SGAC
            result = client.submit_task(
                capability_id="member.search",
                method="search_by_cpf",
                params={"query": clean_cpf, "association_id": int(os.getenv("EXTERNAL_ASSOC_ID", "1"))},
            )

            if not result:
                print("[AAP] search_associate: sem resposta do SGAC")
                return None

            task_id = result["task_id"]

            # Tasks síncronas do mock SGAC retornam completed imediatamente;
            # em produção real pode ser async, então fazemos polling simples.
            import time
            for _ in range(10):
                task = client.get_task(task_id)
                if task and task["status"] in ("completed", "failed"):
                    break
                time.sleep(0.3)

            if not task or task["status"] != "completed":
                print(f"[AAP] search_associate: task {task_id} não completou")
                return None

            members = task.get("result", [])
            if not members or not isinstance(members, list):
                return None

            member_data = members[0]
            return {
                "nome": member_data.get("full_name"),
                "email": member_data.get("email"),
                "telefone": member_data.get("phone"),
                "endereco": member_data.get("address"),
                "data_nascimento": member_data.get("data_nascimento"),
                "rg": member_data.get("rg"),
                "id": member_data.get("id"),
                "external_id": member_data.get("id"),
            }

        except Exception as e:
            print(f"[AAP] Erro em search_associate: {e}")
            return None

    @staticmethod
    def sync_patient_to_association(paciente_data: dict) -> bool:
        """
        Sincroniza paciente do SIAP para o SGAC via AAP.
        Decide CREATE vs UPDATE baseado em search_associate.
        """
        client = ExternalAssociationService._get_aap_client()
        cpf_clean = ExternalAssociationService._normalize_cpf(paciente_data.get("cpf", ""))
        assoc_id = int(os.getenv("EXTERNAL_ASSOC_ID", "1"))

        if not cpf_clean:
            print("[AAP] sync_patient: CPF ausente, abortando")
            return False

        try:
            # 1. Verifica se já existe
            existing = ExternalAssociationService.search_associate(cpf_clean)

            # 2. Monta payload
            data_nascimento = paciente_data.get("data_nascimento")
            if hasattr(data_nascimento, "isoformat"):
                data_nascimento = data_nascimento.isoformat()

            payload = {
                "full_name": paciente_data.get("nome"),
                "cpf": cpf_clean,
                "email": paciente_data.get("email"),
                "phone": paciente_data.get("telefone"),
                "address": paciente_data.get("endereco"),
                "data_nascimento": data_nascimento,
                "association_id": assoc_id,
            }

            if existing and existing.get("id"):
                # UPDATE via AAP
                member_id = existing["id"]
                print(f"[AAP] Sync UPDATE member {member_id}...")
                result = client.submit_task(
                    capability_id="member.update",
                    method="update_member",
                    params={
                        "member_id": member_id,
                        "updates": payload,
                    },
                )
            else:
                # CREATE via AAP
                print(f"[AAP] Sync CREATE member in association {assoc_id}...")
                result = client.submit_task(
                    capability_id="member.create",
                    method="create_member",
                    params=payload,
                )

            if not result:
                print("[AAP] sync_patient: sem resposta do SGAC")
                return False

            # 3. Aguarda conclusão (polling)
            import time
            task_id = result["task_id"]
            for _ in range(15):
                task = client.get_task(task_id)
                if task and task["status"] in ("completed", "failed"):
                    break
                time.sleep(0.3)

            if not task:
                print(f"[AAP] sync_patient: task {task_id} não encontrada")
                return False

            if task["status"] == "completed":
                print(f"[AAP] sync_patient: sucesso — {task.get('result')}")
                return True
            else:
                print(f"[AAP] sync_patient: falha — {task.get('error')}")
                return False

        except Exception as e:
            print(f"[AAP] Erro em sync_patient_to_association: {e}")
            return False
