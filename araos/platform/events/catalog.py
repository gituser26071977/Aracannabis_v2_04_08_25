"""
AraOS Platform — Official Event Catalog.

Este é o CATÁLOGO CANÔNICO de eventos da plataforma.
NENHUM evento pode ser publicado sem estar registrado aqui.

Convenção de nomenclatura obrigatória:
    DOMAIN_ACTION

Exemplos válidos:
    PATIENT_CREATED
    CONSULTATION_STARTED
    VOICE_SESSION_ENDED

Exemplos INVÁLIDOS (não use):
    patientCreated      # camelCase não permitido
    patient-created     # kebab-case não permitido
    new_patient         # verbo ausente
    created_patient     # ordem invertida
"""

from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass


@dataclass
class EventDefinition:
    """Definição de um tipo de evento no catálogo."""
    event_type: str
    domain: str  # patient, consultation, voice, document, etc.
    action: str  # created, updated, deleted, started, finished
    aggregate_type: str
    description: str
    version: str = "1.0"
    consumers: List[str] = None  # Lista de consumer groups esperados
    sensitive: bool = False  # Se contém dados sensíveis (LGPD)
    
    def __post_init__(self):
        if self.consumers is None:
            self.consumers = []


# ═══════════════════════════════════════════════════════════════════════
# CATÁLOGO OFICIAL DE EVENTOS
# ═══════════════════════════════════════════════════════════════════════

_EVENT_CATALOG: Dict[str, EventDefinition] = {
    
    # ─── PACIENTE ────────────────────────────────────────────────────
    "PATIENT_CREATED": EventDefinition(
        event_type="PATIENT_CREATED",
        domain="patient",
        action="created",
        aggregate_type="patient",
        description="Novo paciente cadastrado",
        consumers=["audit", "knowledge", "concierge"],
        sensitive=True,
    ),
    "PATIENT_UPDATED": EventDefinition(
        event_type="PATIENT_UPDATED",
        domain="patient",
        action="updated",
        aggregate_type="patient",
        description="Dados do paciente atualizados",
        consumers=["audit", "knowledge"],
        sensitive=True,
    ),
    "PATIENT_DELETED": EventDefinition(
        event_type="PATIENT_DELETED",
        domain="patient",
        action="deleted",
        aggregate_type="patient",
        description="Paciente removido (LGPD)",
        consumers=["audit"],
        sensitive=True,
    ),
    "PATIENT_MERGED": EventDefinition(
        event_type="PATIENT_MERGED",
        domain="patient",
        action="merged",
        aggregate_type="patient",
        description="Dois registros de paciente unificados",
        consumers=["audit", "knowledge"],
        sensitive=True,
    ),
    
    # ─── CONSULTA ────────────────────────────────────────────────────
    "CONSULTATION_SCHEDULED": EventDefinition(
        event_type="CONSULTATION_SCHEDULED",
        domain="consultation",
        action="scheduled",
        aggregate_type="consultation",
        description="Consulta agendada",
        consumers=["audit", "connect", "smart_flow", "concierge"],
    ),
    "CONSULTATION_STARTED": EventDefinition(
        event_type="CONSULTATION_STARTED",
        domain="consultation",
        action="started",
        aggregate_type="consultation",
        description="Consulta iniciada",
        consumers=["audit", "voice", "smart_flow"],
    ),
    "CONSULTATION_FINISHED": EventDefinition(
        event_type="CONSULTATION_FINISHED",
        domain="consultation",
        action="finished",
        aggregate_type="consultation",
        description="Consulta finalizada",
        consumers=["audit", "connect", "concierge", "knowledge"],
    ),
    "CONSULTATION_CANCELLED": EventDefinition(
        event_type="CONSULTATION_CANCELLED",
        domain="consultation",
        action="cancelled",
        aggregate_type="consultation",
        description="Consulta cancelada",
        consumers=["audit", "connect", "smart_flow"],
    ),
    "CONSULTATION_NO_SHOW": EventDefinition(
        event_type="CONSULTATION_NO_SHOW",
        domain="consultation",
        action="no_show",
        aggregate_type="consultation",
        description="Paciente não compareceu",
        consumers=["audit", "connect"],
    ),
    
    # ─── PRONTUÁRIO ──────────────────────────────────────────────────
    "EVOLUTION_CREATED": EventDefinition(
        event_type="EVOLUTION_CREATED",
        domain="clinical_record",
        action="created",
        aggregate_type="evolution",
        description="Evolução clínica registrada",
        consumers=["audit", "knowledge"],
        sensitive=True,
    ),
    "PRESCRIPTION_CREATED": EventDefinition(
        event_type="PRESCRIPTION_CREATED",
        domain="clinical_record",
        action="created",
        aggregate_type="prescription",
        description="Prescrição médica emitida",
        consumers=["audit", "knowledge"],
        sensitive=True,
    ),
    "EXAM_REQUESTED": EventDefinition(
        event_type="EXAM_REQUESTED",
        domain="clinical_record",
        action="requested",
        aggregate_type="exam_request",
        description="Exame solicitado",
        consumers=["audit", "connect"],
    ),
    "DIAGNOSIS_ADDED": EventDefinition(
        event_type="DIAGNOSIS_ADDED",
        domain="clinical_record",
        action="added",
        aggregate_type="diagnosis",
        description="Diagnóstico adicionado",
        consumers=["audit", "knowledge"],
        sensitive=True,
    ),
    "ALLERGY_ADDED": EventDefinition(
        event_type="ALLERGY_ADDED",
        domain="clinical_record",
        action="added",
        aggregate_type="allergy",
        description="Alergia registrada",
        consumers=["audit", "knowledge"],
        sensitive=True,
    ),
    "MEDICATION_PRESCRIBED": EventDefinition(
        event_type="MEDICATION_PRESCRIBED",
        domain="clinical_record",
        action="prescribed",
        aggregate_type="medication",
        description="Medicamento prescrito",
        consumers=["audit", "knowledge"],
        sensitive=True,
    ),
    
    # ─── DOCUMENTOS ──────────────────────────────────────────────────
    "DOCUMENT_UPLOADED": EventDefinition(
        event_type="DOCUMENT_UPLOADED",
        domain="document",
        action="uploaded",
        aggregate_type="document",
        description="Documento enviado",
        consumers=["audit", "intake"],
    ),
    "DOCUMENT_PROCESSED": EventDefinition(
        event_type="DOCUMENT_PROCESSED",
        domain="document",
        action="processed",
        aggregate_type="document",
        description="Documento processado (OCR/IA)",
        consumers=["audit", "knowledge"],
    ),
    "OCR_COMPLETED": EventDefinition(
        event_type="OCR_COMPLETED",
        domain="document",
        action="completed",
        aggregate_type="document",
        description="OCR concluído",
        consumers=["audit", "knowledge"],
    ),
    
    # ─── COMUNICAÇÃO ─────────────────────────────────────────────────
    "WHATSAPP_RECEIVED": EventDefinition(
        event_type="WHATSAPP_RECEIVED",
        domain="communication",
        action="received",
        aggregate_type="message",
        description="Mensagem WhatsApp recebida",
        consumers=["audit", "connect", "concierge"],
    ),
    "WHATSAPP_SENT": EventDefinition(
        event_type="WHATSAPP_SENT",
        domain="communication",
        action="sent",
        aggregate_type="message",
        description="Mensagem WhatsApp enviada",
        consumers=["audit", "connect"],
    ),
    "EMAIL_SENT": EventDefinition(
        event_type="EMAIL_SENT",
        domain="communication",
        action="sent",
        aggregate_type="message",
        description="Email enviado",
        consumers=["audit", "connect"],
    ),
    "SMS_SENT": EventDefinition(
        event_type="SMS_SENT",
        domain="communication",
        action="sent",
        aggregate_type="message",
        description="SMS enviado",
        consumers=["audit", "connect"],
    ),
    "NOTIFICATION_DELIVERED": EventDefinition(
        event_type="NOTIFICATION_DELIVERED",
        domain="communication",
        action="delivered",
        aggregate_type="message",
        description="Notificação entregue",
        consumers=["audit"],
    ),
    "NOTIFICATION_FAILED": EventDefinition(
        event_type="NOTIFICATION_FAILED",
        domain="communication",
        action="failed",
        aggregate_type="message",
        description="Notificação falhou",
        consumers=["audit", "connect"],
    ),
    
    # ─── VOZ ─────────────────────────────────────────────────────────
    "VOICE_SESSION_STARTED": EventDefinition(
        event_type="VOICE_SESSION_STARTED",
        domain="voice",
        action="started",
        aggregate_type="voice_session",
        description="Sessão de voz iniciada",
        consumers=["audit", "smart_flow"],
    ),
    "VOICE_SESSION_ENDED": EventDefinition(
        event_type="VOICE_SESSION_ENDED",
        domain="voice",
        action="ended",
        aggregate_type="voice_session",
        description="Sessão de voz finalizada",
        consumers=["audit", "knowledge"],
    ),
    "WAKE_WORD_DETECTED": EventDefinition(
        event_type="WAKE_WORD_DETECTED",
        domain="voice",
        action="detected",
        aggregate_type="voice_session",
        description="Wake word detectada",
        consumers=["audit"],
    ),
    "VOICE_COMMAND_EXECUTED": EventDefinition(
        event_type="VOICE_COMMAND_EXECUTED",
        domain="voice",
        action="executed",
        aggregate_type="voice_session",
        description="Comando de voz executado",
        consumers=["audit"],
    ),
    
    # ─── SMART FLOW ──────────────────────────────────────────────────
    "CHECKIN_DETECTED": EventDefinition(
        event_type="CHECKIN_DETECTED",
        domain="smart_flow",
        action="detected",
        aggregate_type="checkin",
        description="Check-in detectado pela câmera",
        consumers=["audit"],
    ),
    "CHECKIN_COMPLETED": EventDefinition(
        event_type="CHECKIN_COMPLETED",
        domain="smart_flow",
        action="completed",
        aggregate_type="checkin",
        description="Check-in concluído com identificação",
        consumers=["audit", "connect", "siap"],
    ),
    "PATIENT_ENTERED_ROOM": EventDefinition(
        event_type="PATIENT_ENTERED_ROOM",
        domain="smart_flow",
        action="entered",
        aggregate_type="room_event",
        description="Paciente entrou em sala",
        consumers=["audit", "smart_flow"],
    ),
    "PATIENT_LEFT_ROOM": EventDefinition(
        event_type="PATIENT_LEFT_ROOM",
        domain="smart_flow",
        action="left",
        aggregate_type="room_event",
        description="Paciente saiu de sala",
        consumers=["audit", "smart_flow"],
    ),
    "WAIT_TIME_EXCEEDED": EventDefinition(
        event_type="WAIT_TIME_EXCEEDED",
        domain="smart_flow",
        action="exceeded",
        aggregate_type="alert",
        description="Tempo de espera excedeu limite",
        consumers=["audit", "connect"],
    ),
    "FLOW_COMPLETED": EventDefinition(
        event_type="FLOW_COMPLETED",
        domain="smart_flow",
        action="completed",
        aggregate_type="flow",
        description="Jornada do paciente concluída",
        consumers=["audit", "connect"],
    ),
    
    # ─── PAGAMENTO ───────────────────────────────────────────────────
    "INVOICE_CREATED": EventDefinition(
        event_type="INVOICE_CREATED",
        domain="payment",
        action="created",
        aggregate_type="invoice",
        description="Fatura criada",
        consumers=["audit", "connect"],
    ),
    "PAYMENT_RECEIVED": EventDefinition(
        event_type="PAYMENT_RECEIVED",
        domain="payment",
        action="received",
        aggregate_type="payment",
        description="Pagamento recebido",
        consumers=["audit", "connect"],
    ),
    "PAYMENT_FAILED": EventDefinition(
        event_type="PAYMENT_FAILED",
        domain="payment",
        action="failed",
        aggregate_type="payment",
        description="Pagamento falhou",
        consumers=["audit", "connect"],
    ),
    "SUBSCRIPTION_RENEWED": EventDefinition(
        event_type="SUBSCRIPTION_RENEWED",
        domain="payment",
        action="renewed",
        aggregate_type="subscription",
        description="Assinatura renovada",
        consumers=["audit", "connect"],
    ),
    
    # ─── SEGURANÇA ───────────────────────────────────────────────────
    "LOGIN_SUCCEEDED": EventDefinition(
        event_type="LOGIN_SUCCEEDED",
        domain="security",
        action="succeeded",
        aggregate_type="session",
        description="Login bem-sucedido",
        consumers=["audit", "identity"],
    ),
    "LOGIN_FAILED": EventDefinition(
        event_type="LOGIN_FAILED",
        domain="security",
        action="failed",
        aggregate_type="session",
        description="Login falhou",
        consumers=["audit", "identity"],
    ),
    "SESSION_REVOKED": EventDefinition(
        event_type="SESSION_REVOKED",
        domain="security",
        action="revoked",
        aggregate_type="session",
        description="Sessão revogada (logout)",
        consumers=["audit"],
    ),
    "PASSWORD_CHANGED": EventDefinition(
        event_type="PASSWORD_CHANGED",
        domain="security",
        action="changed",
        aggregate_type="credential",
        description="Senha alterada",
        consumers=["audit", "identity"],
    ),
    "MFA_ENABLED": EventDefinition(
        event_type="MFA_ENABLED",
        domain="security",
        action="enabled",
        aggregate_type="credential",
        description="MFA habilitado",
        consumers=["audit"],
    ),
    "DATA_EXPORT_REQUESTED": EventDefinition(
        event_type="DATA_EXPORT_REQUESTED",
        domain="security",
        action="requested",
        aggregate_type="lgpd_request",
        description="Exportação de dados solicitada (LGPD)",
        consumers=["audit", "lgpd"],
        sensitive=True,
    ),
    "DATA_PURGED": EventDefinition(
        event_type="DATA_PURGED",
        domain="security",
        action="purged",
        aggregate_type="lgpd_request",
        description="Dados excluídos (LGPD)",
        consumers=["audit", "lgpd"],
        sensitive=True,
    ),
    
    # ─── SISTEMA ─────────────────────────────────────────────────────
    "SYSTEM_STARTED": EventDefinition(
        event_type="SYSTEM_STARTED",
        domain="system",
        action="started",
        aggregate_type="system",
        description="Sistema iniciado",
        consumers=["audit", "monitoring"],
    ),
    "SYSTEM_STOPPED": EventDefinition(
        event_type="SYSTEM_STOPPED",
        domain="system",
        action="stopped",
        aggregate_type="system",
        description="Sistema parado",
        consumers=["audit", "monitoring"],
    ),
    "SYSTEM_HEALTH_DEGRADED": EventDefinition(
        event_type="SYSTEM_HEALTH_DEGRADED",
        domain="system",
        action="degraded",
        aggregate_type="system",
        description="Saúde do sistema degradada",
        consumers=["audit", "monitoring", "connect"],
    ),
    "SYSTEM_HEALTH_RECOVERED": EventDefinition(
        event_type="SYSTEM_HEALTH_RECOVERED",
        domain="system",
        action="recovered",
        aggregate_type="system",
        description="Saúde do sistema recuperada",
        consumers=["audit", "monitoring", "connect"],
    ),
    "SYSTEM_MAINTENANCE_ENABLED": EventDefinition(
        event_type="SYSTEM_MAINTENANCE_ENABLED",
        domain="system",
        action="enabled",
        aggregate_type="maintenance",
        description="Modo de manutenção habilitado",
        consumers=["audit", "monitoring", "gateway"],
    ),
    "SYSTEM_MAINTENANCE_DISABLED": EventDefinition(
        event_type="SYSTEM_MAINTENANCE_DISABLED",
        domain="system",
        action="disabled",
        aggregate_type="maintenance",
        description="Modo de manutenção desabilitado",
        consumers=["audit", "monitoring", "gateway"],
    ),
    "SYSTEM_DEPLOY_STARTED": EventDefinition(
        event_type="SYSTEM_DEPLOY_STARTED",
        domain="system",
        action="started",
        aggregate_type="deploy",
        description="Deploy iniciado",
        consumers=["audit", "monitoring"],
    ),
    "SYSTEM_DEPLOY_COMPLETED": EventDefinition(
        event_type="SYSTEM_DEPLOY_COMPLETED",
        domain="system",
        action="completed",
        aggregate_type="deploy",
        description="Deploy concluído",
        consumers=["audit", "monitoring"],
    ),
    
    # ─── FOLLOW-UP ───────────────────────────────────────────────────
    "FOLLOWUP_STARTED": EventDefinition(
        event_type="FOLLOWUP_STARTED",
        domain="followup",
        action="started",
        aggregate_type="followup_program",
        description="Programa de acompanhamento iniciado",
        consumers=["audit", "knowledge", "digital_twin", "connect"],
        sensitive=True,
    ),
    "FOLLOWUP_COMPLETED": EventDefinition(
        event_type="FOLLOWUP_COMPLETED",
        domain="followup",
        action="completed",
        aggregate_type="followup_program",
        description="Programa de acompanhamento concluído",
        consumers=["audit", "knowledge", "digital_twin"],
        sensitive=True,
    ),
    "FOLLOWUP_RESPONSE_RECEIVED": EventDefinition(
        event_type="FOLLOWUP_RESPONSE_RECEIVED",
        domain="followup",
        action="received",
        aggregate_type="followup_response",
        description="Resposta de questionário recebida",
        consumers=["audit", "knowledge", "digital_twin", "followup_engine"],
        sensitive=True,
    ),
    "FOLLOWUP_ALERT_TRIGGERED": EventDefinition(
        event_type="FOLLOWUP_ALERT_TRIGGERED",
        domain="followup",
        action="triggered",
        aggregate_type="followup_alert",
        description="Alerta de follow-up disparado",
        consumers=["audit", "connect", "digital_twin"],
        sensitive=True,
    ),
    "FOLLOWUP_ESCALATED": EventDefinition(
        event_type="FOLLOWUP_ESCALATED",
        domain="followup",
        action="escalated",
        aggregate_type="followup_alert",
        description="Alerta de follow-up escalonado",
        consumers=["audit", "connect", "concierge"],
        sensitive=True,
    ),
    "FOLLOWUP_PHASE_CHANGED": EventDefinition(
        event_type="FOLLOWUP_PHASE_CHANGED",
        domain="followup",
        action="changed",
        aggregate_type="followup_program",
        description="Fase do programa de acompanhamento alterada",
        consumers=["audit", "knowledge", "digital_twin"],
        sensitive=True,
    ),
    
    # ─── CANNABIS ────────────────────────────────────────────────────
    "CANNABIS_STARTED": EventDefinition(
        event_type="CANNABIS_STARTED",
        domain="cannabis",
        action="started",
        aggregate_type="medication",
        description="Tratamento com cannabis iniciado",
        consumers=["audit", "knowledge", "digital_twin", "followup"],
        sensitive=True,
    ),
    "CANNABIS_PRODUCT_ADDED": EventDefinition(
        event_type="CANNABIS_PRODUCT_ADDED",
        domain="cannabis",
        action="added",
        aggregate_type="medication",
        description="Produto de cannabis adicionado",
        consumers=["audit", "knowledge", "digital_twin"],
        sensitive=True,
    ),
    "CANNABIS_PRODUCT_CHANGED": EventDefinition(
        event_type="CANNABIS_PRODUCT_CHANGED",
        domain="cannabis",
        action="changed",
        aggregate_type="medication",
        description="Produto de cannabis alterado",
        consumers=["audit", "knowledge", "digital_twin"],
        sensitive=True,
    ),
    "CANNABIS_DOSE_CHANGED": EventDefinition(
        event_type="CANNABIS_DOSE_CHANGED",
        domain="cannabis",
        action="changed",
        aggregate_type="medication",
        description="Dose de cannabis alterada",
        consumers=["audit", "knowledge", "digital_twin", "followup"],
        sensitive=True,
    ),
    "CANNABIS_OUTCOME_RECORDED": EventDefinition(
        event_type="CANNABIS_OUTCOME_RECORDED",
        domain="cannabis",
        action="recorded",
        aggregate_type="outcome",
        description="Outcome de cannabis registrado",
        consumers=["audit", "knowledge", "digital_twin"],
        sensitive=True,
    ),
    "CANNABIS_ALERT_TRIGGERED": EventDefinition(
        event_type="CANNABIS_ALERT_TRIGGERED",
        domain="cannabis",
        action="triggered",
        aggregate_type="alert",
        description="Alerta do módulo Cannabis disparado",
        consumers=["audit", "connect", "digital_twin"],
        sensitive=True,
    ),
    "CANNABIS_DISCONTINUED": EventDefinition(
        event_type="CANNABIS_DISCONTINUED",
        domain="cannabis",
        action="discontinued",
        aggregate_type="medication",
        description="Tratamento com cannabis descontinuado",
        consumers=["audit", "knowledge", "digital_twin", "followup"],
        sensitive=True,
    ),

    # ═════════════════════════════════════════════════════════════════
    # NEURODEVELOPMENTAL — Módulo de Neurodesenvolvimento
    # ═════════════════════════════════════════════════════════════════
    # Plataforma multi-domínio (TEA, TDAH, AH/SD, Dupla Excepcionalidade,
    # TOD, Transtornos de Linguagem, Deficiência Intelectual,
    # Transtornos Específicos de Aprendizagem, Outras Neurodivergências).
    # Todos os eventos são sensitive=True (LGPD — dados de crianças).
    "NEURODEVELOPMENTAL_PROFILE_CREATED": EventDefinition(
        event_type="NEURODEVELOPMENTAL_PROFILE_CREATED",
        domain="neurodevelopmental",
        action="created",
        aggregate_type="neuro_patient_profile",
        description="Perfil neurodesenvolvimento criado para o paciente",
        consumers=["audit", "timeline", "digital_twin", "observatory_etl"],
        sensitive=True,
    ),
    "NEURODEVELOPMENTAL_PROFILE_UPDATED": EventDefinition(
        event_type="NEURODEVELOPMENTAL_PROFILE_UPDATED",
        domain="neurodevelopmental",
        action="updated",
        aggregate_type="neuro_patient_profile",
        description="Perfil neurodesenvolvimento atualizado",
        consumers=["audit", "timeline", "digital_twin"],
        sensitive=True,
    ),
    "NEURODEVELOPMENTAL_CONDITION_ADDED": EventDefinition(
        event_type="NEURODEVELOPMENTAL_CONDITION_ADDED",
        domain="neurodevelopmental",
        action="added",
        aggregate_type="neuro_condition",
        description="Nova condição neurodesenvolvimental adicionada ao paciente",
        consumers=["audit", "timeline", "digital_twin", "observatory_etl"],
        sensitive=True,
    ),
    "REDACTED": EventDefinition(
        event_type="REDACTED",
        domain="neurodevelopmental",
        action="removed",
        aggregate_type="neuro_condition",
        description="Condição neurodesenvolvimental removida",
        consumers=["audit", "timeline", "digital_twin"],
        sensitive=True,
    ),
    "NEURODEVELOPMENTAL_SCALE_APPLIED": EventDefinition(
        event_type="NEURODEVELOPMENTAL_SCALE_APPLIED",
        domain="neurodevelopmental",
        action="applied",
        aggregate_type="neuro_scale_response",
        description="Escala neuropsicológica aplicada (GAD-7, PHQ-9, M-CHAT, CARS, etc.)",
        consumers=["audit", "timeline", "knowledge", "observatory_etl", "dashboard_cache"],
        sensitive=True,
    ),
    "NEURODEVELOPMENTAL_SCORE_COMPUTED": EventDefinition(
        event_type="NEURODEVELOPMENTAL_SCORE_COMPUTED",
        domain="neurodevelopmental",
        action="computed",
        aggregate_type="neuro_scale_response",
        description="Score calculado e interpretação gerada",
        consumers=["audit", "dashboard_cache"],
        sensitive=True,
    ),
    "REDACTED": EventDefinition(
        event_type="REDACTED",
        domain="neurodevelopmental",
        action="started",
        aggregate_type="neuro_medication",
        description="Medicação neuropsiquiátrica iniciada",
        consumers=["audit", "timeline", "dashboard_cache"],
        sensitive=True,
    ),
    "REDACTED": EventDefinition(
        event_type="REDACTED",
        domain="neurodevelopmental",
        action="changed",
        aggregate_type="neuro_medication",
        description="Medicação neuropsiquiátrica alterada (dose, frequência, via)",
        consumers=["audit", "timeline", "dashboard_cache"],
        sensitive=True,
    ),
    "REDACTED": EventDefinition(
        event_type="REDACTED",
        domain="neurodevelopmental",
        action="stopped",
        aggregate_type="neuro_medication",
        description="Medicação neuropsiquiátrica suspensa",
        consumers=["audit", "timeline", "dashboard_cache"],
        sensitive=True,
    ),
    "REDACTED": EventDefinition(
        event_type="REDACTED",
        domain="neurodevelopmental",
        action="started",
        aggregate_type="neuro_cannabis_regimen",
        description="Regime de cannabis medicinal neuropsiquiátrico iniciado",
        consumers=["audit", "timeline", "observatory_etl"],
        sensitive=True,
    ),
    "REDACTED": EventDefinition(
        event_type="REDACTED",
        domain="neurodevelopmental",
        action="changed",
        aggregate_type="neuro_cannabis_regimen",
        description="Dose de canabinoide ajustada",
        consumers=["audit", "timeline", "observatory_etl"],
        sensitive=True,
    ),
    "NEURODEVELOPMENTAL_EVENT_RECORDED": EventDefinition(
        event_type="NEURODEVELOPMENTAL_EVENT_RECORDED",
        domain="neurodevelopmental",
        action="recorded",
        aggregate_type="neuro_event",
        description="Evento clínico neurodesenvolvimental registrado (crise, mudança escolar, etc.)",
        consumers=["audit", "timeline"],
        sensitive=True,
    ),
    "REDACTED": EventDefinition(
        event_type="REDACTED",
        domain="neurodevelopmental",
        action="generated",
        aggregate_type="neuro_report",
        description="Relatório neurodesenvolvimental gerado (médico/escolar/judicial/INSS/etc.)",
        consumers=["audit"],
        sensitive=True,
    ),
    "REDACTED": EventDefinition(
        event_type="REDACTED",
        domain="neurodevelopmental",
        action="generated",
        aggregate_type="neuro_ai_summary",
        description="Resumo / relatório gerado por IA clínica (revisão humana obrigatória)",
        consumers=["audit", "knowledge"],
        sensitive=True,
    ),
    "REDACTED": EventDefinition(
        event_type="REDACTED",
        domain="neurodevelopmental",
        action="requested",
        aggregate_type="neuro_research_export",
        description="Exportação de dados para pesquisa solicitada (CSV/Excel/JSON/FHIR/etc.)",
        consumers=["audit"],
        sensitive=True,
    ),
}


# ═══════════════════════════════════════════════════════════════════════
# API PÚBLICA DO CATÁLOGO
# ═══════════════════════════════════════════════════════════════════════

def get_event_definition(event_type: str) -> Optional[EventDefinition]:
    """Retorna definição de um evento pelo tipo."""
    return _EVENT_CATALOG.get(event_type)


def is_valid_event_type(event_type: str) -> bool:
    """Verifica se um tipo de evento está registrado no catálogo."""
    return event_type in _EVENT_CATALOG


def list_events(domain: Optional[str] = None) -> List[str]:
    """
    Lista todos os tipos de evento registrados.
    
    Args:
        domain: Filtra por domínio (patient, consultation, etc.)
    
    Returns:
        Lista de event_type strings
    """
    if domain:
        return [
            et for et, defn in _EVENT_CATALOG.items()
            if defn.domain == domain
        ]
    return list(_EVENT_CATALOG.keys())


def list_domains() -> List[str]:
    """Lista todos os domínios registrados."""
    domains = set(defn.domain for defn in _EVENT_CATALOG.values())
    return sorted(domains)


def get_event_schema(event_type: str) -> Dict[str, Any]:
    """
    Retorna schema JSON-like de um evento.
    Útil para documentação e validação.
    """
    defn = _EVENT_CATALOG.get(event_type)
    if not defn:
        raise ValueError(f"Event type '{event_type}' not found in catalog")
    
    return {
        "event_type": defn.event_type,
        "domain": defn.domain,
        "action": defn.action,
        "aggregate_type": defn.aggregate_type,
        "description": defn.description,
        "version": defn.version,
        "consumers": defn.consumers,
        "sensitive": defn.sensitive,
    }


def get_expected_consumers(event_type: str) -> List[str]:
    """Retorna lista de consumer groups esperados para um evento."""
    defn = _EVENT_CATALOG.get(event_type)
    return defn.consumers if defn else []


def validate_event_type(event_type: str) -> None:
    """
    Valida que um event_type segue as convenções.
    
    Raises:
        ValueError: se inválido
    """
    if "_" not in event_type:
        raise ValueError(
            f"event_type must follow DOMAIN_ACTION pattern. Got: {event_type}"
        )
    
    parts = event_type.split("_")
    if len(parts) < 2:
        raise ValueError(
            f"event_type must have at least DOMAIN and ACTION. Got: {event_type}"
        )
    
    if not event_type.isupper():
        raise ValueError(
            f"event_type must be UPPER_CASE. Got: {event_type}"
        )


class EventCatalog:
    """
    Interface de consulta ao catálogo de eventos.
    
    Uso:
        from araos.platform.events.catalog import EventCatalog
        
        catalog = EventCatalog()
        print(catalog.list_by_domain("patient"))
        print(catalog.get_consumers("PATIENT_CREATED"))
    """
    
    def list_all(self) -> List[str]:
        return list_events()
    
    def list_by_domain(self, domain: str) -> List[str]:
        return list_events(domain=domain)
    
    def get_definition(self, event_type: str) -> Optional[EventDefinition]:
        return get_event_definition(event_type)
    
    def get_consumers(self, event_type: str) -> List[str]:
        return get_expected_consumers(event_type)
    
    def is_valid(self, event_type: str) -> bool:
        return is_valid_event_type(event_type)
    
    def validate(self, event_type: str) -> None:
        validate_event_type(event_type)
