from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Project:
    project_id: str
    project_no: str = ""
    test_plan_no: str = ""
    measurement_period: str = ""
    include_immunity: bool = False
    include_medical: bool = False
    include_taiwan: bool = False
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""
