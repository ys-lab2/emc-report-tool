from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ImmunityCriteria:
    immunity_criteria_id: str
    project_id: str
    criterion_a: str = ""
    criterion_b: str = ""
    criterion_c: str = ""


@dataclass
class ImmunityVerificationPoint:
    point_id: str
    immunity_criteria_id: str
    content: str = ""
    sort_order: int = 0
