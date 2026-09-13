from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Applicant:
    applicant_id: str
    project_id: str
    company_name_jp: str = ""
    company_name_en: str = ""
    address_jp: str = ""
    address_en: str = ""
    notes: str = ""
