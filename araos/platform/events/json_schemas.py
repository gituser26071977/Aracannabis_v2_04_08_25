"""
AraOS Platform — JSON Schemas for Events.

Gera schemas JSON para validação e documentação automática.
Integra com o catálogo para garantir consistência.
"""

from typing import Dict, Any, Optional
from dataclasses import asdict
from .catalog import EventCatalog, EventDefinition


class SchemaRegistry:
    """
    Registro de schemas para payloads de eventos.
    
    Cada evento no catálogo pode ter um schema de payload definido aqui.
    Schemas seguem formato simplificado (não JSON Schema completo).
    """
    
    def __init__(self):
        self._schemas: Dict[str, Dict[str, Any]] = {}
        self._register_defaults()
    
    def _register_defaults(self):
        """Registra schemas padrão para os eventos mais comuns."""
        
        self._schemas["PATIENT_CREATED"] = {
            "patient_id": "string (UUID)",
            "patient_uuid": "string (UUID4)",
            "nome": "string",
            "cpf": "string (masked)",
            "email": "string",
            "telefone": "string",
            "data_nascimento": "string (ISO8601 date)",
            "clinic_id": "string",
            "created_by": "string (user_id)",
        }
        
        self._schemas["CONSULTATION_STARTED"] = {
            "consultation_id": "string (UUID)",
            "patient_id": "string (UUID)",
            "doctor_id": "string (UUID)",
            "clinic_id": "string",
            "room_id": "string (optional)",
            "scheduled_at": "string (ISO8601 datetime)",
            "started_at": "string (ISO8601 datetime)",
        }
        
        self._schemas["CONSULTATION_FINISHED"] = {
            "consultation_id": "string (UUID)",
            "finished_at": "string (ISO8601 datetime)",
            "duration_minutes": "integer",
            "evolution_summary": "string (optional)",
        }
        
        self._schemas["EVOLUTION_CREATED"] = {
            "evolution_id": "string (UUID)",
            "consultation_id": "string (UUID)",
            "patient_id": "string (UUID)",
            "doctor_id": "string (UUID)",
            "content": "string",
            "created_at": "string (ISO8601 datetime)",
        }
        
        self._schemas["PRESCRIPTION_CREATED"] = {
            "prescription_id": "string (UUID)",
            "consultation_id": "string (UUID)",
            "patient_id": "string (UUID)",
            "doctor_id": "string (UUID)",
            "medications": "array of objects",
            "dosage_instructions": "string",
            "valid_until": "string (ISO8601 date)",
        }
        
        self._schemas["DOCUMENT_UPLOADED"] = {
            "document_id": "string (UUID)",
            "patient_id": "string (UUID)",
            "document_type": "string (ex: 'receita', 'atestado', 'exame')",
            "file_name": "string",
            "file_size": "integer (bytes)",
            "mime_type": "string",
            "uploaded_by": "string (user_id)",
        }
        
        self._schemas["DOCUMENT_PROCESSED"] = {
            "document_id": "string (UUID)",
            "processing_status": "string (success|partial|failed)",
            "extracted_fields": "object (optional)",
            "confidence_score": "float (0-1)",
        }
        
        self._schemas["WHATSAPP_RECEIVED"] = {
            "message_id": "string",
            "sender_phone": "string",
            "message_body": "string",
            "message_type": "string (text|image|document|audio)",
            "received_at": "string (ISO8601 datetime)",
            "media_url": "string (optional)",
        }
        
        self._schemas["WHATSAPP_SENT"] = {
            "message_id": "string",
            "recipient_phone": "string",
            "message_body": "string",
            "message_type": "string (text|image|document|template)",
            "sent_at": "string (ISO8601 datetime)",
            "template_name": "string (optional)",
        }
        
        self._schemas["VOICE_SESSION_STARTED"] = {
            "session_id": "string (UUID)",
            "patient_id": "string (UUID, optional)",
            "consultation_id": "string (UUID, optional)",
            "room_id": "string (optional)",
            "device_id": "string (optional)",
            "language": "string (default: 'pt-BR')",
        }
        
        self._schemas["VOICE_SESSION_ENDED"] = {
            "session_id": "string (UUID)",
            "duration_seconds": "integer",
            "transcript_count": "integer",
            "final_state": "string (completed|timeout|error|manual_close)",
        }
        
        self._schemas["CHECKIN_COMPLETED"] = {
            "checkin_id": "string (UUID)",
            "patient_id": "string (UUID)",
            "consultation_id": "string (UUID, optional)",
            "room_id": "string",
            "biometric_confidence": "float (0-1, optional)",
            "checkin_method": "string (face|qr|manual)",
        }
        
        self._schemas["PATIENT_ENTERED_ROOM"] = {
            "event_id": "string (UUID)",
            "patient_id": "string (UUID)",
            "room_id": "string",
            "timestamp": "string (ISO8601 datetime)",
            "camera_id": "string",
        }
        
        self._schemas["PATIENT_LEFT_ROOM"] = {
            "event_id": "string (UUID)",
            "patient_id": "string (UUID)",
            "room_id": "string",
            "timestamp": "string (ISO8601 datetime)",
            "camera_id": "string",
        }
        
        self._schemas["WAIT_TIME_EXCEEDED"] = {
            "alert_id": "string (UUID)",
            "patient_id": "string (UUID)",
            "consultation_id": "string (UUID)",
            "room_id": "string",
            "wait_duration_minutes": "integer",
            "threshold_minutes": "integer",
        }
        
        self._schemas["LOGIN_SUCCEEDED"] = {
            "user_id": "string (UUID)",
            "email": "string",
            "login_method": "string (password|google|biometric)",
            "ip_address": "string",
            "user_agent": "string",
            "session_id": "string",
        }
        
        self._schemas["LOGIN_FAILED"] = {
            "email": "string",
            "failure_reason": "string (invalid_password|account_locked|expired|unknown)",
            "ip_address": "string",
            "attempt_count": "integer",
        }
        
        self._schemas["INVOICE_CREATED"] = {
            "invoice_id": "string (UUID)",
            "patient_id": "string (UUID)",
            "consultation_id": "string (UUID, optional)",
            "amount": "float",
            "currency": "string (default: 'BRL')",
            "due_date": "string (ISO8601 date)",
            "gateway": "string (asaas|mercadopago|stripe)",
        }
        
        self._schemas["PAYMENT_RECEIVED"] = {
            "payment_id": "string (UUID)",
            "invoice_id": "string (UUID)",
            "amount": "float",
            "currency": "string",
            "gateway": "string",
            "gateway_payment_id": "string",
            "paid_at": "string (ISO8601 datetime)",
        }
        
        self._schemas["DATA_EXPORT_REQUESTED"] = {
            "request_id": "string (UUID)",
            "patient_id": "string (UUID)",
            "request_type": "string (full|partial|anonymized)",
            "requested_by": "string (user_id or patient)",
            "legal_basis": "string (LGPD article reference)",
        }
        
        self._schemas["DATA_PURGED"] = {
            "purge_id": "string (UUID)",
            "patient_id": "string (UUID)",
            "deleted_records": "integer",
            "deleted_documents": "integer",
            "purged_at": "string (ISO8601 datetime)",
            "legal_basis": "string (LGPD article reference)",
        }
    
    def get_schema(self, event_type: str) -> Optional[Dict[str, Any]]:
        """Retorna schema de payload para um evento."""
        return self._schemas.get(event_type)
    
    def register_schema(self, event_type: str, schema: Dict[str, Any]) -> None:
        """
        Registra ou atualiza schema de um evento.
        
        Use para eventos customizados de módulos externos.
        """
        self._schemas[event_type] = schema
    
    def list_registered(self) -> list:
        """Lista todos os eventos com schemas registrados."""
        return sorted(self._schemas.keys())
    
    def validate_payload_keys(self, event_type: str, payload: Dict[str, Any]) -> tuple:
        """
        Valida que um payload contém as chaves esperadas pelo schema.
        
        Returns:
            (is_valid: bool, missing_keys: list, extra_keys: list)
        """
        schema = self.get_schema(event_type)
        if not schema:
            return True, [], []
        
        expected = set(schema.keys())
        actual = set(payload.keys())
        
        missing = list(expected - actual)
        extra = list(actual - expected)
        
        return len(missing) == 0, missing, extra
    
    def generate_openapi_component(self, event_type: str) -> Dict[str, Any]:
        """
        Gera componente OpenAPI para um evento.
        
        Útil para documentação Swagger/OpenAPI dos endpoints de eventos.
        """
        schema = self.get_schema(event_type)
        catalog = EventCatalog()
        defn = catalog.get_definition(event_type)
        
        if not schema:
            return {"description": f"No schema registered for {event_type}"}
        
        properties = {}
        for key, type_hint in schema.items():
            # Converte type_hint em tipo OpenAPI
            if "string" in type_hint:
                prop_type = "string"
            elif "integer" in type_hint:
                prop_type = "integer"
            elif "float" in type_hint:
                prop_type = "number"
            elif "boolean" in type_hint:
                prop_type = "boolean"
            elif "array" in type_hint:
                prop_type = "array"
            elif "object" in type_hint:
                prop_type = "object"
            else:
                prop_type = "string"
            
            properties[key] = {
                "type": prop_type,
                "description": type_hint,
            }
        
        return {
            "type": "object",
            "description": defn.description if defn else event_type,
            "properties": properties,
        }


def get_schema_registry() -> SchemaRegistry:
    """Factory para SchemaRegistry singleton."""
    return _schema_registry


_schema_registry = SchemaRegistry()
