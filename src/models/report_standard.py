from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ReportStandard:
    report_standard_id: str
    project_id: str
    standard_name: str = ""
    language: str = "jp"  # "jp" or "en"
    desired_due_date: str = ""
    submission_media: str = "PDF"
    sort_order: int = 0
