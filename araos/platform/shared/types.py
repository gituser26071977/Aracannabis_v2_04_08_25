"""
AraOS Platform — Shared Types.

Type aliases usados em toda a plataforma.
"""

from typing import Dict, List, Any, Union, Optional

# Identificadores
TenantID = str
OrganizationID = str
ClinicID = str
UserID = str
EventID = str
SessionID = str
ConsultationID = str
PatientID = str
DocumentID = str

# Tipos JSON
JSONValue = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
JSONDict = Dict[str, JSONValue]
JSONList = List[JSONValue]

# Eventos
EventPayload = JSONDict
EventMetadata = JSONDict

# Respostas de serviços
ServiceResult = Dict[str, Any]
ErrorResult = Dict[str, Any]

# Configurações
SettingsDict = Dict[str, Any]
FeatureFlagsDict = Dict[str, bool]
