from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Countermeasure:
    countermeasure_id: str
    project_id: str
    description: str = ""
    component_model: str = ""
    component_manufacturer: str = ""
    sort_order: int = 0
