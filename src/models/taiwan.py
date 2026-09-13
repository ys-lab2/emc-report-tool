from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TaiwanApplicant:
    taiwan_applicant_id: str
    project_id: str
    company_name_en: str = ""
    address_en: str = ""
    company_name_zh: str = ""
    address_zh: str = ""
    notes: str = ""
    eut_operation_status_text: str = ""


@dataclass
class InternalComponent:
    internal_component_id: str
    taiwan_applicant_id: str
    device_name: str = ""
    quantity_max: str = ""
    model_name: str = ""
    manufacturer: str = ""
    sort_order: int = 0
