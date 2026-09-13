from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MedicalCriteria:
    medical_criteria_id: str
    project_id: str
    immunity_performance_text: str = ""


@dataclass
class MedicalCriteriaItem:
    item_id: str
    medical_criteria_id: str
    category: str  # "basic_safety" or "basic_performance"
    content: str = ""
    sort_order: int = 0
