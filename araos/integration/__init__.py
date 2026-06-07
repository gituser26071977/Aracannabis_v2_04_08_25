"""
AraOS Integration Layer.

Adapters para desacoplar o Agent Runtime dos módulos:
    - Voice (Voice Copilot)
    - Concierge
    - Smart Flow
    - Core (SIAP)
"""

from .voice_adapter import VoiceAdapter
from .concierge_adapter import ConciergeAdapter
from .smart_flow_adapter import SmartFlowAdapter
from .core_adapter import CoreAdapter

__all__ = [
    "VoiceAdapter",
    "ConciergeAdapter",
    "SmartFlowAdapter",
    "CoreAdapter",
]
