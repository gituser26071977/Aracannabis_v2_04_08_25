"""
AraOS Clinical — Timeline.

História clínica longitudinal baseada em eventos clínicos.
Não utiliza consultas como timeline — utiliza eventos.
"""

from .models import ClinicalTimeline, TimelineEntry

__all__ = ["ClinicalTimeline", "TimelineEntry"]
